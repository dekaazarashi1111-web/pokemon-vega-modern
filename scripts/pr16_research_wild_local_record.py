#!/usr/bin/env python3
"""新しい釣り/生態のローカル原本を照合・記録。旧native/ARM/unitの再実行は禁止。"""
from __future__ import annotations
import datetime
import difflib
import json
import os
from pathlib import Path
import subprocess
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / 'scripts'), str(ROOT)]
import pr16_research_lifecycle_actions as d
import pr16_research_wild_oracle as oracle
from pr16_learnset_compact_record import publish_resume
need, identity = oracle.need, oracle.identity
TASK = 'USER-20260927-RESEARCH-WILD'
START = 'f7f3bb73b822bf995bef404e953b18b7096c428c'
CP = 'content/modernization/pr16_research_wild_checkpoint.json'
GUIDE = 'docs/PR16_RESEARCH_WILD_JA.md'
BASE = 'content/modernization/pr16_research_wild_local_evidence'
MINING = 'content/modernization/pr16_research_mining_checkpoint.json'
SELF = 'scripts/pr16_research_wild_local_record.py'
MODEL = 'scripts/pr16_research_wild_oracle.py'
TEST = 'tests/test_pr16_research_wild_oracle.py'
C = 'tools/mgba_pr16_research_wild.c'
CAPTURE = 'scripts/pr16_research_wild_capture.py'
TRANSPORT = 'content/modernization/pr16_research_wild_local_transport.json'
WF = '.github/workflows/pr16-research-wild-local-record-20260927.yml'
OUT = Path('.local/pr16-research-wild-local-record')
CODE = {WF, TRANSPORT} | {'content/modernization/pr16_research_wild_local_transport/'+str(i)+'.txt' for i in range(1,5)}


def fishing_reuse():
    """全差分が到達不能なecology分岐かそのローカル初期化だけであることを検査。"""
    before = Path(BASE + '/fishing-source.c.txt').read_text()
    after = Path(C).read_text()
    expected = Path(BASE + '/ecology-only-source.diff.txt').read_text()
    need(''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                fromfile='successful-fishing-source', tofile='current-ecology-source')) == expected,
         'complete exact ecology-only delta')
    def strip_menu(text):
        start = ' if(!rw_fishing){\n'
        end = ' }\n unsigned idle='
        need(text.count(start) == text.count(end) == 1, 'one ecology-only menu block')
        a, b = text.index(start), text.index(end)
        need(a < b and 'rw_bag(c)' in text[:a], 'closed method-specific physical menu')
        return text[:a] + ' /* unreachable when fishing */\n' + text[b+3:]
    prefix = '  /* A stock radar miss returns to the field without arming research.\n'
    suffix = '  }else eco_idle=0;\n'
    need(after.count(prefix) == after.count(suffix) == 1, 'one new radar-only miss branch')
    a, b = after.index(prefix), after.index(suffix) + len(suffix)
    branch = after[a:b]
    need('if(!rw_fishing&&f>120&&!read32(c,ADDR_NEW_BATTLE_STRUCT_POINTER)&&si_field(c)){' in branch,
         'new miss branch short-circuited for fishing')
    after = after[:a] + after[b:]
    need(after.count('unsigned idle=0,eco_idle=0;') == 1, 'local scalar initialization only')
    after = after.replace('unsigned idle=0,eco_idle=0;', 'unsigned idle=0;')
    need(strip_menu(before) == strip_menu(after), 'all fishing-reachable code bytes unchanged')
    return dict(status='PASS_FISHING_REACHABLE_SOURCE_UNCHANGED',
                original=identity(before.encode()), current=identity(Path(C).read_bytes()), native_replays=0)


def verify():
    predecessor = d.read(MINING)
    need(predecessor['actions_completion_confirmed'] and predecessor['candidate'] == oracle.CANDIDATE,
         'accepted mining predecessor')
    need(d.bindings(predecessor['source_bindings']) == predecessor['source_bindings'], 'old accepted source bytes unchanged')
    need(d.bindings(predecessor['protected_bindings']) == predecessor['protected_bindings'], 'old accepted evidence bytes unchanged')
    closure = d.read(BASE + '/source-closure.json')
    need(closure['candidate'] == oracle.CANDIDATE and d.bindings(closure['source_bindings']) == closure['source_bindings'], 'exact immutable source/ROM closure')
    manifest = d.read(BASE + '/input-manifest.json')
    need(d.bindings(manifest) == manifest, 'every transported source and receipt bound')
    local = d.read(BASE + '/development.json')
    need(local['counts'] == dict(local_host_compiles=4, local_native_processes=5, guard_processes=7,
         prior_actions_host_compile_failures=1, prior_actions_native_processes=0, arm_compiles=0, accepted_case_reruns=0),
         'complete execution accounting including failure and interrupted attempt')
    need(len(local['host_compiles']) == 4 and len(local['native_processes']) == 5, 'complete local history')
    need(all(r['returncode'] == 0 and not r['stderr'] and not r['stdout'] for r in local['host_compiles']), 'all four strict local compiles')
    for index in (0, 2):
        need(local['native_processes'][index]['returncode'] == 1, 'two failures retained, not rewritten')
    interrupted = local['native_processes'][3]
    need(interrupted['status'] == 'INTERRUPTED_NOT_ACCEPTED' and interrupted['returncode'] is None
         and interrupted['stdout_available'] is False, 'interrupted attempt is not evidence of PASS')
    need([r['method'] for r in local['guards']] == ['bus8','bus16','bus32','raw8','raw16','raw32','register'], 'all seven guarded host APIs')
    for row in local['guards']:
        need(row['returncode'] == 1 and not row['stdout'] and row['stderr'] == 'research-save-impact: host write after observation barrier\n', 'unchanged inherited guard executed')
    review = d.read(BASE + '/visual-review.json')
    need(review['candidate'] == oracle.CANDIDATE and review['native_processes'] == 0 and review['ocr_calls'] == 0, 'real image review scope')
    results = {}
    for method, index in [('fishing', 1), ('ecology', 4)]:
        row = local['native_processes'][index]
        raw = Path(BASE + '/' + method + '.stdout.txt').read_bytes()
        need(row['method'] == method and row['returncode'] == 0 and not row['timeout'] and not row['stderr'], 'strict process success')
        need(raw == row['stdout'].encode() and identity(raw) == row['stdout_identity'] and identity(b'') == row['stderr_identity'], 'original stdout/stderr bytes')
        need(row['fixture']['fixture'] == oracle.FIXTURE and row['fixture']['initial_rp'] == 0 and not row['fixture']['balance_credit_injected'], 'same zero-RP private fixture')
        results[method] = oracle.validate(raw, method, review['images'][method])
        need(results[method] == d.read(BASE + '/' + method + '.oracle.json'), 'saved independent whole-ledger result')
        need(row['screens'] == {name: dict(size=115215, sha256=sha) for name, sha in review['images'][method].items()}, 'all ten complete PPM bindings')
        original_source = Path(BASE + '/fishing-source.c.txt').read_bytes() if method == 'fishing' else Path(C).read_bytes()
        need(identity(original_source) == row['source_binding'] and identity(Path('scripts/pr16_research_wild.py').read_bytes()) == row['generator_binding'], 'exact compiled host source/generator')
        need(row['generated_source'] == local['host_compiles'][1 if method == 'fishing' else 3]['generated_source'], 'case uses successful source-bound compile')
    unit = d.read(BASE + '/unit.json')
    need(unit['returncode'] == 0 and unit['passed'] == 65 and unit['stderr'].count(' ... ok\n') == 65
         and not unit['stdout'] and unit['native_processes'] == unit['compiles'] == 0, '65 original new tests, no rerun')
    need(d.bindings(unit['source_bindings']) == unit['source_bindings'], 'new unit source pins unchanged')
    reuse = fishing_reuse()
    prior = d.read('content/modernization/pr16_research_wild_evidence/36273917599/measurement.json')
    need(prior['counts']['host_compiles'] == 1 and prior['counts']['native_processes'] == 0 and prior['failures'], 'prior Actions compile failure retained')
    return results, reuse, local


def record(mode):
    os.chdir(ROOT); d.current(); OUT.mkdir(parents=True, exist_ok=True)
    results, reuse, local = verify()
    tracked = d.git('ls-files').decode().splitlines()
    need(not [p for p in tracked if p.endswith('/AGENTS.md') and p.split('/')[0] in ('scripts','tools','tests','content','docs','design')], 'no unseen nested rules')
    prior_cp = d.read(CP)
    terminal = None
    if mode == 'confirm':
        need(prior_cp.get('native_acceptance') and not prior_cp.get('actions_completion_confirmed'), 'one pending checkpoint only')
        terminal = d.inputs.api('actions/runs/' + str(prior_cp['record_run_id']))
        need(terminal['status'] == 'completed' and terminal['conclusion'] == 'success'
             and terminal['head_sha'] == prior_cp['record_source_head'], 'record terminal success at bound source')
    else:
        need(mode == 'publish' and not prior_cp.get('native_acceptance'), 'publish once, never replay accepted cases')
    known_runs = {}
    for run_id in (36273404788, 36273917599, 36274537780):
        run = d.inputs.api('actions/runs/' + str(run_id))
        need(run['status'] == 'completed' and run['conclusion'] == 'success', 'source/preflight record terminal, distinct from native acceptance')
        known_runs[str(run_id)] = d.run_summary(run)
    runs = d.inputs.api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=20')['workflow_runs']
    current = dict(known_runs=known_runs, latest=[d.run_summary(r) for r in runs],
                   record_terminal=d.run_summary(terminal) if terminal else None,
                   prior_native_compile_passed=False, all_ci_passed_claimed=False)
    actions_path = BASE + '/actions-' + str(os.environ['GITHUB_RUN_ID']) + '.json'
    d.write(actions_path, current)
    d.write(BASE + '/fishing-reuse.json', reuse)
    status = 'PASS_FISHING_ECOLOGY_REAL_EARNING_SCOPED'
    predecessor = d.read(MINING)
    proof_files = set(d.read(BASE + '/input-manifest.json')) | {BASE + '/input-manifest.json', BASE + '/fishing-reuse.json', actions_path}
    sources = set(predecessor['source_bindings']) | {C, CAPTURE, MODEL, SELF, TEST, 'scripts/pr16_research_wild.py', WF,
        'overlays/save_migration/save_migration.h', 'overlays/reward_encounters_v2/reward_encounters_v2.c',
        'overlays/reward_encounters_v2/reward_encounters_v2.h', 'overlays/qol_production/qol_production_hooks.S',
        'overlays/wild_overlay/wild_overlay.c', 'tools/mgba_reward_encounters_v2_smoke.c', 'tools/mgba_stage61_progression_lifecycle_e2e.c'}
    cp = dict(schema_version=1, task=TASK, status=status, candidate=oracle.CANDIDATE,
              source_head=os.environ['GITHUB_SHA'], accepted_cases=list(oracle.METHODS), native_acceptance=True,
              actions_completion_confirmed=mode == 'confirm', record_run_id=int(os.environ['GITHUB_RUN_ID']),
              record_source_head=os.environ['GITHUB_SHA'], previous_record_run_id=prior_cp.get('record_run_id'),
              original_actions_failure=local['prior_actions_failure'], development=BASE+'/development.json',
              evidence=BASE+'/input-manifest.json', unit=BASE+'/unit.json', visual=BASE+'/visual-review.json',
              actions=actions_path, results=results, counts=dict(local['counts'], new_scoped_tests=65,
              successful_native_processes=2, failed_native_processes=2, interrupted_native_processes=1),
              source_bindings=d.bindings(sources), protected_bindings=predecessor['protected_bindings'],
              proof_bindings=d.bindings(proof_files), record_execution=dict(native_processes=0,compiles=0,unit_processes=0),
              all_activities_accepted=False,natural_arrival_accepted=False,shop_connection_accepted=False,
              daily_cap_native_accepted=False,duplicate_caught_native_accepted=False,
              all_dialogue_native_display_accepted=False,release_ready=False,active_baseline_changed=False,
              remaining_activities=['GAME_CORNER'])
    d.write(CP, cp)
    goal = '釣り0→4RP/生態0→10RPの実稼得・逃走無加算・T24 typed credit併存・取引だけのfresh Continueを限定受入。次はGAME_CORNERの実配当→3RP、通常進行の受付/ショップ接続、残るnative文言。写真/虫取り/採掘/釣り/生態/BP/P08の無変更native再実行は禁止。日内上限・既捕獲種の実経路をこの2caseだけで全受入したと主張しない。'
    guide = f'''# PR16 釣り・生態調査の実RP稼得\n\n{status}\n\n## 実装・限定受入\n\n候補26dac23c/33554432bytesは不変。研究用の新runner・独立oracle・65検査を実装。釣りは港map3/38 (94,10)で通常BagからSuper Rodを使い、未捕獲種から逃走後、別の実遭遇をMaster Ballで捕獲。生態はmap3/63 (14,11)の通常BagからレーダーHIDDENを選び、逃走後の再使用でも前回のカーソル位置4を読み、不要なDOWNを送らず捕獲へ進む。敵/PID/RNG/捕獲結果/RPはhost注入しない。\n\nRPは0→4/0→10、各daily/lifetimeとnext transactionを全64byte ownerで確認。逃走で台帳/手持ち/Bag/Flash/counterは不変。捕獲では1体増加しMaster Ballが20→19、他の全Bag項目と5party枠は不変。取引自身の保存後に新coreで通常Continueし、2KiB台帳・全party600byte・全Bag・全Flash・counter5を保持。手動Saveは0。開始map/進行/道具/leadはfixtureであり自然到達の証明ではない。\n\nT24 RewardEncountersV2のtyped credit保存1回がT23研究のphase1/phase2保存2回に先行する。generation+1・factory.transaction_id+1・釣りHABITAT credit0又は生態RANDOM credit3の+1を別所有者の正規差分として厳密に検査し、研究外ledger全域を無条件除外しない。\n\n## 原本・失敗・再利用\n\n`{BASE}/development.json` にlocal native5回（成功2/失敗2/外側tool打切り1）とstrict host compile4回を保存。先行Actions36273917599は定義不足でcompile1失敗/native0のまま保持。合計host compile5、ARM0、既受入native再実行0。初回釣り失敗はT24差分を省いた検証側の過剰制約。生態失敗は保持カーソルを無視した入力側不具合。打切り原stdoutは未回収でありPASSへ昇格しない。\n\n成功釣りlocal#2・生態local#5のstdoutはbyte不変で公開。10PPMを目視し、成功原本のhashと一致。65新検査は全行欠落/重複・owner128変異・型・捕獲個体・保存分担・画像・過大主張などを拒否。独立oracleは全ledger4状態×2活動を再構成する。記録時unit/native/compileを再実行せずsource拘束済み原本を再利用。\n\n釣り成功後の変更はecology専用の到達不能分岐とローカル初期化だけ。`ecology-only-source.diff.txt` と `fishing-reuse.json` でfishing側の全到達コードが不変と照合したため、釣りは再実行しない。\n\n## Actionsと再開\n\nActions記録終端確認: {cp['actions_completion_confirmed']}。`record_run_id` は今回記録runであり実行中に自己successとは記録しない。確認済み前回runは `{actions_path}`。一般CIの既存失敗/保留と限定native PASSを分離する。\n\n{goal}\n'''
    Path(GUIDE).write_text(guide)
    state = d.read(d.STATE)
    state['research_wild'] = {k: cp[k] for k in ('status','candidate','accepted_cases','native_acceptance','actions_completion_confirmed','record_run_id','record_source_head','counts')}
    state['research_wild'].update(path=CP,guide=GUIDE,evidence=BASE+'/input-manifest.json')
    state['research_remaining']['status'] = 'FISHING_ECOLOGY_ACCEPTED_GAME_CORNER_OPEN'
    state['bp']['current_stop'] = status; state['bp']['next_step'] = goal
    state['next_action'] = dict(state['next_action'], id='RESEARCH_GAME_CORNER_AND_NATURAL_CONNECTION_NEXT',goal_ja=goal,
        read_paths=[GUIDE,CP,'content/research_economy_v1/canonical_model.json','overlays/research_economy_v1/research_economy_v1.c','docs/PR16_RESEARCH_CATALOG_JA.md'])
    state['observed_head'] = os.environ['GITHUB_SHA'];state['observed_head_semantics']='釣り/生態の新規ローカル実測を独立oracle/原本hash/65検査で記録するsource。Actions終端は専用項目で別管理。'
    state['observed_head_checks'] = dict(scope_head=os.environ['GITHUB_SHA'],runs=current['latest'],reconciliation=actions_path,reason_ja='専用実測成功/過去compile failure/一般CI/自己記録終端を区別。')
    state['pending_runs'] = [dict(run_id=r['id'],tested_head=r['head_sha'],status=r['status']) for r in runs if r['status'] in ('queued','in_progress')]
    for path in sources | proof_files | {CP,GUIDE,TRANSPORT,SELF}:
        state['source_bindings'][path] = identity(Path(path).read_bytes())
    note = '釣りlocal#2/生態local#5、候補26dac23cの実稼得4/10RP・逃走・取引保存だけのfresh Continueを限定受入。T24 typed credit1save+T23研究2save、全ledger/Bag/party/Flash、65新検査・10画像。無変更native/旧unit再実行禁止。ゲームコーナー/自然到達/受付接続/未確認native文言は未完。'
    if note not in state['do_not_repeat']: state['do_not_repeat'].insert(0,note)
    stamp = datetime.datetime.now(datetime.timezone.utc).isoformat()
    state['observed_date_jst'] = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=9))).date().isoformat();state['logs_synchronized']=True
    publish_resume(state)
    log = f'\n## {stamp}\n- Timestamp: {stamp}\n- Task: {TASK} / 釣り・生態実稼得の限定受入（{mode}）\n- Version: research-wild-v2\n- Status: DONE（2活動の実稼得/逃走/取引Continue限定）\n- Summary: {goal}\n- Files changed: 専用C/generator/oracle/65検査/記録器、完全stdoutと失敗履歴/画像hash/source差分/checkpoint、引継ぎMD/JSON、両ログ。\n- Verify: local native5=成功2+失敗2+打切り1、host compile4+先行Actions失敗1、ARM0、受入済みnative再実行0。65新検査PASSをsource拘束で再利用。ledger4状態×2を独立再構成、10画像目視・全hash一致。record native/compile/unit再実行0。resume/task graph/最終index scoped guardはcommit前必須。\n- Commit: source={os.environ["GITHUB_SHA"]}; record run={os.environ["GITHUB_RUN_ID"]}; 自己SHAはgit log参照。同branch非force push。\n- Network: GitHub HEAD/PR/Actions・固定artifactのみ。候補/seed/受入済みsource/evidence/baseline不変。merge/releaseなし。全CI成功は主張しない。\n'
    for path in d.LOGS:
        with Path(path).open('a') as stream: stream.write(log)
    owned = proof_files | {CP,GUIDE,d.STATE,d.DOC,SELF,MODEL,TEST,C,CAPTURE,'scripts/pr16_research_wild.py'} | d.LOGS
    # The generator existed before START, so only actually changed paths belong
    # to the exact task diff; immutable inherited inputs are not staged again.
    for path in sorted(owned):
        need(Path(path).is_file(), 'owned path exists')
    subprocess.run(['git','add','--',*sorted(owned)],check=True)
    changed = set(d.git('diff','--cached','--name-only',START).decode().splitlines())
    need(changed <= owned | CODE, 'explicit complete task file set')
    d.write(OUT/'owned.json',sorted(changed - CODE))
    print(json.dumps(dict(status=status,mode=mode,accepted=2,record_native_processes=0,record_unit_processes=0,actions_completion_confirmed=cp['actions_completion_confirmed'])))


def guard():
    import pr16_learnset_runtime_record as g
    g.START=START;g.CODE=CODE;g.OWNED=set(d.read(OUT/'owned.json'));g.guard()
    subprocess.run(['git','diff','--cached','--check'],check=True)


if __name__ == '__main__':
    os.chdir(ROOT)
    if sys.argv[1:] == ['guard']: guard()
    elif sys.argv[1:] in (['publish'],['confirm']): record(sys.argv[1])
    else: raise SystemExit('publish | confirm | guard')
