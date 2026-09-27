#!/usr/bin/env python3
"""未受入の物理入口だけを測定し、独立oracle前の証拠を同branchへ固定する。"""
import datetime
import os
from pathlib import Path
import subprocess
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'scripts'),str(ROOT)]
import pr16_research_connection as m
import pr16_research_lifecycle_actions as d
START='1915a9e949b5344c4e774ac253179bd8af7b5410'
SELF='scripts/pr16_research_connection_actions.py'
WF='.github/workflows/pr16-research-connection-20260927.yml'
CP='content/modernization/pr16_research_connection_checkpoint.json'
GUIDE='docs/PR16_RESEARCH_CONNECTION_JA.md'
BASE='content/modernization/pr16_research_connection_evidence'
CODE={SELF,WF,'scripts/pr16_research_connection.py',m.C}
OUT=ROOT/'.local/pr16-research-connection'
PUBLIC=OUT/'public'
PROTECTED=d.PROTECTED|{'content/modernization/pr16_research_game_corner_checkpoint.json','docs/PR16_RESEARCH_GAME_CORNER_JA.md','content/research_economy_v1/canonical_model.json','overlays/research_economy_v1/research_economy_v1.c'}

def restore():
    import pr16_research_retry as retry
    import pr16_research_v1_corrupt_load as corrupt
    import pr16_research_map_view as view
    d.OUT=OUT/'restore';d.PUBLIC=d.OUT/'public';d.PUBLIC.mkdir(parents=True)
    runtime,data,seed,parent,artifacts=d.restore()
    rec=d.read('content/modernization/pr16_research_retry_recipe.json')
    candidate,_=retry.apply(parent,bytes.fromhex(rec['after']))
    rec=d.read('content/modernization/pr16_research_v1_corrupt_load_recipe.json')
    candidate,_=corrupt.apply(candidate,bytes.fromhex(rec['after'])[:corrupt.CODE['size']])
    candidate,_=view.apply(candidate)
    m.need(m.identity(candidate)==m.CANDIDATE,'fixed current candidate')
    rom=OUT/'candidate.gba';rom.write_bytes(candidate)
    fixture=m.prior.photo.fixture(seed)
    m.need(m.identity(fixture)=={'size':131072,'sha256':'434076d0db74c4c5bf1b63e3aa4cc336d17e1f2dbb894160e840c721aa337a38'},'fixed zero RP fixture')
    d.write(PUBLIC/'inputs.json',dict(candidate=m.identity(candidate),seed=m.identity(seed),fixture=m.identity(fixture),artifacts=artifacts))
    return runtime,seed,candidate,rom,fixture

def measure():
    os.chdir(ROOT);d.current();m.need(not Path(CP).exists(),'recorded matrix must not be rerun')
    PUBLIC.mkdir(parents=True)
    protected=d.bindings(PROTECTED);source=d.bindings(CODE)
    d.write(PUBLIC/'invocation.json',dict(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),source_bindings=source,protected_bindings=protected,accepted_case_reruns=0))
    runtime,seed,candidate,rom,fixture=restore()
    audit=m.audit(candidate);d.write(PUBLIC/'candidate-audit.json',audit)
    text=m.generate(seed);(PUBLIC/'generated.c.txt').write_bytes(text)
    generated=OUT/'generated.c';generated.write_bytes(text);exe=OUT/'probe'
    command=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Itools','-I.','-I'+str(runtime/'include'),str(generated),'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)]
    compiled=subprocess.run(command,capture_output=True,timeout=150)
    (PUBLIC/'compile.stdout.txt').write_bytes(compiled.stdout);(PUBLIC/'compile.stderr.txt').write_bytes(compiled.stderr)
    d.write(PUBLIC/'compile.json',dict(returncode=compiled.returncode,source=m.identity(text),compiler=subprocess.check_output(['cc','--version']).decode(),stdout=m.identity(compiled.stdout),stderr=m.identity(compiled.stderr),command=[v.replace(str(ROOT)+'/', '') for v in command],host_compiles=1,arm_compiles=0))
    m.need(compiled.returncode==0 and not compiled.stderr,'strict compilation')
    prefix=[str(runtime/'ld.so'),'--library-path',str(runtime/'lib'),str(exe)]
    guards={}
    for method in ('bus8','bus16','bus32','raw8','raw16','raw32','register'):
        p=subprocess.run(prefix+['--guard-check',method],capture_output=True,timeout=15)
        guards[method]=dict(returncode=p.returncode,stdout=m.identity(p.stdout),stderr=m.identity(p.stderr))
        d.write(PUBLIC/'guards.json',guards)
        m.need(p.returncode==1 and not p.stdout and p.stderr==b'research-save-impact: host write after observation barrier\n','new executable barrier '+method)
    results={}
    for i,case in enumerate(m.NAMES):
        directory=PUBLIC/case;directory.mkdir()
        save=OUT/(case+'.srm');save.write_bytes(fixture)
        inputs=m.commands(case);(directory/'commands.txt').write_bytes(inputs)
        start=time.monotonic()
        try:
            p=subprocess.run(prefix+[str(rom),str(save),str(i)],input=inputs,capture_output=True,timeout=150,cwd=directory)
            status=dict(returncode=p.returncode,timeout=False);out,err=p.stdout,p.stderr
        except subprocess.TimeoutExpired as exc:
            status=dict(returncode=None,timeout=True);out,err=exc.stdout or b'',exc.stderr or b''
        (directory/'stdout.txt').write_bytes(out);(directory/'stderr.txt').write_bytes(err)
        status.update(elapsed_seconds=round(time.monotonic()-start,3),stdout=m.identity(out),stderr=m.identity(err),commands=m.identity(inputs))
        try:
            m.need(status['returncode']==0 and not err,'clean measurement process')
            status['observation']=m.inspect(out,case,audit)
        except Exception as exc:
            status['observation_error']=dict(type=type(exc).__name__,reason=str(exc))
        status['screens']={p.name:m.identity(p.read_bytes()) for p in sorted(directory.glob('*.ppm'))}
        d.write(directory/'measurement.json',status);results[case]=status
        # The final record is assembled after every case; interruption still leaves raw output.
        d.write(PUBLIC/'measurement.json',dict(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),candidate=m.CANDIDATE,cases=results,host_compiles=1,arm_compiles=0,native_processes=len(results),guard_processes=len(guards),accepted_case_reruns=0,independent_oracle_accepted=False))
        print(case,status['returncode'],status.get('observation'),flush=True)
    m.need(d.bindings(PROTECTED)==protected and d.bindings(CODE)==source,'inputs/source unchanged')
    m.need(m.identity(rom.read_bytes())==m.CANDIDATE,'ROM read only')

def record():
    os.chdir(ROOT);d.current();m.need(not Path(CP).exists(),'immutable initial record')
    invocation=d.read(PUBLIC/'invocation.json');measurement=d.read(PUBLIC/'measurement.json')
    m.need(invocation['source_head']==measurement['source_head']==os.environ['GITHUB_SHA'],'exact measurement HEAD')
    m.need(d.bindings(PROTECTED)==invocation['protected_bindings'],'originals unchanged')
    root=Path(BASE)/os.environ['GITHUB_RUN_ID'];m.need(not root.exists(),'new evidence identity')
    evidence={}
    for p in sorted(PUBLIC.rglob('*')):
        if not p.is_file() or p.suffix not in ('.txt','.json'):continue
        b=p.read_bytes();b.decode('utf-8');m.need(b'\0' not in b,'text proof only')
        target=root/p.relative_to(PUBLIC);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b);evidence[str(target)]=m.identity(b)
    d.write(root/'manifest.json',evidence)
    previous=d.inputs.api('actions/runs/36283786399');m.need(previous['status']=='completed' and previous['conclusion']=='success','prior handoff repair terminal')
    cp=dict(schema_version=1,task='USER-20260927-RESEARCH-CONNECTION',status='MEASURED_PHYSICAL_CONNECTION_PENDING_INDEPENDENT_ORACLE',candidate=m.CANDIDATE,source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),measurement=str(root/'measurement.json'),manifest=str(root/'manifest.json'),source_bindings=invocation['source_bindings'],protected_bindings=invocation['protected_bindings'],prior_handoff_terminal=d.run_summary(previous),accepted_native_cases=[],preliminary_observations={k:v.get('observation',v.get('observation_error')) for k,v in measurement['cases'].items()},native_processes=measurement['native_processes'],guard_processes=measurement['guard_processes'],host_compiles=1,arm_compiles=0,rom_changes=0,accepted_case_reruns=0,local_predecessor=dict(raw_outputs_retained=False,reason_ja='会話実行環境のリセットにより未commit原本消失。ローカル3件の0終端を正式受入へ昇格しない。今回Actionsは未受入範囲の耐久的計測であり既受入再実行ではない。',host_compiles=2,guard_processes=7,native_processes=5,preflight_candidate_failures=1,completed_processes=3,interrupted_processes=1,generation_failures_before_compile=1),not_accepted=['independent-ledger-oracle','native-visual-review','counter-numeric-balance','natural-story-progress','naturally-earned-spending','all-activities','all-maps'],release_ready=False,active_baseline_changed=False,actions_completion_confirmed=False)
    d.write(CP,cp)
    goal='屋外4入口の未受入計測を原本固定。独立ledger/oracleと画面レビューで受入範囲を確定し、生態ガイドの未観測文言だけ追加調査する。受付数値残高の表示欠落・自然稼得RPのショップ支出接続は未完。GAME_CORNER/旧活動/今回の成功原本を無変更再実行しない。'
    guide='# PR16 研究受付・ショップ・ガイドの物理接続\n\n固定候補26dac23c。開始位置は屋外fixtureであり、ストーリー通しの自然到達ではない。barrier後は物理キーと読取のみ。\n\n'+goal+'\n\n## 現在の証拠\n\nsource `'+cp['source_head']+'` / run `'+str(cp['run_id'])+'`。`'+cp['measurement']+'` とmanifestを参照。計測のMEASUREDは正式PASSではない。受付数値表示は未実装の疑義があり、文言を見ただけで残高UIを受入しない。全RP稼得/購入/取消/Continueの旧成功は再実行していない。画像は専用Actions artifact、ROM/saveはGit管理外。\n\n## ローカル前試行\n\n生成前dir不足1、host compile2、guard7、native5（candidate事前拒否1、lab/fishing/game完走3、生態1は環境リセットで中断）。原本消失のため受入0。後継Actions原本で独立受入し、失敗や消失を成功へ改作しない。\n'
    Path(GUIDE).write_text(guide)
    state=d.read(d.STATE)
    state['research_connection']={'path':CP,'status':cp['status'],'candidate':m.CANDIDATE,'run_id':cp['run_id']}
    state['bp']['current_stop']=cp['status'];state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_CONNECTION_ORACLE_AND_ECOLOGY_NEXT',goal_ja=goal,read_paths=[GUIDE,CP,'scripts/pr16_research_connection.py',m.C],stop_rule_ja='固定ROM/seed/受入原本は不変。fixture屋外入口を通常ストーリー到達へ昇格しない。受入済み再実行・merge/release/baseline変更禁止。')
    state['do_not_repeat'].insert(0,'研究接続の新規MEASURED原本を先に照合。旧GAME_CORNER/写真/虫取り/採掘/釣り/生態の稼得nativeは再実行しない。今回の入口3成功計測は独立oracle/画面確認へ進み、未観測の生態ガイドだけ診断する。')
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='研究接続の新規測定source。自己run終端は後継で確認。旧ローカル消失原本は正式受入しない。'
    state['observed_head_checks']={'scope_head':os.environ['GITHUB_SHA'],'runs':[{'id':cp['run_id'],'head_sha':os.environ['GITHUB_SHA'],'status':'in_progress','conclusion':None}], 'reason_ja':'前handoff36283786399は成功確認済み。本runは原本記録のみで正式native受入/自己終端/全CI成功はまだ主張しない。'}
    for p in CODE|{CP,GUIDE}:state['source_bindings'][p]=m.identity(Path(p).read_bytes())
    from pr16_learnset_compact_record import publish_resume
    publish_resume(state)
    now=datetime.datetime.now(datetime.timezone.utc).isoformat()
    log=f'\n## {now}\n- Timestamp: {now}\n- Task: USER-20260927-RESEARCH-CONNECTION / 屋外入口と未確認文言の原本固定\n- Version: research-connection-measured-v1\n- Status: STOPPED（計測原本を固定、独立oracle/画面受入へ）\n- Summary: 新4入口の限定入力probeを実装。受付残高数値欠落を未完保持、屋外fixtureと通常ストーリーを区別。前ローカル環境リセットの原本消失/失敗はcheckpointで明記。\n- Files changed: 専用C/Python/Actions、UTF8原本/checkpoint/専用MD、固定再開MD/JSON、両ログ。\n- Verify: strict host compile1、guard7拒否、native4計測、ARM/ROM変更/受入済み再実行0。正式native受入は独立oracleと画像照合まで0。source hash/保全原本/resume/task graph/最終index scoped guard。\n- Commit: source={os.environ["GITHUB_SHA"]}; 同branchへ非force push。自己SHAはgit log参照。\n- Network: 固定GitHub artifactとPR/Actionsのみ。merge/release/baseline変更なし。全体private guard成功は主張しない。\n'
    for path in d.LOGS:
        with Path(path).open('a',encoding='utf-8') as f:f.write(log)
    owned=set(evidence)|{str(root/'manifest.json'),CP,GUIDE,d.STATE,d.DOC}|d.LOGS
    d.write(OUT/'owned.json',sorted(owned))

def guard():
    import pr16_resume
    import pr16_learnset_runtime_record as g
    os.chdir(ROOT);d.current();pr16_resume.validate(ROOT)
    g.START=START;g.CODE=CODE;g.OWNED=set(d.read(OUT/'owned.json'));g.guard()
    m.need(d.bindings(PROTECTED)==d.read(CP)['protected_bindings'],'protected byte identity')
    subprocess.run(['git','diff','--cached','--check'],check=True)

if __name__=='__main__':
    if sys.argv[1:]==['measure']:measure()
    elif sys.argv[1:]==['record']:record()
    elif sys.argv[1:]==['guard']:guard()
    elif sys.argv[1:]==['paths']:print('\n'.join(d.read(OUT/'owned.json')))
    else:raise SystemExit('measure|record|guard|paths')
