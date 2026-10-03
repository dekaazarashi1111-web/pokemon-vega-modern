#!/usr/bin/env python3
"""保存ARM/30試験を再利用し、新しい標準リスト1連続入力だけ実測・記録する。"""
import datetime
import io
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import time
import zipfile
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_standard_list as s
import pr16_research_standard_list_probe as probe
import pr16_research_standard_list_oracle as oracle
import pr16_research_connection_actions as parent
import pr16_research_lifecycle_actions as d
TASK='USER-20260927-RESEARCH-STANDARD-LIST'
START='1bf1e02fe3b7bf7ee526ca47f4e79c9d971ed246'
WF='.github/workflows/pr16-research-standard-list.yml'
CP='content/modernization/pr16_research_standard_list_checkpoint.json'
GUIDE='docs/PR16_RESEARCH_STANDARD_LIST_JA.md'
RECIPE='content/modernization/pr16_research_standard_list_recipe.json'
BASE='content/modernization/pr16_research_standard_list_evidence'
CODE={WF,s.SOURCE,'scripts/pr16_research_standard_list.py','scripts/pr16_research_standard_list_probe.py',
      'scripts/pr16_research_standard_list_oracle.py','scripts/pr16_research_standard_list_actions.py',
      'tests/test_pr16_research_standard_list.py','tests/test_pr16_research_standard_list_oracle.py'}
PROTECTED=parent.PROTECTED|{'content/modernization/pr16_research_connection_checkpoint.json',
    'content/modernization/pr16_research_connection_acceptance.json','content/modernization/pr16_research_counter_checkpoint.json',
    'content/modernization/pr16_research_counter_numeric_recipe.json','docs/PR16_RESEARCH_COUNTER_JA.md',
    'overlays/research_economy_v1/research_economy_v1.h'}
OUT=ROOT/'.local/pr16-standard-list';PUBLIC=OUT/'public'
COUNTS={'native_processes':0,'guard_processes':0,'host_compiles':0,'arm_compiles':0,'accepted_case_reruns':0}
BUILD_RUN=36310534280
BUILD_HEAD='8b4dfa8626903803d246f1979fa27ef9e12578ee'
BUILD_ART=10928552956
BUILD_BIND={'size':1259229,'sha256':'84f278c2e18bdb17989e347688962589af5a693cfd125a00aa3ea96cf0de55f0'}


def build_reuse():
    run=d.inputs.api('actions/runs/'+str(BUILD_RUN))
    s.need(run['head_sha']==BUILD_HEAD and run['status']=='completed' and run['conclusion']=='success','saved isolated ARM build terminal')
    meta=d.inputs.api('actions/artifacts/'+str(BUILD_ART))
    s.need(not meta['expired'] and meta['workflow_run']['head_sha']==BUILD_HEAD and meta['workflow_run']['id']==BUILD_RUN
           and meta['size_in_bytes']==BUILD_BIND['size'] and meta['digest']=='sha256:'+BUILD_BIND['sha256'],'saved build archive metadata')
    raw=d.inputs.api('actions/artifacts/'+str(BUILD_ART)+'/zip',True);s.need(s.identity(raw)==BUILD_BIND,'saved build archive bytes')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        s.need(len(z.infolist())==len(set(z.namelist()))==201 and sum(i.file_size for i in z.infolist())==5334036,'fixed build archive bounds')
        for entry in z.infolist():
            p=PurePosixPath(entry.filename)
            s.need(not p.is_absolute() and '..' not in p.parts and not entry.is_dir() and entry.external_attr>>28!=10,'regular bounded artifact members')
        build=oracle.load(z.read('build.json'));manifest=oracle.load(z.read('source-manifest.json'))
        s.need(build['source_head']==manifest['head']==BUILD_HEAD and build['run_id']==BUILD_RUN,'saved source provenance')
        for name,binding in manifest['files'].items():
            s.need(s.identity(z.read('source/'+name))==binding==s.identity((ROOT/name).read_bytes()),'unchanged native helper '+name)
        for name,binding in build['source_bindings'].items():s.need(s.identity((ROOT/name).read_bytes())==binding,'accepted new source '+name)
        unit=z.read('unit.stderr.txt');s.need(unit.count(b' ... ok\n')==30 and b'\nOK\n' in unit and not z.read('unit.stdout.txt'),'30 saved host/event tests')
        for name in ('build.json','unit.stdout.txt','unit.stderr.txt','arm/compile.stdout.txt','arm/compile.stderr.txt','arm/link.ld','arm/pr16_research_standard_list_rows.h'):
            dest=PUBLIC/'build'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(z.read(name))
    code=bytes.fromhex(build['code_hex']);s.need(s.identity(code)==build['code'],'compiled new code bytes')
    d.write(PUBLIC/'build-reuse.json',{'run':d.run_summary(run),'artifact_id':BUILD_ART,'archive':BUILD_BIND,
        'reused_arm_compiles':1,'reused_host_event_tests':30,'new_arm_compiles':0,'new_host_event_test_executions':0})
    return code,build


def measure():
    os.chdir(ROOT);d.current();s.need(not (ROOT/CP).exists(),'recorded native input must not be replayed')
    PUBLIC.mkdir(parents=True)
    invocation={'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),
                'source_bindings':d.bindings(CODE),'protected_bindings':d.bindings(PROTECTED)}
    d.write(PUBLIC/'invocation.json',invocation)
    old=d.inputs.api('actions/runs/36287524393')
    s.need(old['head_sha']=='ca8b2648e74e2d603caf2f6bb7311cc8491ff455' and old['status']=='completed' and old['conclusion']=='success','prior numeric acceptance terminal')
    d.write(PUBLIC/'previous-numeric-acceptance.json',d.run_summary(old))
    code,build=build_reuse()
    parent.OUT=OUT/'parent';parent.PUBLIC=PUBLIC
    runtime,seed,predecessor,_,_=parent.restore()
    numeric,_=s.numeric.apply(predecessor)
    candidate,recipe=s.apply(numeric,code,build)
    s.need(recipe['candidate']==oracle.CANDIDATE,'independently bound standard-list candidate')
    d.write(PUBLIC/'recipe.json',recipe)
    rom=OUT/'candidate.gba';rom.write_bytes(candidate)
    fixture,receipt=probe.fixture(seed);immutable=OUT/'immutable-fixture.srm';immutable.write_bytes(fixture)
    save=OUT/'working.srm';save.write_bytes(fixture)
    d.write(PUBLIC/'fixture.json',receipt)
    import pr16_research_lifecycle_v2 as gen
    gen.OUT=OUT/'generated';d.PUBLIC=PUBLIC
    generated=probe.generate(seed,recipe);source=OUT/'probe.c';source.write_bytes(generated)
    (PUBLIC/'generated.c.txt').write_bytes(generated)
    exe=OUT/'probe'
    command=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Itools','-I.',
             '-I'+str(runtime/'include'),str(source),'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)]
    COUNTS['host_compiles']+=1
    compiled=subprocess.run(command,capture_output=True,timeout=150)
    (PUBLIC/'compile.stdout.txt').write_bytes(compiled.stdout);(PUBLIC/'compile.stderr.txt').write_bytes(compiled.stderr)
    d.write(PUBLIC/'compile.json',{'returncode':compiled.returncode,'command':command,'source':s.identity(generated),
        'compiler':subprocess.check_output(['cc','--version']).decode(),'stdout':s.identity(compiled.stdout),'stderr':s.identity(compiled.stderr)})
    s.need(compiled.returncode==0 and not compiled.stderr,'strict changed native observer compile')
    prefix=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(exe)]
    guards={}
    for method in ('bus8','bus16','bus32','raw8','raw16','raw32','register'):
        COUNTS['guard_processes']+=1
        p=subprocess.run(prefix+['--guard-check',method],capture_output=True,timeout=15)
        (PUBLIC/(method+'.stdout.txt')).write_bytes(p.stdout);(PUBLIC/(method+'.stderr.txt')).write_bytes(p.stderr)
        guards[method]={'returncode':p.returncode,'stdout':s.identity(p.stdout),'stderr':s.identity(p.stderr)}
        d.write(PUBLIC/'guards.json',guards)
        s.need(p.returncode==1 and not p.stdout and p.stderr==b'research-save-impact: host write after observation barrier\n','write barrier '+method)
    commands=probe.commands();(PUBLIC/'commands.txt').write_bytes(commands)
    COUNTS['native_processes']+=1;started=time.monotonic()
    try:
        p=subprocess.run(prefix+[str(rom),str(save),'0'],input=commands,capture_output=True,cwd=PUBLIC,timeout=180)
        rc=p.returncode;out,err=p.stdout,p.stderr;timed_out=False
    except subprocess.TimeoutExpired as exc:
        rc=None;out,err=exc.stdout or b'',exc.stderr or b'';timed_out=True
    (PUBLIC/'stdout.txt').write_bytes(out);(PUBLIC/'stderr.txt').write_bytes(err)
    screens={p.name:s.identity(p.read_bytes()) for p in sorted(PUBLIC.glob('*.ppm'))}
    for p in PUBLIC.glob('*.ppm'):
        b=p.read_bytes();s.need(len(b)==115215 and b.startswith(b'P6\n240 160\n255\n'),'complete PPM')
    saved=save.read_bytes()
    measurement={'returncode':rc,'timeout':timed_out,'elapsed_seconds':round(time.monotonic()-started,3),
                 'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),
                 'stdout':s.identity(out),'stderr':s.identity(err),'screens':screens,'commands':s.identity(commands),
                 'counts':COUNTS,'candidate':recipe['candidate'],'save_after':s.identity(saved),
                 'flash_prefix_unchanged':saved[:len(fixture)]==fixture and len(saved) in (len(fixture),len(fixture)+16)}
    d.write(PUBLIC/'measurement.json',measurement)
    s.need(rc==0 and not err and not timed_out and measurement['flash_prefix_unchanged'],'clean native process and unchanged actual Flash')
    result=oracle.validate(out,commands,fixture,screens);d.write(PUBLIC/'oracle.json',result)
    os.environ['PR16_STANDARD_LIST_EVIDENCE']=str(PUBLIC)
    os.environ['PR16_STANDARD_LIST_FIXTURE']=str(immutable)
    unit=subprocess.run([sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_research_standard_list_oracle.py','-v'],capture_output=True,timeout=90)
    (PUBLIC/'oracle-unit.stdout.txt').write_bytes(unit.stdout);(PUBLIC/'oracle-unit.stderr.txt').write_bytes(unit.stderr)
    passed=unit.stderr.count(b' ... ok\n')
    d.write(PUBLIC/'oracle-unit.json',{'returncode':unit.returncode,'passed':passed,'expected':27,'stdout':s.identity(unit.stdout),'stderr':s.identity(unit.stderr)})
    s.need(unit.returncode==0 and not unit.stdout and passed==27,'27 new positive-controlled oracle tests')
    s.need(d.bindings(CODE)==invocation['source_bindings'] and d.bindings(PROTECTED)==invocation['protected_bindings'],'all task/protected sources unchanged')
    s.need(s.identity(rom.read_bytes())==recipe['candidate'] and immutable.read_bytes()==fixture,'working observation does not mutate candidate/fixture')


def record():
    os.chdir(ROOT);d.current();s.need(not (ROOT/CP).exists(),'immutable initial standard-list checkpoint')
    invocation=d.read(PUBLIC/'invocation.json')
    s.need(invocation['source_head']==os.environ['GITHUB_SHA'] and d.bindings(CODE)==invocation['source_bindings']
           and d.bindings(PROTECTED)==invocation['protected_bindings'],'same source/protected record boundary')
    error=d.read(PUBLIC/'error.json') if (PUBLIC/'error.json').exists() else None
    measurement=d.read(PUBLIC/'measurement.json') if (PUBLIC/'measurement.json').exists() else {}
    recipe=d.read(PUBLIC/'recipe.json') if (PUBLIC/'recipe.json').exists() else None
    state=d.read(ROOT/d.STATE)
    previous=[]
    for pending in state.get('pending_runs',[]):previous.append(d.run_summary(d.inputs.api('actions/runs/'+str(pending['run_id']))))
    failed=d.inputs.api('actions/runs/36310336114')
    s.need(failed['status']=='completed' and failed['conclusion']=='failure' and failed['head_sha']=='78af3822e1d9782a8af5805e342b3f8d1f6f617e','retain implicit-memcpy failed build')
    d.write(PUBLIC/'reconciled-prior-actions.json',{'previous_pending_runs':previous,'failed_first_build':d.run_summary(failed)})
    directory=Path(BASE)/os.environ['GITHUB_RUN_ID'];s.need(not directory.exists(),'immutable raw evidence directory')
    evidence={}
    for p in sorted(PUBLIC.rglob('*')):
        if not p.is_file() or p.suffix not in ('.json','.txt','.ld','.h'):continue
        raw=p.read_bytes();raw.decode('utf-8');s.need(b'\0' not in raw,'tracked text only')
        target=directory/p.relative_to(PUBLIC)
        if target.suffix in ('.ld','.h'):target=target.with_suffix(target.suffix+'.txt')
        target.parent.mkdir(parents=True,exist_ok=True)
        normalized=raw.replace((str(ROOT)+'/').encode(),b'<checkout>/')
        if normalized!=raw:
            target=target.with_name(target.stem+'.normalized'+target.suffix)
            notice=target.with_suffix(target.suffix+'.normalization.json')
            d.write(notice,{'raw':s.identity(raw),'normalized':s.identity(normalized),'method':'CHECKOUT_ROOT_ONLY','raw_in_actions_artifact':True})
            evidence[str(notice)]=s.identity(notice.read_bytes())
        target.write_bytes(normalized);evidence[str(target)]=s.identity(normalized)
    d.write(directory/'manifest.json',evidence)
    status='STOPPED_STANDARD_LIST_MEASUREMENT' if error else 'MEASURED_STANDARD_LIST_PENDING_VISUAL_AND_TERMINAL_REVIEW'
    cp={'schema_version':1,'task':TASK,'status':status,'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),
        'source_bindings':invocation['source_bindings'],'protected_bindings':invocation['protected_bindings'],
        'parent':s.PARENT,'candidate':recipe['candidate'] if recipe else None,'recipe':RECIPE if recipe else None,
        'measurement':measurement,'error':error,'evidence_directory':str(directory),'evidence_manifest':str(directory/'manifest.json'),
        'standard_list_accepted':False,'visual_review_completed':False,'actions_completion_confirmed':False,
        'naturally_earned_spending_accepted':False,'natural_story_progress_accepted':False,
        'active_baseline_changed':False,'release_ready':False,'issue19_complete':False,
        'reused_build':{'run_id':BUILD_RUN,'source_head':BUILD_HEAD,'artifact_id':BUILD_ART,'archive':BUILD_BIND,'arm_compiles':1,'tests':30},
        'failed_build_preserved':d.run_summary(failed),'previous_pending_runs_reconciled':previous}
    d.write(CP,cp)
    extra=set()
    if recipe:d.write(RECIPE,recipe);extra.add(RECIPE)
    goal=('標準リストの生原本を保存。22実画面と実行run終端を照合し、選択/取消/再訪の限定受入を確定する。'
          if not error else '標準リスト失敗原本を先に読む。成功した入力/生成物を再実行せず、変更された障害層だけ修正する。')
    goal+=' 次の独立境界は自然稼得RP→ショップ支出、通常ストーリー進行。数値2境界/旧4入口/旧稼得/BP/P08は再実行しない。'
    guide='# PR16 受付STANDARD_LIST\n\nTask: `'+TASK+'`\n\n'+goal+'\n\n## 実装\n\n固定c3971e83の後処理層。既存の受付数値script/text、研究owner、volatile、canonicalは不変。未参照FF領域0x09F4A800/2048byteとlocal4 script pointerだけを所有。744byte独立Thumbコード、212byteイベント、実差分950byte、全ROM rollback一致。stock task/window/menu APIで「ポイントとランク」「ポイントのあつめかた」「おわる」、B取消、両機能からlistへ戻る。task/window解放・入力debounce・資源不足時の非待機終了。新EWRAM0。正本recipeは `'+RECIPE+'`。新親では再監査を要求する。\n\n## 検証境界\n\nrun36310534280のARM生成1回とhost/event30検査を保存再利用。初回run36310336114の暗黙memcpyリンク失敗を保持。今回の新しい連続入力1processは起動前0RP fixture、屋外prefix後は物理keyだけ。3回訪問、2機能選択、B取消2回、終了行1回。所有task/window、全owner/ledger/Bag/party/Flash/counter、展開文言と22画面を照合。7方式書込み拒否、厳格host compile、新oracle27検査。件数の実績/失敗有無はcheckpoint原本が優先。通常ストーリー到達や自然稼得支出は未受入。\n\n## 現在地\n\n`'+status+'` / source `'+cp['source_head']+'` / run `'+str(cp['run_id'])+'`。画面視認と自己run終端を自動成功へ昇格しない。\n'
    (ROOT/GUIDE).write_text(guide,encoding='utf-8')
    state['research_standard_list']={k:cp[k] for k in ('status','source_head','run_id','candidate','standard_list_accepted')}
    state['research_standard_list'].update(path=CP,recipe=cp['recipe'])
    state['bp']['current_stop']=status;state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_STANDARD_LIST_REVIEW_THEN_NATURAL_SPENDING',goal_ja=goal,
        read_paths=[GUIDE,CP]+([RECIPE] if recipe else [])+['scripts/pr16_research_standard_list_oracle.py'],
        stop_rule_ja='保存済み生成/30検査/実測原本を再利用。変更影響なしの数値2境界/旧4入口/旧稼得/BP/P08を反復しない。merge/release/baseline変更禁止。')
    state['do_not_repeat'].insert(0,'STANDARD_LIST原本 '+CP+' を先に照合。同じARM生成/host30検査/成功した物理入力を再実行しない。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='標準リスト実測source HEAD。自己記録commitではなく、終端は次の読取で確定する。'
    runs=d.inputs.api('actions/runs?head_sha='+os.environ['GITHUB_SHA']+'&per_page=50')
    s.need(runs['total_count']==len(runs['workflow_runs'])<=50,'all current HEAD Actions')
    state['observed_head_checks']={'scope_head':os.environ['GITHUB_SHA'],'runs':[d.run_summary(r) for r in runs['workflow_runs']],
                                   'reason_ja':'過去pendingの終端を別記照合。自己run/一般CIを一括成功へ昇格しない。'}
    state['pending_runs']=[{'run_id':r['id'],'tested_head':r['head_sha'],'status':r['status']} for r in runs['workflow_runs'] if r['status'] in ('queued','in_progress')]
    for p in CODE|{CP,GUIDE}|extra:state['source_bindings'][p]=s.identity((ROOT/p).read_bytes())
    from pr16_learnset_compact_record import publish_resume
    publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK}\n- Version: research-standard-list-v1-measured\n- Status: STOPPED（原本/画面/終端を区別して記録）\n- Summary: 標準リスト2機能/終了行/B取消/再訪を実装。後処理領域とlocal4 pointerのみ、旧数値層・保存owner不変。\n- Files changed: 新list C/builder/probe/oracle/30+27検査/Actions、専用MD/JSON/recipe/UTF8原本、固定引継ぎ、両ログ。\n- Verify: ARM/30検査はrun36310534280を再利用。初回暗黙memcpy失敗run36310336114を保持。今回の実行数とerrorは{CP}のmeasurement/errorを正本とする。計画はnative1/guard7/host1/ARM0、新oracle27。旧受入matrix再実行0。画面・自己run終端・全CI成功を未確認のまま主張しない。\n- Commit: source={os.environ["GITHUB_SHA"]}; 同branch非force記録、自己SHAはgit log。\n- Network: 固定GitHub artifactsとActions/PR metadataのみ。ROM/save/実画像はGit管理外。merge/release/baseline変更なし。\n'
    for p in d.LOGS:
        with (ROOT/p).open('a',encoding='utf-8') as f:f.write(log)
    owned=set(evidence)|{str(directory/'manifest.json'),CP,GUIDE,d.STATE,d.DOC}|d.LOGS|extra
    d.write(OUT/'owned.json',sorted(owned))


def guard():
    os.chdir(ROOT);d.current()
    import pr16_resume
    import pr16_learnset_runtime_record as g
    pr16_resume.validate(ROOT)
    g.START=START;g.CODE=CODE;g.OWNED=set(d.read(OUT/'owned.json'));g.guard()
    s.need(d.bindings(PROTECTED)==d.read(CP)['protected_bindings'],'protected originals/baselines preserved')
    subprocess.run(['git','diff','--cached','--check'],check=True)


if __name__=='__main__':
    if sys.argv[1:]==['measure']:
        try:measure()
        except Exception as exc:
            if PUBLIC.exists():d.write(PUBLIC/'error.json',{'type':type(exc).__name__,'reason':str(exc),'counts':COUNTS})
            raise
    elif sys.argv[1:]==['record']:record()
    elif sys.argv[1:]==['guard']:guard()
    elif sys.argv[1:]==['paths']:print('\n'.join(d.read(OUT/'owned.json')))
    else:raise SystemExit('measure|record|guard|paths')
