#!/usr/bin/env python3
"""全catalogだけを実行して記録。終端同期ではunit/native/compileを繰り返さない。"""
from __future__ import annotations
import datetime
import os
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'),str(ROOT)]
import pr16_research_catalog as m
import pr16_research_lifecycle_actions as d
import pr16_research_purchase as purchase
from pr16_research_phase0_load_actions import terminal
need, identity = m.need, m.identity
TASK = 'USER-20260927-RESEARCH-SUPPLY'
SELF = 'scripts/pr16_research_catalog_actions.py'
WF = '.github/workflows/pr16-research-supply-20260927.yml'
CP = 'content/modernization/pr16_research_catalog_checkpoint.json'
GUIDE = 'docs/PR16_RESEARCH_CATALOG_JA.md'
BASE = 'content/modernization/pr16_research_catalog_evidence'
PREVIOUS = 'content/modernization/pr16_research_new_game_checkpoint.json'
INITIAL = 'db6796aefc755e87c4ead86e54d240cae1c2a6d5'
OWN = {SELF, WF, m.C, 'scripts/pr16_research_catalog.py', 'tests/test_pr16_research_catalog.py'}
SCREENS = d.OUT/'catalog-screens'
REVIEWED = ['c63bba1e14a0d88958f07345ca68eb72538c2a505db3309f99d70a1ccc8f18dc',
            'f83d88cc7bd9ba9375cfafdc2946237b4cb3c702b7f63f5885b614ae5c173245',
            '9ffa1ff8b7b4396b14a87263af308f63c39beac1272ce479c8777e2b6ee736ac',
            '1c7fda7f77b36b00c00b808376c5e003f2ed85032d12023eeea4843152fdf764',
            '1d226381fcc02a51a02991f9cdb3314b95959cd7699a64aa594771350b09d6f3']

def run_logged(name, args, timeout=120, cwd=ROOT):
    p = subprocess.run(args, cwd=cwd, capture_output=True, timeout=timeout)
    (d.PUBLIC/(name+'.stdout.txt')).write_bytes(p.stdout)
    (d.PUBLIC/(name+'.stderr.txt')).write_bytes(p.stderr)
    return p

def measure():
    d.current();need(not (ROOT/CP).exists(), '既存catalog記録の再実行禁止')
    d.PUBLIC.mkdir(parents=True); SCREENS.mkdir()
    old = d.read(PREVIOUS)
    need(old['actions_completion_confirmed'] and old['normal_new_game_accepted']
         and not old['failed_cases'] and old['candidate'] == m.CANDIDATE, '前工程受入を継承')
    prior = terminal(old['finalize_run_id'],old['finalize_source_head'],'.github/workflows/pr16-research-new-game-20260926.yml')
    sources = d.bindings(set(old['source_bindings']) | OWN | {m.MODEL,m.ITEMS})
    protected = d.bindings(set(old['protected_bindings']) | set(old['source_bindings']) | {PREVIOUS})
    d.put('invocation.json',dict(source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
          source_bindings=sources,protected_bindings=protected,prior_terminal=prior))
    stats = dict(new_unit_tests=0,host_compiles=0,native_processes=0,guard_processes=0,
                 arm_compiles=0,arm_links=0,rom_changes=0,accepted_case_reruns=0)
    result = dict(status='FAIL',counts=stats,failures=[])
    try:
        unit = run_logged('unit',[sys.executable,'-B','-m','unittest','discover','-s','tests','-p','test_pr16_research_catalog.py','-v'])
        stats['new_unit_tests'] = (unit.stdout+unit.stderr).count(b' ... ok\n')
        need(unit.returncode == 0 and stats['new_unit_tests'] == 86, '新規86 oracle')
        runtime,data,seed,parent,artifacts = d.restore()
        import pr16_research_retry as retry
        import pr16_research_v1_corrupt_load as corrupt
        candidate,_ = retry.apply(parent,bytes.fromhex(d.read('content/modernization/pr16_research_retry_recipe.json')['after']))
        recipe = d.read('content/modernization/pr16_research_v1_corrupt_load_recipe.json')
        candidate,_ = corrupt.apply(candidate,bytes.fromhex(recipe['after'])[:corrupt.CODE['size']])
        d.put('catalog-audit.json',m.audit(candidate))
        rom = d.OUT/'catalog-candidate.gba';rom.write_bytes(candidate)
        save = d.OUT/'catalog.srm';fixture,receipt=purchase.fixture(seed);save.write_bytes(fixture)
        code = d.OUT/'catalog.c';code.write_bytes(m.generate(seed));exe=d.OUT/'catalog-runner'
        d.put('inputs.json',dict(candidate=identity(candidate),seed=identity(seed),fixture=receipt,
              runtime_artifacts=artifacts,generated_source=identity(code.read_bytes()),
              additional_stopped_flagset=['VEGA_DH_CLEAR'],natural_progress_claimed=False))
        stats['host_compiles'] = 1
        command=['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-Itools','-I.',
                 '-I'+str(runtime/'include'),str(code),'-L'+str(runtime/'lib'),'-lmgba','-lm','-Wl,--allow-shlib-undefined','-o',str(exe)]
        p=run_logged('compile',command);need(p.returncode==0 and not p.stderr,'strict host compile')
        d.put('compile.json',dict(command=command,compiler=subprocess.check_output(['cc','--version']).decode(),
                                 executable=identity(exe.read_bytes()),source=identity(code.read_bytes())))
        prefix=[str((runtime/'ld.so').resolve()),'--library-path',str((runtime/'lib').resolve()),str(exe.resolve())]
        for method in ('bus8','bus16','bus32','raw8','raw16','raw32','register'):
            stats['guard_processes']+=1;p=run_logged('guard-'+method,prefix+['--guard-check',method],10)
            need(p.returncode==1 and not p.stdout and p.stderr==b'research-save-impact: host write after observation barrier\n','7 API拒否 '+method)
        stats['native_processes']=1
        p=run_logged('native',prefix+[str(rom.resolve()),str(save.resolve()),m.CASE],180,SCREENS)
        need(p.returncode==0 and not p.stderr,'native正常終了')
        native=m.validate_native(p.stdout)
        for page,expected in enumerate(REVIEWED):
            raw=(SCREENS/f'catalog-page-{page}.ppm').read_bytes()
            need(raw.startswith(b'P6\n240 160\n255\n') and len(raw)==115215,'実240x160画像')
            need(identity(raw)['sha256']==native['screens'][page]['screen_sha256']==expected,'目視済み原本と同一画面')
        result.update(status='PASS',native=native,visual_review=dict(status='PASS',reviewed_sha256=REVIEWED,
            note_ja='5ページすべての商品名/価格/つぎ/やめるは正本と一致し、行末欠けなし。数量は商品ABIの照合であり画面表示とは主張しない。35会話のnative全表示は未受入。'))
    except Exception as exc:
        result['failures'].append(dict(type=type(exc).__name__,reason=str(exc)))
    need(d.bindings(sources)==sources and d.bindings(protected)==protected,'旧受入/source保全')
    result['local_diagnostics']=dict(host_compiles=3,native_processes=3,new_unit_tests=86,
        failures=['19商品はDH未解放fixture。観測前の正規FlagSet1回を追加。',
                  '最初の5画像はvideo reset前接続不足で黒一色。専用起動だけを修正し非空/異なるhashを検査。'],
        final='全23商品/5画面と86oracleが成功。これを既存保存/購入/取消受入の再実行に数えない。')
    d.put('measurement.json',result)
    directory=BASE+'/'+os.environ['GITHUB_RUN_ID'];need(not (ROOT/directory).exists(),'原本は追記専用')
    manifest={}
    for path in sorted(d.PUBLIC.iterdir()):
        raw=path.read_bytes();raw.decode('utf-8');need(path.suffix in ('.txt','.json') and b'\0' not in raw and len(raw)<2000000,'UTF8原本のみ')
        dest=Path(directory)/path.name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw);manifest[str(dest)]=identity(raw)
    d.write(Path(directory)/'manifest.json',manifest)
    cp=dict(schema_version=1,task=TASK,source_head=os.environ['GITHUB_SHA'],run_id=int(os.environ['GITHUB_RUN_ID']),
            candidate=m.CANDIDATE,source_bindings=sources,protected_bindings=protected,
            status='PASS_CATALOG_PENDING_TERMINAL' if result['status']=='PASS' else 'FAIL_CATALOG_RECORDED',
            catalog_accepted=result['status']=='PASS',actions_completion_confirmed=False,
            measurement=directory+'/measurement.json',manifest=directory+'/manifest.json',counts=stats,
            failed_cases=[] if result['status']=='PASS' else [m.CASE],natural_progress_accepted=False,
            real_rp_earning_accepted=False,all_dialogue_native_display_accepted=False,release_ready=False,active_baseline_changed=False)
    publish(cp,set(manifest)|{directory+'/manifest.json'},'measure')

def publish(cp, owned, mode):
    from pr16_learnset_compact_record import publish_resume
    d.write(CP,cp)
    goal='次は実RP稼得と通常進行からResearchショップへの接続。全23商品価格/数量/解放/在庫/日本語行・5画面と35会話ROM byte監査は受入済み原本を再利用する。35会話のnative全表示/自然到達は別の未完境界。'
    text='# PR16 Research catalog価格・日本語監査\n\n'+cp['status']+'\n\n'+goal+'\n\n'
    text+='## 方法と限定範囲\n\nitem manifest/canonical model/実ROMの23 ABI行を結合し、価格・数量・解放条件・在庫・pointer・終端を全件照合する。35会話は正本と実ROMのbyte一致と内部符号整合性だけ。独立charmapや35会話の実表示とは呼ばない。\n\n'
    text+='表示は明示進行/10RP fixtureと停止中のDH FlagSet1回、stock warpを使う。7 API barrier後はキー入力だけで全5pageを採取し、未選択のまま終了。RP・全Bag・party600・ledger2048（自然minuteを除く）・Flash131072と保存counterを保持し、購入/取消/Saveケースは実行しない。5画面の日本語名と価格を目視し、Actionsの実画面hashも照合。bundle数量はABIであり行には表示されない既存仕様。\n\n'
    text+='## 原本と継承\n\nsource `'+cp['source_head']+'` / run `'+str(cp['run_id'])+'` / `'+cp['measurement']+'`。新規86oracle/host compile1/native1/guard7、ARM0。ローカル準備はcompile3/native3（19商品fixtureと黒画面の2診断失敗を含む）/86oracle1回。終端同期では再実行0。通常new-game・購入・取消・旧host/phase0/V1/retry・BP/P08の受入原本は保全。\n'
    Path(GUIDE).write_text(text)
    state=d.read(d.STATE);state['research_catalog']={k:cp[k] for k in ('status','source_head','run_id','catalog_accepted','actions_completion_confirmed','candidate')}
    state['research_catalog']['path']=CP
    state['bp']['current_stop']=cp['status'];state['bp']['next_step']=goal
    state['next_action']=dict(state['next_action'],id='RESEARCH_REAL_RP_AND_NATURAL_CONNECTION_NEXT',goal_ja=goal,
        read_paths=[GUIDE,CP,'scripts/pr16_research_catalog.py',SELF,m.C,'docs/PR16_RESEARCH_NEW_GAME_JA.md',PREVIOUS,
                    'overlays/research_economy_v1/research_economy_v1.c',m.MODEL])
    state['observed_head']=os.environ['GITHUB_SHA'];state['observed_head_semantics']='catalog限定記録source。自己commitはgit log参照。'
    latest=d.inputs.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=12')['workflow_runs']
    state['observed_head_checks']={'scope_head':os.environ['GITHUB_SHA'],'runs':[d.run_summary(r) for r in latest],
        'reason_ja':'限定工程と全体CIを区別。source-validation既存failure/承認待ちを全CI成功へ昇格しない。'}
    for path in OWN|{CP,GUIDE}:state['source_bindings'][path]=identity(Path(path).read_bytes())
    note='catalog23商品/5画面・35会話ROM byteは専用checkpointを参照。native全会話/自然RP/通常進行とは分離し、受入済み保存/購入/取消を再実行しない。'
    if note not in state['do_not_repeat']:state['do_not_repeat'].insert(0,note)
    state['observed_date_jst']=datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat()
    state['logs_synchronized']=True;publish_resume(state)
    stamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
    line=f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 全catalog価格と日本語監査\n- Version: research-catalog-v1\n- Status: '+('DONE' if cp['catalog_accepted'] else 'BLOCKED')+'（限定scope）\n- Summary: '+cp['status']+' / '+mode+'。23商品と35会話ROM byte、5page表示。自然RP/通常進行/35会話native全表示は未受入。\n- Files changed: catalog validator/native/oracle/Actions、専用証拠/MD/JSON、固定引継ぎ、両ログ。\n- Verify: 新規86oracle、host1/native1/guard7、ARM0。準備診断compile3/native3、2失敗を保存し専用fixture/videoだけ修正。終端はunit/native/compile0。旧受入ケース再実行0。resume/task graph/限定index guardをcommit前に検査。\n- Commit: 同branch非force push、source='+os.environ['GITHUB_SHA']+'。自己SHAはgit log参照。\n- Network: 接続済みGitHub APIと固定SHA artifactのみ。全体CI成功/releaseは主張しない。ROM/saveは非tracked、active baseline不変。\n'
    for path in sorted(d.LOGS):
        with Path(path).open('a') as stream:stream.write(line)
    d.write(d.OUT/'catalog-owned.json',sorted(owned|{CP,GUIDE,d.STATE,d.DOC}|d.LOGS))

def finalize():
    d.current();d.PUBLIC.mkdir(parents=True);cp=d.read(CP)
    need(cp['catalog_accepted'] and not cp['failed_cases'] and not cp['actions_completion_confirmed'],'一度だけ終端確認')
    need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'履歴保全')
    for path,binding in cp['source_bindings'].items():
        if path!=WF:need(identity(Path(path).read_bytes())==binding,'原本source一致 '+path)
    cp['terminal']=terminal(cp['run_id'],cp['source_head'],WF)
    cp.update(status='PASS_CATALOG_SCOPED',actions_completion_confirmed=True,
              finalize_run_id=int(os.environ['GITHUB_RUN_ID']),finalize_source_head=os.environ['GITHUB_SHA'])
    d.put('terminal-verification.json',cp['terminal']);publish(cp,set(),'finalize')

def guard():
    cp=d.read(CP);need(d.bindings(cp['protected_bindings'])==cp['protected_bindings'],'旧受入保全')
    owned=set(d.read(d.OUT/'catalog-owned.json'))
    subprocess.run(['git','add','--',*sorted(owned)],check=True)
    import pr16_learnset_runtime_record as g
    g.START=os.environ['GITHUB_SHA'];g.CODE=set();g.OWNED=owned;g.guard()
    changed=set(d.git('diff','--cached','--name-only',INITIAL).decode().splitlines())
    allowed=OWN|{CP,GUIDE,d.STATE,d.DOC}|d.LOGS
    need(all(p in allowed or p.startswith(BASE+'/') for p in changed),'開始HEADからの全差分限定')
    for p in d.LOGS:need(Path(p).read_bytes().startswith(d.git('show',INITIAL+':'+p)),'両ログappend-only')
    subprocess.run(['git','diff','--cached','--check'],check=True)

if __name__=='__main__':
    os.chdir(ROOT)
    if sys.argv[1:]==['measure']:measure()
    elif sys.argv[1:]==['finalize']:finalize()
    elif sys.argv[1:]==['guard']:guard()
    elif sys.argv[1:]==['result']:need(not d.read(CP)['failed_cases'],'失敗原本を保持し未受入')
    else:raise SystemExit('measure | finalize | guard | result')
