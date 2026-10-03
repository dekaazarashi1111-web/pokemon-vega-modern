#!/usr/bin/env python3
"""初勝利・単体交換・次戦の原本を再照合して保存。新規emulator/ROM生成はしない。"""
from __future__ import annotations
import datetime
import hashlib
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'scripts'), str(ROOT)]
import pr16_resume as resume
import pr16_bp_win_exchange as native
import pr16_bp_selection_native as launch
TASK = 'USER-20260913-BP-WIN-EXCHANGE'
REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
BRANCH = 'codex/modernization-followup-20260908'
ENTRY = '86113af36642e9a8b91f5eafff8e148c50133328'
TESTED = '0464cecea12377e7a85bbad8fa1957eec00d5fe8'
SELF = 'scripts/pr16_bp_win_exchange_record.py'
TEST = 'tests/test_pr16_bp_win_exchange_record.py'
WORKFLOW = '.github/workflows/pr16-bp-win-exchange-record.yml'
NAV = 'tests/test_pr16_bp_exchange_navigation.py'
VERIFIED = 'content/modernization/pr16_bp_win_exchange_verified.json'
EVIDENCE = 'content/modernization/pr16_bp_win_exchange_evidence'
OUT = ROOT/'.local/pr16-bp-win-exchange-record'
LOGS = ('design/run_log.md', 'design/version_log.md')
BOUNDS = [
    dict(run=34767145222, job=103750027063, head=ENTRY, artifact=10320823231, size=834399,
         sha256='a647a450737533843246d1873ba599809346ea6c8aaa0bf68e5e0a8bdf0f2b3c', conclusion='failure',
         stop='single selection did not reach Confirm'),
    dict(run=34769665360, job=103756823515, head='a7d6d7ff4df815cf20d1345dc2704e707679a1c9', artifact=10321641761, size=841743,
         sha256='85dbdfdd4d97b1e4a61d5b61a588005d240fa7ec0999d79d3747e0801613ec18', conclusion='failure',
         stop='exchange exact600 compare (selected healed100 + unchanged500) failed'),
    dict(run=34770280751, job=103758504094, head=TESTED, artifact=10322016905, size=848217,
         sha256='4dc8e0e11d77faf9eeff67075252488e6d8dab9ca4e9259000880fc9ada09a18', conclusion='success', stop=None),
]
CASE = native.CASE
COPIES = ('stderr', 'process.json', 'runner-result.json', 'receipt.json')
SAVED = tuple(f'{EVIDENCE}/{b["run"]}.{x if x.endswith("json") else x+".txt"}' for b in BOUNDS for x in COPIES)
RESULT = EVIDENCE+'/native-result.json'
ACTIONS = EVIDENCE+'/actions.json'
UNITS = EVIDENCE+'/native-unit-tests.txt'
WRITES = (*SAVED, RESULT, ACTIONS, UNITS, VERIFIED, resume.STATE, resume.DOC, resume.BACKLOG, *LOGS)


def need(ok, message):
    if not ok:
        raise ValueError(message)


def ident(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def stable(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()


def git(*args, **kwargs):
    return subprocess.check_output(['git', *args], cwd=ROOT, **kwargs)


def api(path):
    return json.loads(subprocess.check_output(['gh', 'api', 'repos/'+REPO+'/'+path], cwd=ROOT))


def current_head():
    return api('git/ref/heads/'+BRANCH)['object']['sha']


def safe_zip(raw):
    need(len(raw) < 4000000, 'archive size bound')
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        need(0 < len(names) <= 200 and len(names) == len(set(names)), 'duplicate/empty archive')
        need(sum(x.file_size for x in z.infolist()) < 30000000, 'expanded archive bound')
        for x in z.infolist():
            p = Path(x.filename)
            need(not p.is_absolute() and '..' not in p.parts and '\\' not in x.filename
                 and not x.is_dir() and x.file_size < 4000000
                 and (x.external_attr >> 16) & 0o170000 != 0o120000, 'unsafe archive member')
        return {n: z.read(n) for n in names}


def checked_process(p, code):
    need(type(p['returncode']) is int and p['returncode'] == code
         and p['timed_out'] is False and p['spawn_error'] is None, 'native process boundary')


def bundle(raw, bound):
    need(ident(raw) == {k: bound[k] for k in ('size', 'sha256')}, 'pinned archive identity')
    outer = safe_zip(raw)
    prefix = 'pr16-bp-win-exchange/'
    data = {p[len(prefix):]: b for p, b in outer.items() if p.startswith(prefix)}
    receipt = json.loads(data['receipt.json'])
    need(receipt['tested_head'] == bound['head'], 'receipt source HEAD')
    need(set(receipt['members']) == set(data)-{'receipt.json'}, 'receipt coverage')
    for p, meta in receipt['members'].items():
        need(ident(data[p]) == meta, 'receipt member: '+p)
    report = json.loads(data['result.json'])
    need(report['candidate'] == dict(size=33554432, sha256=native.SHA), 'native candidate')
    sources, generated = safe_zip(data['sources.zip']), safe_zip(data['generated-controller.zip'])
    for key, members in (('sources', sources), ('generated', generated)):
        need(set(report[key]) == set(members), key+' scope')
        for p, b in members.items():
            need(ident(b) == report[key][p] and b'\0' not in b, key+' identity')
            b.decode('utf-8')
    need(report['guard_checks'] == ['bus8','bus16','bus32','raw8','raw16','raw32','register'], 'seven barriers')
    for key in report['guard_checks']:
        checked_process(json.loads(data[f'guard-{key}.process.json']), 1)
        need(data[f'guard-{key}.stderr'] == b'P03 archive: host write after observation barrier\n'
             and not data[f'guard-{key}.stdout'], 'write rejection witness')
    process = json.loads(data[CASE+'.process.json'])
    checked_process(process, 0 if bound['conclusion'] == 'success' else 1)
    if bound['conclusion'] == 'success':
        need(report['status'] == native.STATUS and report['failures'] == []
             and report['actual_new_processes'] == report['successful_fresh_cores'] == 1, 'native run success')
        old = launch.SHA
        try:
            launch.SHA = native.SHA
            row = native.validate(data[CASE+'.stdout'], data[CASE+'.stderr'], 0)
        finally:
            launch.SHA = old
        need(report['results'] == [dict(result=row, process=process)], 'native stdout/result agreement')
        need(generated['controller.c'] == native.assemble_controller().encode(), 'assembled C differs')
        unit = outer['pr16-bp-win-exchange-run/unit.stderr']
        need(re.search(rb'Ran 14 tests in [0-9.]+s\s+OK\s*$', unit) is not None, 'fourteen source tests')
    else:
        need(report['status'] == 'FAIL' and report['failures'] and not data[CASE+'.stdout'], 'original failure retained')
        need(data[CASE+'.stderr'].endswith(('P03 archive: '+bound['stop']+'\n').encode()), 'original failure boundary')
        row = None
    return dict(data=data, outer=outer, report=report, receipt=receipt, row=row, sources=sources)


def small(r):
    return {k: r[k] for k in ('id','name','head_sha','path','status','conclusion','event')}


def write_text(name, raw):
    need(name in WRITES and b'\0' not in raw and (len(raw) < 4000000 or name in LOGS and len(raw) <= (ROOT/name).stat().st_size+12000), 'write scope/text bound')
    raw.decode('utf-8')
    p = resume.safe_path(ROOT, name)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(raw)


def record():
    need(os.environ.get('GITHUB_REPOSITORY') == REPO and os.environ.get('GITHUB_REF') == 'refs/heads/'+BRANCH, 'repository/branch')
    head = git('rev-parse', 'HEAD', text=True).strip()
    need(head == os.environ['GITHUB_SHA'] == current_head(), 'concurrent HEAD')
    need(not git('status','--porcelain','--untracked-files=no'), 'dirty checkout')
    git('merge-base','--is-ancestor',TESTED,head)
    s = resume.validate(ROOT)
    need(s['next_action']['id'] == 'BP_NATIVE_WIN_EXCHANGE_REWARD', 'task already advanced')
    pr = api('pulls/16')
    need(pr['state'] == 'open' and pr['draft'] and not pr['merged'] and pr['head']['sha'] == head, 'PR changed')
    OUT.mkdir(parents=True, exist_ok=True)
    saved, observed, good = {}, [], None
    for b in BOUNDS:
        r = api(f'actions/runs/{b["run"]}')
        need(r['head_sha'] == b['head'] and r['status'] == 'completed' and r['conclusion'] == b['conclusion'], 'Actions source result')
        jobs = api(f'actions/runs/{b["run"]}/jobs')['jobs']
        need(len(jobs) == 1 and jobs[0]['id'] == b['job'] and jobs[0]['conclusion'] == b['conclusion'], 'Actions source job')
        a = api(f'actions/artifacts/{b["artifact"]}')
        need(a['workflow_run']['id'] == b['run'] and a['workflow_run']['head_sha'] == b['head']
             and a['digest'] == 'sha256:'+b['sha256'] and not a['expired'], 'Actions artifact binding')
        raw = subprocess.check_output(['gh','api',f'repos/{REPO}/actions/artifacts/{b["artifact"]}/zip'])
        v = bundle(raw, b)
        for name, content in v['sources'].items():
            need(git('show', b['head']+':'+name) == content, 'source archive vs tested Git tree: '+name)
            if b['conclusion'] == 'success':
                need((ROOT/name).read_bytes() == content, 'tested source changed: '+name)
        observed.append(small(r))
        (OUT/(str(b['run'])+'.zip')).write_bytes(raw)
        for suffix, original in (('stderr',CASE+'.stderr'),('process.json',CASE+'.process.json'),('runner-result.json','result.json'),('receipt.json','receipt.json')):
            name = f'{EVIDENCE}/{b["run"]}.{suffix if suffix.endswith("json") else suffix+".txt"}'
            saved[name] = v['data'][original]
        if b['conclusion'] == 'success':
            good = v
    need(good is not None, 'no completed native result')
    latest = api('actions/workflows/pr16-bp-win-exchange.yml/runs?branch=codex%2Fmodernization-followup-20260908&per_page=1')['workflow_runs'][0]
    need(latest['id'] == BOUNDS[-1]['run'], 'new native run: reconcile first')
    resolved_pending = []
    for pending in s['pending_runs']:
        prior = api(f'actions/runs/{pending["run_id"]}')
        need(prior['head_sha'] == pending['tested_head'] and prior['status'] == 'completed', 'previous writer still pending')
        resolved_pending.append(small(prior))
    head_runs = []
    for sha in (ENTRY, TESTED):
        listing = api(f'actions/runs?head_sha={sha}&per_page=100')
        need(listing['total_count'] == len(listing['workflow_runs']), 'incomplete Actions list')
        head_runs.extend(small(r) for r in listing['workflow_runs'])
    row = good['row']
    need(git('show',ENTRY+':'+native.SOURCE).split(b'/* WX_EXTENSION_BOUNDARY */')[0]
         == (ROOT/native.SOURCE).read_bytes().split(b'/* WX_EXTENSION_BOUNDARY */')[0], 'historical input policy changed')
    saved[RESULT] = good['data'][CASE+'.stdout']
    saved[UNITS] = good['outer']['pr16-bp-win-exchange-run/unit.stderr']
    saved[ACTIONS] = stable(dict(source_runs=observed, resolved_pending_runs=resolved_pending, entry_and_tested_head_runs=head_runs,
                                recording_run=int(os.environ['GITHUB_RUN_ID']), recording_source_head=head))
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    visual = {}
    for label in ('battle-outcome','facility-afterbattle','exchange-single-menu','exchange-single-selected','exchange-committed','exchange-next-action'):
        name = CASE+'-'+label+'.ppm'
        visual[label] = dict(member=name, **ident(good['data'][name]))
    decision = ('初勝利→単体order3→通常UP4入力でConfirm→交換確定→次戦struct/actionを観測。'
                '600bytes厳密比較は選択枠の回復済み100bytes＋不変500bytes。元snapshot600、BP0、save counter2を保持。'
                '次戦画面はplayerポリゴン/敵ゴースで、交換直後partyと次戦battlerの個体同一性は本runnerのassert対象外。'
                '次手でPrepareBattle前後・chooser・新戦闘のparty/個体をread-only採取して照合し、確定後3勝報酬へ延長する。'
                '画面だけから原因やROM不具合を断定しない。')
    receipt = dict(schema_version=1, classification='DIAGNOSTIC_ONLY_NOT_ACCEPTANCE', task=TASK,
        status=native.STATUS, run_id=BOUNDS[-1]['run'], job_id=BOUNDS[-1]['job'], tested_head=TESTED,
        entry_head=ENTRY, artifacts=BOUNDS, native_result=row,
        candidate=dict(size=33554432,sha256=native.SHA,crc32='0D5D9178'),
        sources=good['report']['sources'], generated=good['report']['generated'],
        evidence_files={p:ident(raw) for p,raw in saved.items()}, visual_review=visual,
        visual_review_method='6 original PPM screens rendered and inspected in ChatGPT; no OCR',
        decision_ja=decision, accepted_native_cases_replayed=0, task_new_native_processes=2,
        task_failed_native_processes=1, task_successful_native_processes=1, source_only_record_processes=0,
        native_exchange_observed=True, native_exchange_accepted=False,
        next_battle_exchanged_individual_identity_verified=False,
        native_bp_earning_accepted=False, p05_native_bp_gap_closed=False, release_ready=False,
        rom_changes_this_task=0, active_baseline_changed=False)
    for name, raw in saved.items():
        write_text(name, raw)
    write_text(VERIFIED, stable(receipt))
    candidate = dict(s['candidate'], sha256=native.SHA, size=33554432, crc32='0D5D9178')
    goal = ('7f32の交換直後partyと次戦battlerの個体同一性を、PrepareBattle前後・chooser・戦闘開始のread-only証拠で先に照合する。'
            'native party保持を確定してから未観測の2/3戦目・3勝completion・BP報酬へ延長する。')
    s.update(status=native.STATUS, observed_head=TESTED, candidate=candidate,
        observed_head_semantics='native成功原本の固定source HEAD。現在branch HEADはAPIで再取得し、record commitと混同しない。',
        latest_native_run=BOUNDS[-1]['run'], latest_native_job=BOUNDS[-1]['job'], latest_native_tested_head=TESTED,
        latest_native_evidence=VERIFIED, latest_native_scope='DIAGNOSTIC_ONLY_NOT_ACCEPTANCE',
        latest_native_summary_ja=decision,
        candidate_scope_ja='交換修復済み7f32の今回native診断候補。正式BP受入・最終製品SHAではない。',
        observed_head_checks=dict(reason_ja='native run34770280751はSUCCESS。開始HEAD/実行HEADの全Actionsメタデータは'+ACTIONS+'。失敗2原本はfailureのまま保存。記録workflowの終端はAPIで照合し、Checksとrelease受入を混同しない。'),
        pending_runs=[], logs_synchronized=True, p08_resume_synchronized=True)
    s['bp'].update(current_stop='run34770280751/job103758504094 SUCCESS。'+decision,
        next_step=goal, battle_started=row['battle_started'], bp_earned=row['bp_earned'],
        selected_frame=row['selected_frame'], second_chooser_frame=row['second_chooser_frame'],
        move_id=row['move_id'],pp_before=row['pp_before'],pp_after=row['pp_after'],action_return_frame=row['action_return_frame'],
        native_first_victory_observed=True,native_exchange_observed=True,native_exchange_accepted=False,
        next_battle_started_observed=True,next_battle_exchanged_individual_identity_verified=False,
        after_battle_launch='交換直後600bytesは検証済み。次戦開始後の交換個体同一性を先に検証し、未観測の3勝/報酬・通常Save/fresh Continue・獲得BP消費へ進む。')
    s['next_action'].update(id='BP_NEXT_BATTLE_IDENTITY_AND_REWARD', goal_ja=goal,
        read_paths=[VERIFIED,RESULT,native.SELF,native.SOURCE,NAV,'overlays/facility_runtime/facility_runtime.c',
                    'scripts/pr16_bp_exchange_successor.py','content/modernization/pr16_bp_battle_return_evidence/reward-source-audit.json'],
        success_observations=['read-only party identity across PrepareBattle/chooser/next battle',
                              'native second and third victories and exact BP reward',
                              'ordinary Save/fresh Continue and earned BP spending'],
        stop_rule_ja='初勝利/単体交換/次戦開始の単独再実行はしない。次の新規個体連鎖・3勝ケースへ既存runnerを延長し、今回の成功prefixを再利用する。取消Save/Continue・敗北帰還・P03等は影響なしにつき再実行しない。原失敗、全byte比較、timeout、7barrierを保持する。')
    s['do_not_repeat'].append('run34770280751の単体交換＋次戦開始は診断原本を再利用。次戦個体同一性とBP報酬まで受入済みと読まない。')
    s['win_exchange_completed'] = dict(run_id=BOUNDS[-1]['run'],evidence=VERIFIED,scope='NATIVE_DIAGNOSTIC_NOT_FORMAL_ACCEPTANCE')
    s['recording_workflow'] = dict(run_id=int(os.environ['GITHUB_RUN_ID']), source_head=head,
        status_at_snapshot='in_progress', note_ja='native未完runは0。記録workflowの終端/commitはAPIとartifact result.jsonで照合する。')
    for name in (native.SELF,native.SOURCE,NAV,SELF,TEST,WORKFLOW,VERIFIED,RESULT):
        s['source_bindings'][name] = ident((ROOT/name).read_bytes())
    backlog = resume.load(ROOT,resume.BACKLOG)
    backlog['next_integration_candidate'].update(candidate=dict(size=33554432,sha256=native.SHA,crc32='0D5D9178'),
        scope='NATIVE_WIN_EXCHANGE_NEXT_BATTLE_DIAGNOSTIC_BP_PENDING',
        builder='scripts/pr16_bp_exchange_successor.py',source_path=VERIFIED)
    for item in backlog['remaining_conditions']:
        if item['id'] in ('NATURAL_CAPTURE_GEAR','FINAL_NATIVE_ACCEPTANCE'):
            item['resume'] = 'Current resume: '+resume.DOC+'. '+s['bp']['current_stop']+' Next: '+goal
    write_text(resume.BACKLOG,stable(backlog))
    write_text(resume.STATE,stable(s))
    subprocess.run([sys.executable,'scripts/pr16_resume.py','render'],cwd=ROOT,check=True)
    common = (f'\n\n## {stamp} — {TASK}\n- Version: PR16 native exchange diagnostic\n'
        f'- Task: {TASK} / 初勝利・単体交換・次戦の未完runnerを実装/検証/記録\n- Status: DONE\n'
        '- Summary: 自動Confirm移動の誤前提を通常UP入力へ修正。scratch消去途中ではなくscript復帰境界で600byteを厳密比較。\n'
        f'- Native: run34770280751/job103758504094、HEAD={TESTED}、候補7f32/CRC0D5D9178。'
        '勝利16234f→AfterBattle16457f→交換選択17001f→Confirm17250f→確定17345f→次戦struct17755f→action19169f。500不変+100交換、snapshot600、BP0、save2、警告0。\n'
        '- Scope: '+decision+'\n'
        '- History: run34767145222（開始前）とrun34769665360（今回の途中回復誤検出）はfailure原本のまま保存。WIP入力type tableの1セル転記差分も開始HEADへ復元し、最終native sourceと生成Cを完全照合。\n'
        '- Replay: 今回native主process2（失敗1/成功1）、各7拒否guard。受入済みcase再実行0。ROM変更0。記録工程emulator0。\n'
        '- Files changed: tools/mgba_pr16_bp_win_exchange.c、navigation/record tests、record script/workflow、verified/evidence、固定resume MD/JSON、P08診断候補、両ログ。\n'
        '- Verify: 原本14 source tests PASS。記録工程でnavigation4/record8/resume18 tests、原本receipt/source/生成C/7拒否証拠、task graph、diff checkを検証。標準private guardの既存違反はbaseline/index比較で別記し全体PASSと主張しない。\n'
        f'- Commit: この記録を含むcommit。記録入力HEAD={head}。非force push後のhashはworkflow result.jsonとremoteから照合。\n'
        '- Network: GitHub connectorでbranch/PR/Actions/artifact照合、Actionsでpinned candidate再生成。記録はActions API原本取得のみ。private入力/ROM/saveの追跡・公開なし。上流CFRU-JP e24a16fe include/pokemon.hも読取参照。\n'
        '- Boundary: 正式physical4/P08ゲート2、BP稼得/消費未受入、PR draft/open維持、merge/release/baseline変更0。\n')
    for name in LOGS:
        old = (ROOT/name).read_text()
        need(TASK not in old, 'task already recorded')
        write_text(name,(old+common).encode())
    check()


def check():
    receipt = resume.load(ROOT,VERIFIED)
    need(receipt['classification'] == 'DIAGNOSTIC_ONLY_NOT_ACCEPTANCE' and receipt['tested_head'] == TESTED, 'saved identity')
    for key in ('native_exchange_accepted','native_bp_earning_accepted','p05_native_bp_gap_closed','release_ready','next_battle_exchanged_individual_identity_verified'):
        need(receipt[key] is False, 'acceptance inflated')
    for name, meta in receipt['evidence_files'].items():
        need(ident((ROOT/name).read_bytes()) == meta, 'saved evidence: '+name)
    for name, meta in receipt['sources'].items():
        need(ident((ROOT/name).read_bytes()) == meta, 'saved native source: '+name)
    need(resume.load(ROOT,RESULT) == receipt['native_result'], 'saved raw native result')
    old = launch.SHA
    try:
        launch.SHA = native.SHA
        checked = native.validate((ROOT/RESULT).read_bytes(), (ROOT/f'{EVIDENCE}/{BOUNDS[-1]["run"]}.stderr.txt').read_bytes(), 0)
    finally:
        launch.SHA = old
    need(checked == receipt['native_result'] and receipt['run_id'] == BOUNDS[-1]['run']
         and receipt['job_id'] == BOUNDS[-1]['job'], 'saved validation/run identity')
    s = resume.validate(ROOT)
    need(s['next_action']['id'] == 'BP_NEXT_BATTLE_IDENTITY_AND_REWARD', 'next action')
    need(len(s['remaining_physical_gap_ids']) == 4 and len(s['remaining_p08_gate_ids']) == 2, 'formal gaps changed')
    return receipt


def publish():
    check()
    head = git('rev-parse','HEAD',text=True).strip()
    need(head == os.environ['GITHUB_SHA'] == current_head(), 'concurrent HEAD before stage')
    actual = set(git('diff','--name-only',text=True).splitlines()) | set(git('ls-files','--others','--exclude-standard',text=True).splitlines())
    need(actual == set(WRITES), 'changed/untracked scope')
    for name in LOGS:
        need((ROOT/name).read_bytes().startswith(git('show',head+':'+name)), 'append-only log')
    git('add','--',*WRITES)
    need(set(git('diff','--cached','--name-only',text=True).splitlines()) == set(WRITES), 'staged scope')
    git('diff','--cached','--check')
    with tempfile.TemporaryDirectory() as tmp:
        env = dict(os.environ,GIT_INDEX_FILE=str(Path(tmp)/'baseline.index'))
        git('read-tree',ENTRY,env=env)
        old = subprocess.run([sys.executable,'scripts/guard_private_files.py'],cwd=ROOT,env=env,capture_output=True)
    final = subprocess.run([sys.executable,'scripts/guard_private_files.py'],cwd=ROOT,capture_output=True)
    need(old.returncode in (0,1) and not old.stderr and final.returncode == old.returncode
         and final.stdout == old.stdout and not final.stderr, 'new global guard violations')
    import guard_private_files as guard
    for name in git('diff','--name-only',ENTRY,'--',text=True).splitlines():
        p=ROOT/name;raw=p.read_bytes();raw.decode('utf-8')
        need(not p.is_symlink() and b'\0' not in raw and p.suffix.lower() not in guard.BLOCKED_SUFFIXES, 'nontext/private suffix')
        need(not any(name==x or name.startswith(x+'/') for x in guard.BLOCKED_PARTS), 'private input change')
        need(not re.search(rb'gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',raw), 'credential-like content')
        if p.suffix.lower() in guard.DOCUMENT_SUFFIXES:
            before=subprocess.run(['git','show',ENTRY+':'+name],cwd=ROOT,capture_output=True)
            need(guard.document_user_path_lines(raw)==guard.document_user_path_lines(before.stdout if before.returncode==0 else b''), 'new machine path')
    boundary=dict(baseline_head=ENTRY,input_head=head,baseline_returncode=old.returncode,final_returncode=final.returncode,
                  stdout=ident(final.stdout),new_violations=0,whole_guard_passed=final.returncode==0)
    (OUT/'guard-boundary.json').write_bytes(stable(boundary))
    content={p:ident((ROOT/p).read_bytes()) for p in WRITES}
    need(current_head()==head,'concurrent HEAD before commit')
    git('config','user.name','github-actions[bot]')
    git('config','user.email','41898282+github-actions[bot]@users.noreply.github.com')
    git('commit','-m',TASK+': 初勝利・単体交換・次戦の検証完了を固定引継ぎと両ログへ記録')
    new=git('rev-parse','HEAD',text=True).strip()
    need(git('rev-parse','HEAD^',text=True).strip()==head,'commit parent')
    for name,meta in content.items():
        need(ident(git('show',new+':'+name))==meta,'committed blob readback')
    need(current_head()==head,'concurrent HEAD before push')
    git('push','origin','HEAD:refs/heads/'+BRANCH)
    need(current_head()==new and not git('status','--porcelain','--untracked-files=no'),'remote/clean readback')
    (OUT/'result.json').write_bytes(stable(dict(status='PASS_RECORDED_COMMITTED_NONFORCE_PUSHED',task=TASK,
        parent=head,commit=new,branch=BRANCH,native_run=BOUNDS[-1]['run'],native_job=BOUNDS[-1]['job'],
        recording_run=int(os.environ['GITHUB_RUN_ID']),guard=boundary,files=content,
        native_source_tests_reused=14,new_navigation_tests=4,new_record_tests=8,resume_tests=18,
        new_emulator_processes=0,accepted_native_cases_replayed=0,release_ready=False)))
    print('RESULT=DONE TASK='+TASK+' VERIFY=PASS COMMIT='+new)


if __name__ == '__main__':
    need(len(sys.argv)==2 and sys.argv[1] in ('record','check','publish'), 'explicit record/check/publish required')
    globals()[sys.argv[1]]()
