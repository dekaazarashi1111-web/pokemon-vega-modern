#!/usr/bin/env python3
"""新しい停止点継続/実LZ readerを保存。receipt分岐は測定を再実行しない。"""
from __future__ import annotations
import contextlib
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback
import unittest
import zipfile
import pr16_berry_child_lz as m
import pr16_berry_child_actions as old

ROOT = Path(__file__).resolve().parents[1]
a, publication = old.a, old.publication
read, load, write, snapshot = old.read, old.load, old.write, old.snapshot
BASE = '0e1069b62e5d0a5ac1187f3fec1782cd28881b78'
TASK = 'USER-20261011-BERRY-CHILD-LZ'
STATE, GUIDE, BRANCH, LOGS = old.STATE, old.GUIDE, old.BRANCH, old.LOGS
REPORT = 'content/modernization/pr16_berry_child_lz_checkpoint.json'
EVIDENCE = 'content/modernization/pr16_berry_child_lz_evidence'
REQUEST = 'content/modernization/pr16_berry_lz_receipt_request.json'
RECEIPT = 'content/modernization/pr16_berry_child_lz_receipt.json'
CODE = {'scripts/pr16_berry_child_lz.py', 'scripts/pr16_berry_child_lz_actions.py',
        'tests/test_pr16_berry_child_lz.py', 'tools/mgba_pr16_berry_child_lz.c', '.github/workflows/pr16-berry-child-lz.yml'}
WORK = ROOT / '.local/pr16-berry-child-lz'
PUBLIC = WORK / 'public'
PHASE = 'preflight'
ATTEMPT = {'rom_reconstructions': 0, 'native_processes': 0, 'accepted_test_reruns': 0,
           'accepted_reader_replays': 0, 'full_rom_scans': 0}


def public(name, value):
    (PUBLIC / name).write_bytes(m.encode(value) if isinstance(value, dict) else value)


def blob(raw):
    return hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()


def command(args, timeout=300):
    p = subprocess.run([str(x) for x in args], cwd=ROOT, capture_output=True, timeout=timeout)
    if p.returncode or p.stderr:
        public('command-failure.json', {'phase': PHASE, 'exit_code': p.returncode,
            'diagnostic': p.stderr.decode(errors='replace').replace(str(ROOT), '.')[-2000:]})
    m.need(p.returncode == 0 and not p.stderr, '限定command失敗')
    return p.stdout


def members(raw):
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        names = z.namelist()
        m.need(len(names) == len(set(names)) and sum(x.file_size for x in z.infolist()) < 16000000,
               'ZIP重複/サイズ境界')
        return {n: z.read(n) for n in names}


def receive(run_id, source, artifact_id, digest, published, report, step):
    receipt = publication.accepted_run(run_id, source, [step, 'Run actions/upload-artifact@v4'])
    art = a.fetch('actions/artifacts/' + str(artifact_id))
    m.need(not art['expired'] and art['workflow_run']['id'] == run_id and
           art['workflow_run']['head_sha'] == source and art['digest'] == 'sha256:' + digest, 'artifact identity')
    raw = a.fetch('actions/artifacts/' + str(artifact_id) + '/zip', binary=True)
    m.need(m.identity(raw) == {'size': art['size_in_bytes'], 'sha256': digest}, '全ZIP hash')
    data = members(raw);result = json.loads(data['result.json'])
    m.need(result['source_head'] == source and result['commit'] == published, '公開commit/run束縛')
    m.need(data[Path(report).name] == read(report), '保存checkpoint完全byte')
    context = members(data['scoped-context.zip'])
    for name, value in context.items():
        m.need(not name.startswith('/') and '..' not in Path(name).parts, '安全なmember名')
        value.decode();m.need(b'\0' not in value and a.git('show', published + ':' + name) == value, '全context blob')
    receipt.update(published_commit=published,
        artifact={k: art[k] for k in ('id', 'name', 'digest', 'size_in_bytes')},
        members={n: m.identity(v) for n, v in data.items()},
        context_bindings={n: m.identity(v) for n, v in context.items()},
        accepted_test_reruns=0, native_processes=0, rom_reconstructions=0)
    return receipt


def record(head, task, report_path, report, summary, goal, proofs, protected, before, allowed_source):
    global PHASE
    state = load(STATE)
    unchanged = m.encode({k: state['owner_execution_plan'][k] for k in ('wiki', 'wiki_readability', 'owner_review', 'scope')})
    observed = a.live(head)
    report.update(task=task, source_head=head, observed_head_checks=observed,
        actions_run_id=int(os.environ['GITHUB_RUN_ID']), actions_completion_confirmed=False,
        preserved_inputs={n: row[0] for n, row in before.items()},
        evidence_bindings={n: m.identity(read(n)) for n in sorted(proofs)},
        read_only_check_passed=True, task_graph_passed=True, **ATTEMPT)
    write(report_path, report)
    lane = state['owner_execution_plan']['technical_lanes']['save_capacity']
    lane.update(status=report['status'], checkpoint_path=report_path, next_ja=goal,
                scheduling_status='READY_FROM_SAVED_LZ_READER')
    state['next_action'] = {'id': 'SAVE_CAPACITY_BERRY_LZ_TYPED_RECEIPT', 'goal_ja': goal,
        'read_paths': [GUIDE, report_path, EVIDENCE + '/lz-reader.json'],
        'done_ja': '完了runと実LZ token全4byteを根拠に、保存親788/86へ対象1件だけの正式型差分を適用する。'}
    state['observed_head_checks'] = observed
    state['recording']['last_execution'] = {k: report[k] for k in ('task', 'source_head', 'actions_run_id',
        'actions_completion_confirmed', 'read_only_check_passed', 'task_graph_passed', *ATTEMPT.keys())}
    state['recording'].update(task=task, source_head=head, status=report['status'],
        berry_lz_checkpoint=report_path, berry_lz_no_replay=True)
    if report_path == REPORT:
        state['recording']['pending_berry_child_run'].update(status='COMPLETION_BOUND_WITHOUT_REPLAY',
            completion_evidence_path=EVIDENCE + '/child-completion.json')
    else:
        state['recording']['received_berry_lz_completion'] = EVIDENCE + '/actions-completion.json'
    text = read('CHATGPT_RESUME.md').decode();left, rest = text.split('## 次の未完作業\n', 1)
    _, right = rest.split('\n所有者が閲覧版で', 1)
    text = left + '## 次の未完作業\n\n現在の next_action は SAVE_CAPACITY_BERRY_LZ_TYPED_RECEIPT。' + summary + ' ' + goal + \
        ' 固定JSONのread_pathsを使う。\n\n所有者が閲覧版で' + right
    write('CHATGPT_RESUME.md', text.encode())
    state['bindings']['CHATGPT_RESUME.md'] = {'git_blob_sha': blob(text.encode()), **m.identity(text.encode())}
    m.need(unchanged == m.encode({k: state['owner_execution_plan'][k] for k in ('wiki', 'wiki_readability', 'owner_review', 'scope')}), 'Wiki/安全方針不変')
    write(STATE, state)
    guide = read(GUIDE).decode().replace('## 次の未完作業', '## 以前の停止点（履歴）')
    guide += '\n## ' + task + '\n\n' + summary + f'\n\n[checkpoint](../{report_path}) / [実reader](../{EVIDENCE}/lz-reader.json)。\n\n## 次の未完作業\n\n' + goal + '\n'
    write(GUIDE, guide.encode())
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    block = (f'\n## {now}\n- Timestamp: {now}\n- Task: {task} / Berry停止点以後のLZ reader\n'
        f'- Version: berry-child-lz-v1\n- Status: DONE（{report["status"]}。正式型/容量/保存統合は未完）\n'
        f'- Summary: {summary}\n- Files changed: LZ専用source/試験/native/Actionsと公開text証拠、固定MD/JSON、両ログ。\n'
        f'- Verify: 新scope={report.get("new_unit_tests", 0)}試験、原本hash/read-only/task graph/限定最終index。native={ATTEMPT["native_processes"]}、復元={ATTEMPT["rom_reconstructions"]}。受入済み再走0。\n'
        '- Boundary: 通信値はfixture、元BIOS/自然リンク/元cartの成功ではない。正式788/86・残7・安全容量0。全体CI greenを推測しない。\n'
        f'- Next: {goal}\n- Commit: この記録を含む同branch単親通常commit。実SHAはActions result/Gitで照合。\n'
        '- Network: 同repo PR/ref/Actions/artifact GET、既存固定再構成入力、非force push。'
        '一次資料 https://github.com/mgba-emu/mgba/blob/0.10.2/src/gba/bios.c と include/mgba/internal/arm/arm.h のSWI11/透過memory APIを確認。'
        '検索語: github pret berry fix multiboot crt0 02000120（有用な検索結果なし）。私有原本・展開byteは公開しない。\n')
    for name in LOGS:
        previous = read(name);m.need(('- Task: ' + task + ' /').encode() not in previous, '同task二重記録禁止')
        write(name, previous + block.encode())
    m.need(before == snapshot(protected), '旧原本byte/mtime不変')
    PHASE = 'final-index-and-push'
    allowed = allowed_source | proofs | LOGS | {report_path, STATE, GUIDE, 'CHATGPT_RESUME.md'}
    base = BASE if report_path == REPORT else a.git('rev-parse', head + '^').decode().strip()
    publication.final_index(base, allowed, report_path)
    m.need(before == snapshot(protected), 'push前の旧原本保全')
    m.need(a.git('ls-remote', 'origin', 'refs/heads/' + BRANCH).decode().split()[0] == head, 'push直前HEAD')
    a.git('config', 'user.name', 'github-actions[bot]');a.git('config', 'user.email', '41898282+github-actions[bot]@users.noreply.github.com')
    a.git('commit', '-m', task + ': 実LZ読出しの証拠と継続点を保存')
    a.git('push', 'origin', 'HEAD:' + BRANCH)
    pushed = a.git('rev-parse', 'HEAD').decode().strip()
    m.need(a.git('ls-remote', 'origin', 'refs/heads/' + BRANCH).decode().split()[0] == pushed, 'push後HEAD')
    for name in allowed:m.need(a.git('show', 'HEAD:' + name) == read(name), '全commit blob')
    for name in proofs | {report_path}:public(Path(name).name, read(name))
    with zipfile.ZipFile(PUBLIC / 'scoped-context.zip', 'w', zipfile.ZIP_DEFLATED) as z:
        for name in sorted((allowed | protected) - LOGS):z.writestr(name, read(name))
    public('result.json', {'status': report['status'], 'source_head': head, 'commit': pushed,
        'actions_run_id': int(os.environ['GITHUB_RUN_ID']), **ATTEMPT})
    print(f'RESULT=DONE TASK={task} VERIFY=PASS COMMIT={pushed}')


def run():
    global PHASE
    m.need(os.environ.get('GITHUB_REPOSITORY') == a.REPO and os.environ.get('GITHUB_REF') == 'refs/heads/' + BRANCH and
           os.environ.get('GITHUB_RUN_ATTEMPT') == '1', '同branch初回のみ')
    m.need(not WORK.exists(), '同scope再走禁止');PUBLIC.mkdir(parents=True)
    head = a.git('rev-parse', 'HEAD').decode().strip()
    m.need(head == os.environ['GITHUB_SHA'], 'event HEAD');a.live(head)
    m.need(not a.git('status', '--porcelain', '--untracked-files=no').strip(), 'clean checkout')
    m.need(not a.git('ls-files', '--', *[n + '/AGENTS.md' for n in ('tools','scripts','tests','docs','design','.github','.github/workflows','content','content/modernization')]).strip(), '追加AGENTSの確認が必要')
    state = load(STATE);lane = state['owner_execution_plan']['technical_lanes']['save_capacity']
    m.need([lane[k] for k in ('classified','unclassified','selected_unknown_origins','donor_safe_bytes')] == [788,86,7,0], '正式台帳不変')
    if (ROOT / REPORT).exists():
        finish_receipt(head);return
    m.need(state['next_action']['id'] == 'SAVE_CAPACITY_BERRY_CHILD_ENTRY_CONTINUATION', '現在のnext_action')
    m.need(set(a.git('diff','--name-only',BASE,head).decode().splitlines()) == CODE, '新5sourceだけ')
    cp = load(old.REPORT)
    protected = {old.REPORT}
    for key in ('source_bindings','evidence_bindings','preserved_inputs'):
        for name, expected in cp[key].items():
            m.need(m.identity(read(name)) == expected, '全継承入力hash');protected.add(name)
    before = snapshot(protected)
    PHASE = 'new-tests'
    stream = io.StringIO();suite = unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern='test_pr16_berry_child_lz.py')
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    m.need(result.wasSuccessful() and result.testsRun == 25 and not result.skipped, '新25試験')
    public('lz-tests.txt', stream.getvalue().encode())
    command(['python3','-B','scripts/validate_task_graph.py'])
    PHASE = 'old-child-completion-without-replay'
    receipt = receive(38108309355, '02d4a37b9def19af9f3f4acc3c8c0a5946381679', 11690471713,
        '101643044fc474ae24b3daf8f9fe376a6402bb7cc022c2abc07534688013e15e', BASE, old.REPORT,
        '親境界を再走せず子機entryを限定検証して保存')
    PHASE = 'native-build'
    version = command(['dpkg-query','-W','-f=${Version}','libmgba-dev']).decode()
    library = Path('/usr/lib/x86_64-linux-gnu/libmgba.so').read_bytes()
    header = Path('/usr/include/mgba/internal/arm/arm.h').read_bytes()
    m.need(version == '0.10.2+dfsg-1.1build3' and m.identity(library) == m.LIBRARY and
           blob(header) == 'f9eeafdb6dbfbf22b92b5bf3dc481597738512b2', '固定native library/ABI')
    binary = WORK / 'native'
    command(['cc','-std=c11','-O2','-Wall','-Wextra','-Werror',ROOT / 'tools/mgba_pr16_berry_child_lz.c','-lmgba','-lm','-o',binary])
    PHASE = 'one-new-scope-reconstruction'
    import pr16_dex_hof_capacity_actions as reconstruction
    reconstruction.OUT = WORK / 'candidate';reconstruction.OUT.mkdir()
    ATTEMPT['rom_reconstructions'] = 1;public('attempt.json', ATTEMPT)
    with (WORK / 'private-reconstruction.log').open('w') as log, contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
        raw, candidate = reconstruction.reconstruct()
    m.need(m.identity(raw) == candidate['candidate'] == m.CANDIDATE, '全候補SHA/配置')
    body = raw[m.START-0x08000000:m.START-0x08000000+m.SIZE]
    m.need(m.identity(body) == m.IMAGE, '転送image不変')
    m.decode_lz(body[m.STREAM-m.CHILD:])  # native前に出力/参照境界を拒否する。
    rom = WORK / 'candidate.gba';rom.write_bytes(raw)
    PHASE = 'new-continuation-native'
    ATTEMPT['native_processes'] = 1;public('attempt.json', ATTEMPT)
    native = json.loads(command([binary,rom,WORK / 'expanded.bin'], timeout=120))
    public('native.json', native)
    m.need(rom.read_bytes() == raw, '全ROM file不変')
    proof = m.bind(raw,native,load(old.EVIDENCE+'/child-reader.json'),(WORK/'expanded.bin').read_bytes())
    proof.update(library=m.LIBRARY,library_package_version=version,abi_header=m.identity(header),
        native_binary=m.identity(binary.read_bytes()), **ATTEMPT)
    names = {'lz-reader.json':proof,'native.json':native,'child-completion.json':receipt,'lz-tests.txt':stream.getvalue().encode()}
    proofs = {EVIDENCE+'/'+name for name in names}
    for name, value in names.items():write(EVIDENCE+'/'+name,value)
    saved = snapshot(proofs);m.need(load(EVIDENCE+'/lz-reader.json') == proof and snapshot(proofs) == saved, '保存後read-only')
    parsed = proof['reader']
    summary = (f'保存PC0x02000120から通信32readを明示fixtureとする新nativeを実行。実ARM caller→SWI11→0x020001D8帰還を{native["steps"]}stepで観測。'
        f'展開元{parsed["consumed_bytes"]}byteを全て1回ずつ実readし、対象0x086C51BF全4byteをLZ tokenとして消費。'
        f'展開{parsed["output"]["size"]}byteは独立parserと完全一致。親13profile/旧393220stepは再走0。')
    goal = '新LZ測定の完了run/全artifactを再走せず受領し、正式788/86親へ対象1件だけの条件付き圧縮token型差分を適用する。容量移管/heap/controller/局所Saveは未完。残7・安全容量0。'
    report = {'schema_version':1,'status':'LZ_READER_OBSERVED_COMPLETION_PENDING','candidate':m.CANDIDATE,
        'new_unit_tests':result.testsRun,'source_bindings':{n:m.identity(read(n)) for n in sorted(CODE)},
        'target_bytes_consumed':4,'formal_classified':788,'formal_unclassified':86,'selected_unknown_origins':7,'donor_safe_bytes':0,
        'next_ja':goal}
    record(head,TASK,REPORT,report,summary,goal,proofs,protected,before,CODE)


def finish_receipt(head):
    global PHASE
    PHASE = 'receipt-without-native-or-test-replay'
    m.need(not (ROOT / RECEIPT).exists(), '受領済み再走禁止')
    p = load(REQUEST);cp = load(REPORT)
    m.need(p['run_id'] == cp['actions_run_id'] and p['source_head'] == cp['source_head'], '受領依頼のscope')
    m.need(set(a.git('diff','--name-only',head+'^',head).decode().splitlines()) == {REQUEST}, 'receipt依頼だけ')
    protected = {REPORT} | set(cp['source_bindings']) | set(cp['evidence_bindings']) | set(cp['preserved_inputs'])
    for key in ('source_bindings','evidence_bindings','preserved_inputs'):
        m.need(all(m.identity(read(n))==v for n,v in cp[key].items()), '受領原本hash')
    before = snapshot(protected)
    receipt = receive(p['run_id'],p['source_head'],p['artifact_id'],p['artifact_sha256'],p['published_commit'],REPORT,
                      '保存停止点から実LZ readerだけを検証して記録')
    path = EVIDENCE+'/actions-completion.json';write(path,receipt)
    command(['python3','-B','scripts/validate_task_graph.py'])
    proof = load(EVIDENCE+'/lz-reader.json');m.validate_native(proof['native'],proof['reader'])
    summary = '子機継続LZ測定runの完了・全ZIP/member・公開commit/contextを受領。対象全4byteは実SWI11の展開元token。測定原本のpending表記は改作せず、別receiptで完了を確定。新native/復元/旧試験再走0。'
    goal = '保存済みLZ readerと完了receiptから、正式788/86のreference-chain/unknown-frontier/window-progressへ対象0x086C51BFの1件だけの型差分を追加し、他873行と原本を保持する。reader/native/25試験は再走しない。容量移管/heap/controller/局所Saveは未完。残7・安全容量0。'
    report = {'schema_version':1,'status':'LZ_READER_COMPLETION_BOUND_FORMAL_DELTA_PENDING',
        'measurement_run_id':p['run_id'],'measurement_source_head':p['source_head'],
        'measurement_completion_confirmed':True,'new_unit_tests':0,'formal_classified':788,'formal_unclassified':86,
        'selected_unknown_origins':7,'donor_safe_bytes':0,'next_ja':goal}
    record(head,TASK+'-RECEIPT',RECEIPT,report,summary,goal,{path},protected,before,{REQUEST})


if __name__ == '__main__':
    try:run()
    except Exception as exc:
        PUBLIC.mkdir(parents=True,exist_ok=True)
        public('failure.json', {'status':'NOT_ACCEPTED','phase':PHASE,'exception_type':type(exc).__name__,
            'detail':str(exc).replace(str(ROOT),'.')[:300] if isinstance(exc,ValueError) else None,
            'frames':[{'path':f.filename[len(str(ROOT))+1:],'line':f.lineno} for f in traceback.extract_tb(exc.__traceback__) if f.filename.startswith(str(ROOT)+'/scripts/')],
            'attempt':ATTEMPT})
        print('RESULT=BLOCKED TASK='+TASK+' VERIFY=FAIL PHASE='+PHASE+' TYPE='+type(exc).__name__)
        sys.exit(1)
