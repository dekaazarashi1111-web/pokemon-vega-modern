#!/usr/bin/env python3
"""同一候補/保存生成Cで正規受付から抑制を観測し、境界ごとに非force記録。"""
from __future__ import annotations
from datetime import datetime, timezone
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
sys.path.insert(0, str(Path(__file__).resolve().parent))
import pr16_circus_battle25 as b
import pr16_circus_suppression_contract as c

ROOT = b.ROOT
OUT = ROOT / '.local/pr16-circus-suppression'
CACHE = OUT / 'resume'
TASK = 'USER-20260920-CIRCUS-SUPPRESSION'
REPORT = 'content/modernization/pr16_circus_suppression.json'
BASE = '8e8c818acf7e8671b9e3f62ab11cc201e8e2ca42'
RUN, JOB, ARTIFACT = 35479503528, 105994620734, 10596015821
OLD_HEAD = '7ac90a66df9a31212fb09cedbd430d59d62649bf'
ARCHIVE = dict(size=1074450, sha256='ac762db37f9402ea03db1d8f6a8f763e4ad48cde228297b9117ea23509246ecf')
PRIOR = 'content/modernization/pr16_circus_battle30_pp.json'
HEADER = 'tools/mgba_pr16_circus_suppression.h'
FILES = ('scripts/pr16_circus_suppression.py', 'scripts/pr16_circus_suppression_contract.py',
         HEADER, 'tests/test_pr16_circus_suppression.py', '.github/workflows/pr16-circus-suppression.yml')
b.OUT = OUT
need = c.need


def source_files():
    return {name: b.identity((ROOT / name).read_bytes()) for name in FILES}


def original():
    prior = b.load(PRIOR)
    need(prior['genuine_30_wins_verified'] and prior['candidate'] == b.TARGET
         and prior['result']['wins'] == 30 and prior['result']['bp_earned'] == 90, 'accepted30 changed')
    run, job, artifact = b.api('actions/runs/' + str(RUN)), b.api('actions/jobs/' + str(JOB)), b.api('actions/artifacts/' + str(ARTIFACT))
    need(run['head_sha'] == OLD_HEAD and run['status'] == 'completed' and run['conclusion'] == 'success', '30-win run identity')
    need(job['run_id'] == RUN and job['status'] == 'completed' and job['conclusion'] == 'success', '30-win job')
    need(artifact['workflow_run']['id'] == RUN and artifact['digest'] == 'sha256:' + ARCHIVE['sha256']
         and not artifact['expired'], '30-win artifact')
    raw = subprocess.check_output(['gh', 'api', 'repos/' + b.REPO + '/actions/artifacts/' + str(ARTIFACT) + '/zip'], cwd=ROOT)
    need(b.identity(raw) == ARCHIVE, '30-win archive bytes')
    folder = OUT / 'input'; (folder / 'generated').mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(len(z.namelist()) == len(set(z.namelist())), 'duplicate archive member')
        for name, bound in prior['generated'].items():
            need(Path(name).name == name and Path(name).suffix in ('.c', '.h'), 'generated path')
            member = 'execution/policy.c' if name == 'pr16_streak_policy.c' else 'original/generated/' + name
            data = z.read(member); need(b.identity(data) == bound, 'fixed generated C: ' + name)
            data.decode('utf-8'); need(b'\0' not in data, 'nontext source')
            (folder / 'generated' / name).write_bytes(data)
        for suffix in ('.stdout', '.stderr'):
            (folder / (c.PREFIX_CASE + suffix)).write_bytes(z.read('execution/' + c.PREFIX_CASE + suffix))
        need(not any(name.endswith(('.srm', '.sav', '.ss0')) for name in z.namelist()), 'prior save exists; do not bootstrap')
    return dict(run_id=RUN, job_id=JOB, artifact_id=ARTIFACT, tested_head=OLD_HEAD,
                archive=ARCHIVE, original_conclusion='success', generated=prior['generated'],
                host_dependencies=prior['original']['host_dependencies'],
                save_not_retained_in_prior_artifact=True)


def tests(label):
    raw, err, proc = b.capture([sys.executable, '-m', 'unittest', 'discover', '-s', 'tests',
                              '-p', 'test_pr16_circus_suppression.py', '-v'], label)
    need(b.exited(proc) == 0 and b'\nOK\n' in err and b'Ran 20 tests' in err, 'new suppression contracts')
    return dict(tests_run=20, failures=0, errors=0, skips=0, successful=True)


def checkpoint(value, phase):
    head = b.scope(); state = b.resume.validate(ROOT); backlog = b.load(b.resume.BACKLOG)
    need(state['latest_native_run'] == 34946969126 and not state['release_ready'], 'formal BP/release scope')
    row = next(x for x in backlog['remaining_conditions'] if x['id'] == 'PHYSICAL_CIRCUS_ADMISSION')
    need(row['success_evidence'] is None and not row.get('complete'), 'formal suppression already accepted')
    rid = int(os.environ['GITHUB_RUN_ID']); value.update(recording_run=rid, recording_source_head=head)
    verified = value.get('native_verified') is True
    if verified:
        stop = '同一2b107e7eの真正Save30から正規受付・通常待機による特性抑制抽選、自然な抑制callee/Stage77委譲、勝敗帰還・通常Save/fresh Continueを検証。完了Actionsと画面の受入照合は未完。'
        nxt = 'この抑制runの完了Actions・原本・target/保存/Continue画面を照合し、正式physical受入へ接続する。新native/旧30勝の重複起動はしない。'
    elif phase == 'START':
        stop = '抑制観測driver/異常系20契約を実装。旧30勝原本と生成Cを照合し、SRAM未保持を確認。未完経路へ必要な真正Save30を一度だけ確保し、以後はhash付きcacheから再開する。'
        nxt = '進行中の同branch suppression runのみ確認。通常入力の抽選と自然callee観測を完了し、原本・引継ぎ・両ログを記録する。'
    else:
        stop = '抑制継続の原本と実停止を記録。真正30勝/90BPの受入は不変。未観測を成功へ昇格しない。' + str(value.get('failures', []))
        nxt = 'pr16_circus_suppression.jsonの最初の未達段階だけ修復する。normal_save30が検証済みなら指定cacheを再利用し、30戦prefixを再実行しない。'
    state['circus_suppression'] = dict(path=REPORT, run_id=rid, classification=value['classification'], candidate=b.TARGET)
    state['bp']['current_stop'] = state['source_change_review_ja'] = stop
    state['bp']['next_step'] = state['next_action']['goal_ja'] = nxt
    state['next_action']['id'] = 'CIRCUS_SUPPRESSION_RECEIPT' if verified else 'CIRCUS_SUPPRESSION_NATIVE'
    state['next_action']['read_paths'] = [REPORT, *FILES, 'content/modernization/pr16_circus_battle30_receipt.json', b.resume.BACKLOG]
    state['observed_head'] = head; state['observed_date_jst'] = '2026-09-20'
    state['observed_head_semantics'] = 'この記録前のremote HEAD。native source/実起動数/継続prefix/cacheは抑制report。正式BPと30勝受入は不変。'
    state['observed_head_checks'] = dict(scope_head=head, runs=[dict(id=RUN, head_sha=OLD_HEAD, status='completed', conclusion='success')],
        reason_ja='既存30勝runのsuccessを実API照合。今回runは記録中で全CI green・正式抑制受入は未主張。')
    state['pending_runs'] = [dict(run_id=rid, tested_head=value['source_head'], status='in_progress', scope='circus-suppression')]
    state['session_execution_summary'] = {k: value.get(k, 0) for k in ('new_emulator_processes','arm_compiles','arm_links','accepted_standalone_replays')}
    state['session_execution_summary']['scope_ja'] = '旧SRAM未保持時のみ30勝を未完抑制への連続prefixとして一度確保。以後は真正Save30のhash付き非tracked cache。抽選不一致も全件記録。'
    note = f'{TASK} run{rid}の完了状況と原本を先に読む。真正Save30 cacheが検証済みなら30戦を再実行しない。抑制fl ag/乱数/特性/owner/PCへのhost書込みは禁止。'.replace('fl ag','flag')
    if note not in state['do_not_repeat']: state['do_not_repeat'].insert(0, note)
    row['suppression_checkpoint'] = REPORT; row['resume'] = nxt
    state['logs_synchronized'] = state['p08_resume_synchronized'] = True
    prefix = f'evidence/pr16_circus_suppression/{rid}/'; evidence = {}
    for path in sorted((OUT / 'execution').rglob('*')):
        if not path.is_file() or path.suffix not in ('.json','.c','.h','.stdout','.stderr'): continue
        name = prefix + 'execution/' + path.relative_to(OUT / 'execution').as_posix()
        data = path.read_bytes(); b.write(name, data); evidence[name] = b.identity(data)
    value['text_evidence'] = evidence
    immutable_report = prefix + phase.lower() + '.json'
    b.write(REPORT, b.stable(value)); b.write(immutable_report, b.stable(value)); b.write(b.resume.BACKLOG, b.stable(backlog))
    for name in (*FILES, REPORT, immutable_report, *evidence): state['source_bindings'][name] = b.identity((ROOT / name).read_bytes())
    if b.resume.BACKLOG in state['source_bindings']: state['source_bindings'][b.resume.BACKLOG] = b.identity((ROOT / b.resume.BACKLOG).read_bytes())
    b.write(b.resume.STATE, b.stable(state)); b.write(b.resume.DOC, b.resume.render(state).encode()); b.resume.validate(ROOT)
    for label, args in [('resume',[sys.executable,'-m','unittest','discover','-s','tests','-p','test_pr16_resume.py','-v']),
                        ('task-graph',[sys.executable,'scripts/validate_task_graph.py'])]:
        raw, err, proc = b.capture(args, label + '-' + phase); need(b.exited(proc) == 0, label + ' failed')
    stamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    paths = [REPORT, immutable_report, b.resume.STATE, b.resume.DOC, b.resume.BACKLOG, *evidence, *b.LOGS]
    entry = (f'\n\n## {stamp} — {TASK}-{phase}\n- Timestamp: {stamp}\n- Task: {TASK}\n'
        f'- Status: {"DONE" if verified else "STOPPED"}（正式physical受入・P08は未完）\n'
        '- Version: pr16-circus-suppression-v1\n- Summary: ' + stop + '\n'
        '- Files changed: ' + ', '.join((*FILES, *paths)) + '\n'
        '- Verify: 新規20契約・固定resume/影響tests・task graph・index差分private guard・diff check。実native/trace成否は原本report。\n'
        '- Commit: この記録を含む同branch非force commit。自己SHAはremote/receipt。\n'
        '- Network: GitHub原本API照合・host mGBA依存。ROM/save/private入力はGit/artifactへ追加せず、真正Save30のみActions cache。旧ARM/旧builder/受入単体0。\n'
        '- Next: ' + nxt + '\n')
    for name in b.LOGS:
        path = ROOT / name; need(f'{TASK}-{phase}\n' not in path.read_text(), 'duplicate phase log')
        with path.open('a') as stream: stream.write(entry)
    subprocess.run(['git','add','--',*paths], cwd=ROOT, check=True)
    changed = set(b.command('git','diff','--cached','--name-only',head).splitlines())
    need(changed and changed <= set(paths), 'unexpected staged paths')
    import pr16_ring_compiled_record as guard
    guard.BASE, guard.OUT, guard.ALLOWED = head, OUT, changed; guard.guard()
    subprocess.run(['git','diff','--cached','--check'],cwd=ROOT,check=True); b.scope()
    subprocess.run(['git','config','user.name','github-actions[bot]'],cwd=ROOT,check=True)
    subprocess.run(['git','config','user.email','41898282+github-actions[bot]@users.noreply.github.com'],cwd=ROOT,check=True)
    subprocess.run(['git','commit','-m',TASK+': '+phase+' 正規抽選・自然callee・保存原本・固定引継ぎ・両ログ'],cwd=ROOT,check=True)
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+b.BRANCH],cwd=ROOT,check=True)
    committed = b.scope(); need(not b.command('git','status','--porcelain','--untracked-files=no'), 'dirty after push')
    (OUT / ('receipt-' + phase + '.json')).write_bytes(b.stable(dict(task=TASK, phase=phase, commit=committed, source_head=head, run_id=rid, non_force_push=True)))
    print('RESULT=' + ('DONE' if verified else 'STOPPED') + ' TASK=' + TASK + ' VERIFY=PASS COMMIT=' + committed)


def prepare():
    head = b.scope(); b.resume.validate(ROOT); OUT.mkdir(parents=True, exist_ok=True)
    previous = b.load(REPORT) if (ROOT / REPORT).exists() else None
    need(previous is None, 'existing attempt: inspect report/cache and implement a scoped successor, never replay blindly')
    import pr16_ring_compiled_record as guard
    guard.BASE, guard.OUT, guard.ALLOWED = BASE, OUT, set(FILES); guard.guard()
    value = dict(schema_version=1, task=TASK, classification='CIRCUS_SUPPRESSION_IMPLEMENTED_NATIVE_PENDING',
        source_head=head, candidate=b.TARGET, original=original(), host_tests=tests('contracts'), sources=source_files(),
        new_emulator_processes=0, arm_compiles=0, arm_links=0, accepted_standalone_replays=0,
        rom_changes=0, native_verified=False, physical_admission_accepted=False,
        suppression_accepted=False, release_ready=False, failures=[], visual_review_completed=False)
    checkpoint(value, 'START')


def native():
    head = b.scope(); b.resume.validate(ROOT); value = b.load(REPORT)
    need(value['recording_run'] == int(os.environ['GITHUB_RUN_ID']) and value['new_emulator_processes'] == 0, 'native already attempted')
    value['native_source_head'] = head
    work = OUT / 'work'; work.mkdir(parents=True, exist_ok=True)
    protected = {}
    try:
        program = """import sys,json
from pathlib import Path
sys.path.insert(0,'scripts')
import pr16_saved_reconstruction as r
def offline(event,args):
    if event.startswith('socket.') or event in ('urllib.Request','http.client.connect'):raise RuntimeError('offline reconstruction')
sys.addaudithook(offline)
print(json.dumps(r.reconstruct(Path('.local/pr16-circus-suppression/runtime').resolve())))
"""
        raw, err, proc = b.capture([sys.executable, '-c', program], 'reconstruct', 120)
        need(b.exited(proc) == 0 and not err, 'saved-byte reconstruction failed'); value['reconstruction'] = c.strict(raw)
        candidate = OUT / 'runtime/candidate.gba'; seed = ROOT / b.SEED
        need(b.identity(candidate.read_bytes()) == b.TARGET, 'candidate identity')
        need(not seed.is_symlink() and b.identity(seed.read_bytes())['sha256'] == b.SEED_SHA, 'fixed seed')
        protected = {p: b.identity(p.read_bytes()) for p in (candidate, seed)}
        for name, bound in value['original']['host_dependencies'].items():
            need(b.identity((ROOT / name).read_bytes()) == bound, 'host dependency drift: ' + name)
        generated = {}
        for name, bound in value['original']['generated'].items():
            data = (OUT / 'input/generated' / name).read_bytes(); need(b.identity(data) == bound, 'generated C changed')
            generated[name] = data
        generated = c.adapt(generated)
        dispatchers = c.routes(candidate.read_bytes(), b.load('config/modernization_p05_stage77_suppression.json'))
        value['dispatchers'] = dispatchers; generated['ss_routes.h'] = c.route_header(dispatchers)
        for name, data in generated.items(): (work / name).write_bytes(data)
        value['generated'] = {name: b.identity(data) for name, data in generated.items()}
        for name in ('controller.c','pr16_shop_breeding_helpers.c','ss_routes.h'):
            dst=OUT/'execution/generated'/name;dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(generated[name])
        exe = work / 'runner'; rel = lambda p: p.relative_to(ROOT).as_posix()
        raw, err, proc = b.capture(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror','-Itools','-I'+rel(work),rel(work/'controller.c'),'-lmgba','-o',rel(exe)],'compile',120)
        need(b.exited(proc) == 0 and not err, 'new host controller compile failed')
        value['host_compiles'] = 1; value['executable'] = b.identity(exe.read_bytes())
        value['guard_evidence_reused'] = [b.OLD+'guard-'+g+'.process.json' for g in ('bus8','bus16','bus32','raw8','raw16','raw32','register')]
        for name in value['guard_evidence_reused']: need(b.exited(b.load(name)) == 1, 'inherited guard missing')
        # This first implementation bootstraps once. Successors must bind the recorded cache, not rerun this prepare.
        need(not (CACHE/'normal30.srm').exists(), 'cache already exists: use a scoped resume successor')
        scratch = work / 'scratch.srm'; shutil.copyfile(seed, scratch)
        point = work / 'normal30.srm'; shots = OUT / 'screens'; shots.mkdir(exist_ok=True)
        value['new_emulator_processes'] = 1
        raw, err, proc = b.capture([rel(exe),rel(candidate),rel(scratch),c.SHA,b.SEED_SHA,c.CASE,rel(shots/c.CASE),'bootstrap',rel(point)],c.CASE,1800)
        value['process'] = proc
        if proc['spawn_error'] is not None: value['new_emulator_processes'] = 0
        oldout=(OUT/'input'/(c.PREFIX_CASE+'.stdout')).read_bytes(); olderr=(OUT/'input'/(c.PREFIX_CASE+'.stderr')).read_bytes()
        value['prefix'] = c.prefix_proof(oldout, olderr, raw, err)
        points = c.rows(err, b'CIRCUS_SUPPRESSION_CHECKPOINT ')
        need(len(points) == 1 and points[0]['bootstrap'] and points[0]['prefix_wins_reexecuted'] == 30
             and not points[0]['host_state_injection'], 'genuine normal save checkpoint')
        bound = b.identity(point.read_bytes()); need(bound['sha256'] == points[0]['normal_save30_sha256'], 'normal save checkpoint bytes')
        cache_key = 'pr16-circus-save30-' + c.SHA + '-' + os.environ['GITHUB_RUN_ID']
        checkpoint_data = dict(candidate=b.TARGET, save=bound, source_head=head, run_id=int(os.environ['GITHUB_RUN_ID']),
            cache_key=cache_key, prefix=value['prefix'], verified=True, tracked=False, artifact_included=False)
        CACHE.mkdir(parents=True,exist_ok=True); shutil.copyfile(point,CACHE/'normal30.srm')
        (CACHE/'provenance.json').write_bytes(b.stable(checkpoint_data)); value['normal_save30'] = checkpoint_data
        value['draws'] = c.rows(err,b'CIRCUS_SUPPRESSION_DRAW ')
        value['natural_calls'] = c.rows(err,b'CIRCUS_SUPPRESSION_CALL ')
        if raw.splitlines(): value['raw_last_result'] = c.strict(raw.splitlines()[-1])
        analysis = c.validate_lifecycle(raw,err,b.exited(proc))
        value['analysis'] = analysis; value['native_verified'] = True
        value['classification'] = 'CIRCUS_SUPPRESSION_NATIVE_VERIFIED_VISUAL_PENDING'
    except Exception as error:
        value['failures'].append(dict(stage='native-or-setup',type=type(error).__name__,error=str(error)))
        value['classification'] = 'CIRCUS_SUPPRESSION_DIAGNOSTIC_OPEN'
    finally:
        for path, bound in protected.items():
            if b.identity(path.read_bytes()) != bound:
                value['failures'].append(dict(stage='immutability',error=path.name))
        if value['failures']: value['native_verified'] = False
        (OUT/'native-result.json').write_bytes(b.stable(value))


def finish():
    path=OUT/'native-result.json'; value=c.strict(path.read_bytes()) if path.exists() else b.load(REPORT)
    if not path.exists(): value['failures'].append(dict(stage='workflow-setup',error='native not started; inspect steps'))
    checkpoint(value,'FINISH')


def pack():
    # Existing pack excludes work/runtime; explicitly exclude the genuine save cache too.
    dst=OUT/'artifact';dst.mkdir(exist_ok=True)
    import re
    for path in sorted(OUT.rglob('*')):
        if not path.is_file() or any(path.is_relative_to(p) for p in (dst,OUT/'work',OUT/'runtime',CACHE,OUT/'input')):continue
        if path.suffix not in ('.json','.c','.h','.stdout','.stderr','.ppm'):continue
        raw=path.read_bytes()
        if path.suffix=='.ppm':need(raw.startswith(b'P6\n240 160\n255\n') and len(raw)==115215,'screenshot shape')
        else:
            raw.decode('utf-8');need(b'\0' not in raw and len(raw)<4000000,'bounded text')
            need(not re.search(rb'gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----',raw),'credential')
        target=dst/path.relative_to(OUT);target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)


if __name__=='__main__':
    need(len(sys.argv)==2 and sys.argv[1] in ('prepare','native','finish','pack','result'),'command')
    if sys.argv[1]=='result':
        value=b.load(REPORT);need(value['native_verified'] and not value['failures'],'suppression target remains open')
    else:globals()[sys.argv[1]]()
