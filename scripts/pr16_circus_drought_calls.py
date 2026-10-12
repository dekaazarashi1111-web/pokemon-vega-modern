#!/usr/bin/env python3
"""定数callbackの消失を実関数境界で修復。旧失敗は再実行せず照合する。"""
from pathlib import Path
import hashlib
import io
import json
import os
import re
import struct
import subprocess
import sys
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT), str(ROOT / 'scripts')]
SELF = 'scripts/pr16_circus_drought_calls.py'
TEST = 'tests/test_pr16_circus_drought_calls.py'
WORKFLOW = '.github/workflows/pr16-circus-drought-calls.yml'
SOURCE = 'overlays/circus_streak/circus_drought.c'
REPORT = 'content/modernization/pr16_circus_drought_calls.json'
TASK = 'USER-20260919-CIRCUS-DROUGHT-CALLS'
OUT = ROOT / '.local/pr16-circus-drought-calls'
OLD_RUN = 35434591898
OLD_JOB = 105875004261
OLD_ARTIFACT = 10582003357
OLD_ARCHIVE = dict(size=1752874, sha256='9816094abec54457e80eff70c468addca7cef7bbb41722c5d16eefbf0f33f842')
OLD_CANDIDATE = '45bdbd720019cbb1e864f44bc4a745ef46303791d6fe089c84c0f8e6b758be0a'
NEXT = '新候補で実17勝後のDrought復帰とnative完了cursorを検証し、未完continuation/原party600/owner64/通常Save/fresh Continueへ進む。30勝未達なら最初の新停止点だけ修復し、真正30勝後に正規特性抑制を別検証。旧失敗の同一native/旧2link/受入単体は再実行しない。'
WRAPPERS = '''/* 定数addressをinline関数のcallback引数へ直接渡さない。
 * GCCで分岐/復帰が消失する縮小再現を保存し、実関数symbolをABI境界にする。 */
__attribute__((noinline)) static void DroughtOriginal(void) { NATIVE(0x0807AD09u)(); }
__attribute__((noinline)) static void DroughtInitVars(void) { NATIVE(0x0807ACD5u)(); }
__attribute__((noinline)) static void DroughtStep(void) { NATIVE(0x0807AD39u)(); }
'''
OLD_ARGS = 'NATIVE(0x0807AD09u), NATIVE(0x0807ACD5u), NATIVE(0x0807AD39u)'
NEW_ARGS = 'DroughtOriginal, DroughtInitVars, DroughtStep'


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(raw):
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def stable(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def repair(source):
    anchor = '__attribute__((used, noinline, externally_visible))'
    need(source.count(anchor) == 1 and source.count(OLD_ARGS) == 1 and 'DroughtOriginal' not in source,
         'native callback repair anchor differs')
    return source.replace(anchor, WRAPPERS + anchor).replace(OLD_ARGS, NEW_ARGS)


def relative_text(raw, root):
    text = raw.decode('utf-8')
    need('\0' not in text, 'text evidence only')
    return text.replace(str(root) + '/', '').encode('utf-8')


def verify_target(payload, disassembly):
    match = re.search(r'^[0-9a-f]+ <CircusDroughtInitAll>:\n(.*?)(?=^[0-9a-f]+ <|\Z)', disassembly, re.M | re.S)
    need(match is not None, 'ARM entry absent')
    entry = match.group(1)
    for pattern in (r'\bstrb\b', r'\bpop\b', r'\bb(?:eq|ne|hi|ls|pl|mi|cc|cs|ge|le|gt|lt)(?:\.n)?\b'):
        need(re.search(pattern, entry) is not None, 'ARM conditional/write/return disappeared: ' + pattern)
    for symbol in ('DroughtOriginal', 'DroughtInitVars', 'DroughtStep'):
        need(re.search(r'^[0-9a-f]+ <' + symbol + r'>:', disassembly, re.M) is not None, 'native ABI wrapper absent: ' + symbol)
    for address in (0x0807AD09, 0x0807ACD5, 0x0807AD39):
        need(struct.pack('<I', address) in payload, 'native delegate missing')
    return dict(entry_has_condition=True, entry_has_cursor_store=True, entry_has_return=True,
                native_symbol_boundaries=3, native_addresses_verified=3)


def failed_events(raw):
    rows = [json.loads(line.split(b' ', 1)[1]) for line in raw.splitlines() if line.startswith(b'CIRCUS_CONTINUOUS ')]
    need(len(rows) == 80 and rows[-1]['label'] == 'timeout', 'old timeout event count')
    need(rows[-2]['label'] == 'outcome' and rows[-2]['outcome'] == 1 and rows[-2]['battle'] == 16, 'old seventeenth WIN absent')
    need(rows[-1]['callback2'] == 0x08055E75 and rows[-1]['script'] == 0x09FF4D77, 'old native stop changed')
    need(not any(r['label'] in ('saved', 'reloaded') for r in rows), 'old result unexpectedly saved')
    need(sum(r['label'] == 'outcome' and r['outcome'] == 1 for r in rows) == 17, 'old win count')
    need(sum(r['label'] == 'settled' for r in rows) == 16 and rows[-1]['bp'] == 45, 'old settlement count')
    return dict(events=80, real_win_outcomes=17, settled_wins=16, bp=rows[-1]['bp'], saved=False, reloaded=False,
                native_return_verified=False, original_conclusion='failure')


def configure():
    import pr16_circus_drought as d
    if not hasattr(d, '_calls_original_compile'):
        d._calls_original_compile = d.compile_bridge
        d._calls_original_files = d.FILES
    d.SELF, d.TEST, d.WORKFLOW, d.REPORT, d.TASK, d.OUT, d.NEXT = SELF, TEST, WORKFLOW, REPORT, TASK, OUT, NEXT
    d.FILES = tuple(dict.fromkeys((SELF, TEST, WORKFLOW, *d._calls_original_files)))
    def checked_compile(folder, address, armed):
        payload, entry = d._calls_original_compile(folder, address, armed)
        checked = verify_target(payload, (folder / 'disassembly.txt').read_text())
        (folder / 'target-contract.json').write_bytes(stable(checked))
        # 元のstack-usageもartifact内でidentityを保持し、tracked抄録だけ相対化する。
        return payload, entry
    d.compile_bridge = checked_compile
    return d, d.configure()


def export(name, raw, evidence):
    transformed = relative_text(raw, ROOT)
    path = ROOT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    need(not path.exists() or path.read_bytes() == transformed, 'immutable evidence collision')
    path.write_bytes(transformed)
    evidence[name] = identity(transformed)
    return dict(original=identity(raw), tracked=identity(transformed), workspace_relative=raw != transformed)


def record(value, phase, stop):
    import pr16_resume as resume
    d, b = configure()
    r = b.rec
    state = resume.load(ROOT, resume.STATE)
    loss = resume.load(ROOT, r.REPORT)
    (ROOT / REPORT).write_bytes(stable(value))
    ref = dict(path=REPORT, classification=value['classification'], run_id=int(os.environ['GITHUB_RUN_ID']))
    state['circus_drought_followup'] = loss['drought_calls_followup'] = ref
    state['circus_continuous_followup'] = dict(ref, target_wins=30)
    state['prior_actions_reconciled'] = value['actions_reconciled']
    note = 'run35434591898/job105875004261は独立2link一致だが実17勝後timeout。生成entryの条件分岐/復帰が消失し、記録もstack-usageのrunner絶対pathで停止。native受入/Save/30勝ではない。原artifact10582003357を保持し、失敗の同一nativeと旧2linkは再実行しない。'
    if note not in state['do_not_repeat']:
        state['do_not_repeat'].insert(0, note)
    r.SELF, r.TEST, r.WORKFLOW, r.HEADER, r.TASK = SELF, TEST, WORKFLOW, d.HEADER, TASK
    r.checkpoint(state, loss, stop, NEXT, [REPORT, *d.FILES, *value.get('text_evidence', {})], phase,
                 value['classification'] + '。定数callback縮小再現/実関数wrapper/ARM条件分岐・cursor store・復帰/失敗原本identity/相対path抄録を検証。元artifact不変、全体private guardを成功へ改作しない。')


def prepare():
    import pr16_resume as resume
    d, b = configure()
    b.rec.scope()
    state = resume.validate(ROOT)
    need(not (ROOT / REPORT).exists(), 'attempt already exists; reconcile instead of replay')
    run = b.rec.api('actions/runs/' + str(OLD_RUN))
    artifact = b.rec.api('actions/artifacts/' + str(OLD_ARTIFACT))
    need(run['status'] == 'completed' and run['conclusion'] == 'failure' and run['head_sha'] == 'bf27c13d5ff9f4089084cec269389b3d492ecb13', 'old run identity')
    need(artifact['workflow_run']['id'] == OLD_RUN and artifact['digest'] == 'sha256:' + OLD_ARCHIVE['sha256'], 'old artifact identity')
    raw = subprocess.check_output(['gh', 'api', 'repos/' + b.rec.REPO + '/actions/artifacts/' + str(OLD_ARTIFACT) + '/zip'], cwd=ROOT)
    need(identity(raw) == OLD_ARCHIVE, 'old archive bytes differ')
    evidence, transforms = {}, {}
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        need(len(z.namelist()) == len(set(z.namelist())), 'duplicate ZIP members')
        members = json.loads(z.read('members.json'))
        names = ['finish/build.json', 'finish/native/report.json', 'finish/native/' + d.probe.CASE + '.stderr',
                 'finish/compile-1/disassembly.txt', 'finish/compile-1/stack-usage.txt', 'finish/compile-2/disassembly.txt']
        for name in names:
            original = z.read(name)
            need(identity(original) == members[name], 'member identity differs: ' + name)
            target = 'evidence/pr16_circus_drought_calls/' + str(OLD_RUN) + '/' + name.removeprefix('finish/')
            transforms[target] = export(target, original, evidence)
        build = json.loads(z.read(names[0]))
        need(build['candidate']['sha256'] == OLD_CANDIDATE and build['independent_arm_links'] == 2, 'old candidate differs')
        previous = failed_events(z.read(names[2]))
        previous.update(run_id=OLD_RUN, job_id=OLD_JOB, artifact_id=OLD_ARTIFACT, archive=OLD_ARCHIVE,
                        candidate=build['candidate'], independent_arm_links=2, visual_review_ja='第16戦後の通常交換画面、第17戦の勝利直後、timeoutの黒画面を照合。保存画面は存在しない。')
    before = (ROOT / SOURCE).read_bytes()
    need(identity(before) == state['source_bindings'][SOURCE], 'unreviewed source drift')
    (ROOT / SOURCE).write_text(repair(before.decode()))
    value = dict(schema_version=1, classification='CIRCUS_DROUGHT_CALLS_REPAIR_PREPARED', previous=previous,
                 actions_reconciled=[{k: run[k] for k in ('id', 'head_sha', 'status', 'conclusion')}],
                 source_change=dict(path=SOURCE, before=identity(before), after=identity((ROOT / SOURCE).read_bytes())),
                 text_evidence=evidence, evidence_transformations=transforms,
                 host_tests=b.rec.tests([Path(TEST).name, Path(d._calls_original_files[1]).name]),
                 accepted_native_cases_replayed=0, independent_old_arm_links_replayed=0,
                 win_return_native_verified=False, genuine_30_wins_verified=False, visual_review_completed=False,
                 physical_admission_accepted=False, suppression_accepted=False, release_ready=False,
                 external_research_ja='GCC integer function pointer argument inline builtin_unreachable等で公式一次情報を検索したが該当資料なし。外部記事を原因証拠にせず、固定ARM出力とhost縮小再現を根拠とする。')
    record(value, 'PREPARED', '最新run35434591898の失敗と記録停止を原本照合。定数callbackで消失する分岐/復帰を実関数symbol境界へ修復し、host/生成ARMの回帰を追加。未完nativeだけを後継候補で検証する。')


def finish():
    d, b = configure()
    value = json.loads((ROOT / REPORT).read_bytes())
    value['classification'] = 'CIRCUS_DROUGHT_CALLS_NATIVE_OPEN'
    for path, key in [('build.json', 'build'), ('native/report.json', 'native'), ('return-result.json', 'return_result'), ('native/streak.json', 'scoped_result')]:
        p = OUT / path
        if p.exists():
            value[key] = json.loads(relative_text(p.read_bytes(), ROOT))
    if 'build' in value:
        value['candidate'] = value['build']['candidate']
    if 'return_result' in value:
        value['classification'] = value['return_result']['classification']
        value['win_return_native_verified'] = True
        value['genuine_30_wins_verified'] = value['return_result']['genuine_30_wins_verified']
    value['recording_run'] = int(os.environ['GITHUB_RUN_ID'])
    # 過去の原本は上書きしない。新しいrunのtextだけを追加する。
    for p in sorted(OUT.rglob('*')):
        if not p.is_file() or p.suffix not in {'.json', '.txt', '.stderr', '.stdout'} or p.name.endswith('-receipt.json'):
            continue
        name = 'evidence/pr16_circus_drought_calls/' + os.environ['GITHUB_RUN_ID'] + '/' + p.relative_to(OUT).as_posix()
        value['evidence_transformations'][name] = export(name, p.read_bytes(), value['text_evidence'])
    record(value, 'RECORDED', '実関数境界修復の独立2link/生成ARM/全ROM rollbackと新native原本を保存。17勝後復帰=' + str(value['win_return_native_verified']) + '、真正30勝=' + str(value['genuine_30_wins_verified']) + '。画像レビュー/特性抑制/P08は別ゲート。')


def main():
    need(len(sys.argv) == 2, 'one command required')
    action = sys.argv[1]
    if action == 'prepare':
        prepare()
    elif action == 'finish':
        finish()
    else:
        d, b = configure()
        if action == 'pipeline':
            b.pipeline()
        elif action == 'reconstruct':
            d.reconstruct()
        elif action == 'native':
            d.native()
        elif action == 'pack':
            d.c.f.pack()
        else:
            raise SystemExit('unknown command')


if __name__ == '__main__':
    main()
