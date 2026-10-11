#!/usr/bin/env python3
"""新しいC host境界を一回検証し、正本・両ログを同branchへ保存する。"""
from __future__ import annotations
import datetime
import importlib.util
import io
import os
from pathlib import Path
import subprocess
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT)]
import pr16_research_phase0_load_actions as prior
import pr16_research_ui_boundary as m
d = prior.d
need, identity = prior.need, prior.identity
TASK = 'USER-20260926-RESEARCH-UI-BOUNDARY'
SELF = 'scripts/pr16_research_ui_boundary_actions.py'
MODEL = 'scripts/pr16_research_ui_boundary.py'
TEST = 'tests/test_pr16_research_ui_boundary.py'
SHIM = 'tools/research_ui_boundary_shim.c'
WF = '.github/workflows/pr16-research-ui-boundary-20260926.yml'
CP = 'content/modernization/pr16_research_ui_boundary_checkpoint.json'
GUIDE = 'docs/PR16_RESEARCH_UI_BOUNDARY_JA.md'
EVIDENCE = 'content/modernization/pr16_research_ui_boundary_evidence'
OWN_SOURCE = {SELF, MODEL, TEST, SHIM, WF}


def publish(cp, evidence):
    from pr16_learnset_compact_record import publish_resume
    summary = '正本Cの新規ゲーム初期化と取引UI callbackの限定host境界49試験PASS。通常native new-game/実取引は未受入。候補5d1fc9c4と既受入loadは保持。'
    goal = '次は通常new-game入口→初回通常Save/Continue、および実取引UIの取消/選択/購入/保存をnativeで限定検証する。host49件とphase0 load2件/43unit、V1 load3件/40unit、7retryは変更影響なしに再実行しない。'
    if not cp['actions_completion_confirmed']:
        goal = 'まず本runの終端とpush/uploadを照合し、host49件を再実行せず受入記録を確定する。' + goal
    d.write(ROOT/CP, cp)
    text = '# PR16 新規ゲーム初期化・取引UIのC host境界\n\n'+summary+'\n\n## 受入範囲\n\n正本22関数をexact Git blobから無改変抽出。44個のC正常境界と5個の抽出/不正要求検査、計49 unittest。新規初期化は2048byte全体・独立checksum・両端canary・badge 0/1/255・NULL・再初期化を確認。UIは全23選択位置/5ページ、絞込後catalog対応、B/末尾取消、入力待ち/不正行、task/window生成失敗、次ページ描画失敗、残高0/9999、NULL行文言、PostShopMenu、未選択購入拒否と選択済み購入委譲を確認。全選択で購入前ledger/owner不変、task/window解放とscript context復帰を検査。\n\n## 限界\n\nこれはhost上の正本C制御フロー試験であり、ARM ABI・実描画/日本語文言・正規NPC到達・実Bag/Flash取引・初回通常Save/Continueを証明しない。engineサービスとunlock/catalog表示は明示stub。PurchaseByIndex本体はstubであり、購入成功を受入しない。normal_new_game_accepted=false / transaction_ui_accepted=falseを保持。旧native/単体再実行0、ROM変更/ARM compile/link0、mGBA実行0、host compile1。\n\n## 次工程\n\n'+goal+'\n\nrun `'+str(cp['run_id'])+'` / source `'+cp['source_head']+'` / 終端照合 `'+str(cp['actions_completion_confirmed'])+'`。source/protected bindingsと原本manifestはcheckpoint参照。一般CI action_requiredは全CI成功に読み替えない。\n'
    (ROOT/GUIDE).write_text(text)
    state = d.read(ROOT/d.STATE)
    state['research_ui_boundary'] = {k: cp[k] for k in ('status','source_head','run_id','actions_completion_confirmed','new_unit_tests','normal_new_game_accepted','transaction_ui_accepted')}
    state['research_ui_boundary']['path'] = CP
    state['bp']['current_stop'] = summary
    state['bp']['next_step'] = goal
    state['next_action'] = dict(state['next_action'], id='RESEARCH_NORMAL_NEW_GAME_TRANSACTION_UI_NATIVE_NEXT', goal_ja=goal,
        read_paths=[GUIDE,CP,MODEL,SELF,SHIM,prior.CP,m.SOURCE,'overlays/qol_production/qol_production.c'],
        stop_rule_ja='host検証をnative受入にしない。既受入を反復せず、候補/旧証拠/旧Wikiを保持。merge/release/active baseline変更禁止。')
    state['observed_head'] = os.environ['GITHUB_SHA']
    state['observed_head_semantics'] = '限定host境界の実行または終端記録source。自己SHAはgit log参照。'
    state['observed_head_checks'] = {'scope_head':cp['source_head'],'runs':[{'id':cp['run_id'],'head_sha':cp['source_head'],'status':'completed' if cp['actions_completion_confirmed'] else 'in_progress','conclusion':'success' if cp['actions_completion_confirmed'] else None}],'reason_ja':'限定host境界のみ。一般CIのaction_requiredは別状態。'}
    for path in OWN_SOURCE | {CP,GUIDE}:
        state['source_bindings'][path] = identity((ROOT/path).read_bytes())
    state['logs_synchronized'] = True
    publish_resume(state)
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    log = f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 新規ゲーム初期化と取引UIの正本C host境界\n- Version: research-ui-boundary-v1\n- Status: DONE（限定host境界、通常nativeは未受入）\n- Summary: '+summary+'\n- Files changed: '+', '.join(sorted(OWN_SOURCE | {CP,GUIDE,d.STATE,d.DOC} | d.LOGS))+'、限定証拠。\n- Verify: 新unit49PASS/host compile1（終端記録時は再実行0）。22正本関数と2048byte初期化、全23選択/取消/資源解放を検証。旧受入再実行/native/ARM/ROM変更0。resume check/task graph/scoped final-index guard/diff-checkは同runの後続gate。全体歴史guard成功は主張しない。終端確認='+str(cp['actions_completion_confirmed'])+'。\n- Commit: source='+os.environ['GITHUB_SHA']+'、同branch非force。自己SHAはgit log。\n- Network: GitHub Actions API/先行終端照合。私有入力取得0、外部調査0。merge/release/active baseline変更0。\n'
    for path in d.LOGS:
        with (ROOT/path).open('a') as f: f.write(log)
    owned = evidence | {CP,GUIDE,d.STATE,d.DOC} | d.LOGS
    d.write(d.OUT/'ui-boundary-owned.json', sorted(owned))
    d.put('record-summary.json', {k: cp[k] for k in ('status','run_id','new_unit_tests','actions_completion_confirmed')})


def measure():
    os.chdir(ROOT); d.current(); d.PUBLIC.mkdir(parents=True)
    need(not (ROOT/CP).exists(), 'already measured: do not rerun')
    old = d.read(ROOT/prior.CP)
    need(old['actions_completion_confirmed'] and old['accepted_native_cases'] == 2 and not old['failed_cases'], 'accepted phase0 baseline')
    terminal = prior.terminal(old['finalize_run_id'],old['finalize_source_head'],prior.WF)
    tracked = d.git('ls-files').decode().splitlines()
    need(not [p for p in tracked if p.endswith('/AGENTS.md') and p.split('/')[0] in ('scripts','tools','tests','content','docs','design')], 'nested rules require review')
    protected_paths = set(old['protected_bindings']) | set(old['source_bindings']) | {prior.CP,prior.GUIDE,m.SOURCE,'overlays/research_economy_v1/research_economy_v1.h'}
    protected_paths |= {p for p in tracked if p.startswith(prior.EVIDENCE+'/')}
    protected = d.bindings(protected_paths)
    sources = d.bindings(OWN_SOURCE | {m.SOURCE,'overlays/research_economy_v1/research_economy_v1.h'})
    d.put('invocation.json', {'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'source_bindings':sources,'protected_bindings':protected,'prior_terminal':terminal})
    spec = importlib.util.spec_from_file_location('new_ui_boundary_tests', ROOT/TEST)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    suite = unittest.defaultTestLoader.loadTestsFromModule(module)
    stream = io.StringIO(); result = unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    unit = stream.getvalue(); (d.PUBLIC/'unit.txt').write_text(unit); print(unit,flush=True)
    report = {'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'successful':result.wasSuccessful(),'native_processes':0,'arm_compiles':0,'accepted_case_reruns':0}
    if hasattr(module.CanonicalUIBoundaryTests,'generated_sha256'):
        report.update(generated_sha256=module.CanonicalUIBoundaryTests.generated_sha256,function_bindings=module.CanonicalUIBoundaryTests.bindings)
    d.put('unit.json', report)
    need(result.wasSuccessful() and result.testsRun == 49 and not result.skipped, 'new scoped 49 tests')
    need(d.bindings(protected) == protected and d.bindings(sources) == sources, 'source and historical acceptance preservation')
    directory = EVIDENCE+'/'+os.environ['GITHUB_RUN_ID']; need(not (ROOT/directory).exists(),'immutable evidence')
    evidence = {}
    for p in sorted(d.PUBLIC.iterdir()):
        need(p.is_file() and p.suffix in ('.json','.txt'), 'public text only')
        raw = p.read_bytes(); raw.decode('utf-8'); need(b'\0' not in raw, 'no binary')
        target = ROOT/directory/p.name; target.parent.mkdir(parents=True,exist_ok=True); target.write_bytes(raw)
        evidence[str(target.relative_to(ROOT))] = identity(raw)
    d.write(ROOT/directory/'manifest.json', evidence)
    cp = {'schema_version':1,'task':TASK,'status':'PASS_HOST_UI_BOUNDARY_PENDING_TERMINAL','source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),'source_bindings':sources,'protected_bindings':protected,'candidate':old['candidate'],'new_unit_tests':49,'host_compiles':1,'native_processes':0,'arm_compiles':0,'arm_links':0,'rom_changes':0,'accepted_case_reruns':0,'normal_new_game_accepted':False,'transaction_ui_accepted':False,'actions_completion_confirmed':False,'active_baseline_changed':False,'release_ready':False,'issue19_complete':False,'manifest':directory+'/manifest.json','measurement':directory+'/unit.json','prior_terminal':terminal}
    publish(cp, set(evidence) | {directory+'/manifest.json'})


def finalize():
    os.chdir(ROOT); d.current(); d.PUBLIC.mkdir(parents=True)
    cp = d.read(ROOT/CP); need(not cp['actions_completion_confirmed'], 'already finalized')
    need(d.bindings(cp['protected_bindings']) == cp['protected_bindings'], 'protected history')
    for path,binding in cp['source_bindings'].items():
        if path != WF: need(identity((ROOT/path).read_bytes()) == binding, 'unchanged measured source '+path)
    cp['terminal'] = prior.terminal(cp['run_id'],cp['source_head'],WF)
    cp.update(status='PASS_CANONICAL_HOST_UI_BOUNDARY',actions_completion_confirmed=True,finalize_run_id=int(os.environ['GITHUB_RUN_ID']),finalize_source_head=os.environ['GITHUB_SHA'])
    d.put('terminal-verification.json', cp['terminal']); publish(cp,set())


def guard():
    os.chdir(ROOT); cp = d.read(ROOT/CP); owned = set(d.read(d.OUT/'ui-boundary-owned.json'))
    need(d.bindings(cp['protected_bindings']) == cp['protected_bindings'], 'protected paths unchanged')
    subprocess.run(['git','add','--',*sorted(owned)],check=True)
    import pr16_learnset_runtime_record as g
    g.START = os.environ['GITHUB_SHA']; g.CODE = set(); g.OWNED = owned; g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)

if __name__ == '__main__':
    if sys.argv[1:] == ['measure']: measure()
    elif sys.argv[1:] == ['finalize']: finalize()
    elif sys.argv[1:] == ['guard']: guard()
    else: raise SystemExit('measure | finalize | guard')
