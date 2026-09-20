#!/usr/bin/env python3
"""完了済み通常戦闘の原本/5画面を受入。新native・ROM再構築は行わない。"""
from __future__ import annotations
import copy
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SELF = 'scripts/pr16_p08_ordinary_acceptance.py'
TEST = 'tests/test_pr16_p08_ordinary_acceptance.py'
WORKFLOW = '.github/workflows/pr16-p08-ordinary-accept.yml'
FILES = (SELF, TEST, WORKFLOW)
REPORT = 'content/modernization/pr16_p08_ordinary_acceptance.json'
SOURCE = 'content/modernization/pr16_p08_ordinary_abi.json'
OUT = ROOT / '.local/pr16-p08-ordinary-accept'
RUN, JOB, ARTIFACT = 35512907219, 106083860159, 10605572804
HEAD = '63ec984e57524d747ef2a2b9816a7c979f2e1b37'
CASE = 'circus-exit30-ordinary'
TARGET = dict(size=33554432, sha256='46487d98a09916012dccd335d2fac983e8130087c9812276e889b4f199638c38')
ARCHIVE = dict(size=90622, sha256='8d439eb6f7e831ef5f2f58df23db3d6fa99c4f156c09cb5de54414f7cb94478a')
SCREENS = {
    CASE+'-ordinary-run-selection.ppm': '4cf4fb8217c4f916b9e18dbde148fb404a7ec571406e12678c70fdc718b7ac45',
    CASE+'-streak-01-p08-exit30.ppm': '205442de09fb3b8ad740d9a574a9675d5744837353bf245d8aa2c761ee275e22',
    CASE+'-streak-02-p08-town-boundary.ppm': '3d834aecbc36ea9707ea07d046b77f6a69e13ded9da1e1bf28b0b6861e5d5799',
    CASE+'-streak-03-p08-normal-action.ppm': 'de4680620ee6707d12cdaf51f679f4382b6c82c1982c36031ab79fdc6bee338a',
    CASE+'-streak-04-p08-normal-return.ppm': 'af82855843192632f919d0ea10740353834dd7ef5144b9646eb2ecbc95dc90b1',
}


def need(ok, label):
    if not ok:
        raise ValueError(label)


def verify(value):
    """受入済み/旧失敗との取り違え、boolを整数に見せる過大主張を拒否する。"""
    need(value['candidate'] == TARGET and value['workflow_source_head'] == HEAD
         and type(value['recording_run']) is int and value['recording_run'] == RUN
         and value['regression_id'] == 'P08_CIRCUS_POST_EXIT_ORDINARY'
         and value['case'] == CASE and value['task'] == 'USER-20260920-P08-ORDINARY-ABI', 'ordinary provenance')
    need(value['native_verified'] is True and value['representative_accepted'] is False
         and value['visual_review_completed'] is False and value['release_ready'] is False
         and value['failures'] == [], 'ordinary scope')
    for key, expected in dict(new_emulator_processes=1, fresh_cores=1, host_compiles=1,
                              arm_compiles=0, arm_links=0, accepted_standalone_replays=0,
                              prefix_wins_reexecuted=0, rom_changes=0).items():
        need(type(value[key]) is int and value[key] == expected, 'ordinary accounting: '+key)
    need(value['screens'] == {name: dict(size=115215, sha256=digest)
                             for name, digest in SCREENS.items()}, 'reviewed screens differ')
    old = value['previous_trial']
    need(old['run_id'] == 35512429611 and old['conclusion'] == 'failure'
         and old['accepted'] is False, 'historical failure relabelled')


def verify_images(members, expected):
    names = {name for name in members if name.startswith('screens/')}
    need(names == {'screens/'+name for name in SCREENS}, 'screen member set')
    for name, digest in SCREENS.items():
        raw = members['screens/'+name]
        actual = dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        need(raw.startswith(b'P6\n240 160\n255\n') and len(raw) == 115215
             and actual == expected[name] and actual['sha256'] == digest, 'reviewed image bytes: '+name)


def accept():
    sys.path[:0] = [str(ROOT/'scripts'), str(ROOT)]
    import pr16_p08_checkpoint as cp
    import pr16_p08_ordinary_abi as m
    import pr16_p08_ring_recovery as e
    b = cp.b
    b.OUT = OUT
    b.scope()
    b.resume.validate(ROOT)
    OUT.mkdir(parents=True, exist_ok=True)
    need(not (ROOT/REPORT).exists(), 'ordinary already accepted; do not repeat')
    run = b.api('actions/runs/'+str(RUN))
    job = b.api('actions/jobs/'+str(JOB))
    art = b.api('actions/artifacts/'+str(ARTIFACT))
    need(run['head_sha'] == HEAD and run['status'] == 'completed'
         and run['conclusion'] == 'success', 'ordinary completed run')
    need(job['run_id'] == RUN and job['head_sha'] == HEAD and job['status'] == 'completed'
         and job['conclusion'] == 'success' and all(s['conclusion'] == 'success' for s in job['steps']), 'ordinary completed job')
    need(not art['expired'] and art['workflow_run']['id'] == RUN
         and art['workflow_run']['head_sha'] == HEAD
         and art['digest'] == 'sha256:'+ARCHIVE['sha256'], 'ordinary artifact metadata')
    raw = subprocess.check_output(['gh', 'api', 'repos/'+b.REPO+'/actions/artifacts/'+str(ARTIFACT)+'/zip'], cwd=ROOT)
    members = e.archive_members(raw, ARCHIVE)
    value = e.strict(members['native-result.json'])
    verify(value)
    current = b.load(SOURCE)
    for key in ('native_result', 'native_proof', 'screens', 'source_bindings', 'generated',
                'protected_originals', 'transitive_compiled_sources', 'oracle', 'original', 'previous_trial'):
        need(current[key] == value[key], 'tracked original projection: '+key)
    for path, expected in {**value['source_bindings'], **value['protected_originals'],
                           **value['transitive_compiled_sources']}.items():
        need(e.identity((ROOT/path).read_bytes()) == expected, 'source/protected drift: '+path)
    stdout = members['execution/'+CASE+'.stdout']
    stderr = members['execution/'+CASE+'.stderr']
    proc = e.strict(members['execution/'+CASE+'.process.json'])
    row, proof = m.validate(stdout, stderr, proc, value['oracle'], value['original']['exit_event'])
    proof['previous_prefix'] = m.prefix_proof(members['previous.stderr'], stderr)
    need(row == value['native_result'] and proof == value['native_proof'], 'raw native projection')
    verify_images(members, value['screens'])
    # 原本のZIPはROM/saveを含まない固定artifact。Gitにはbyte包絡textとして保存する。
    execution = OUT/'execution'
    execution.mkdir(exist_ok=True)
    (execution/'original-artifact.json').write_bytes(e.stable(dict(artifact_id=ARTIFACT, archive=ARCHIVE, payload=e.envelope(raw))))
    result = copy.deepcopy(value)
    result.update(task='USER-20260921-P08-ORDINARY-ACCEPT', source_report=SOURCE,
                  source_report_identity=e.identity((ROOT/SOURCE).read_bytes()), original_run_id=RUN,
                  original_job_id=JOB, original_source_head=HEAD, original_conclusion='success',
                  artifact_id=ARTIFACT, archive=ARCHIVE, representative_accepted=True,
                  visual_review_completed=True, original_native_processes=1, original_fresh_cores=1,
                  new_emulator_processes=0, fresh_cores=0, host_compiles=0,
                  workflow_source_head=os.environ['GITHUB_SHA'])
    result['visual_review'] = dict(
        reviewer='ChatGPT', reviewed_at_utc='2026-09-20', reviewed_screen_count=5,
        artifact_id=ARTIFACT, archive=ARCHIVE, screen_identities=value['screens'], visual_review_completed=True,
        observations_ja=[
            '退出後の町、6ばんどうろへの境界、ファマーLv50対ハブネークLv78の通常戦闘、にげる選択、草むらfield復帰を5画面で確認。',
            '画面から抑制や保存状態を推測せず、自然predicate=false 8回、通常dispatcher12回、owner64/Factory106byte、BP90、Savecounter3不変を原本で照合。',
            '真正退出Save30のContinue後だけの代表。現候補の施設内/退出cleanupは別の受入済み原本を継承。旧失敗run35512429611はfailureのまま。'])
    cp.save(REPORT, result, FILES, OUT, 'ACCEPT',
            'P08最後の通常戦闘代表を完了Actions・原本・5画面で受入。4代表の実測は完了、候補移送の最終照合は次。新native/ARM/ROM変更0。',
            'P08_TRANSFER_RECONCILIATION',
            '四代表と候補影響台帳を照合して移送・古い所有範囲CIを整合。その後Issue #18の候補Wikiを生成し、clean-ROM独立2生成/BPS固定/release判定はWiki後まで開始しない。',
            [SOURCE, 'content/modernization/pr16_p08_candidate_impact.json',
             'content/modernization/pr16_p08_memory_acceptance.json',
             'content/modernization/pr16_p08_ring_acceptance.json',
             'content/modernization/pr16_circus_acceptance.json'])


def context():
    """次の候補移送/Wiki実装用に、限定tracked textとファイル索引だけをartifactへ。"""
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    tracked = [p for p in tracked if p]
    wanted = {
        'AGENTS.md', 'CHATGPT_RESUME.md', 'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md',
        'content/modernization/pr16_native_supply_resume_20260913.json',
        'content/modernization/p08_remaining_work.json', 'config/active_play_baseline.json',
        'design/active_play_baseline.md', 'scripts/pr16_resume.py', 'scripts/pr16_p08_checkpoint.py',
        'scripts/pr16_circus_battle25.py', 'scripts/pr16_ring_compiled_record.py',
        '.github/workflows/p03-forgetting-ci.yml', 'scripts/validate_task_graph.py',
    }
    wanted.update(p for p in tracked if p.endswith('AGENTS.md'))
    wanted.update(p for p in tracked if (p.startswith(('scripts/', 'tests/')) and
                  ('pr16_p08' in p or 'wiki' in p or 'p03_forgetting' in p)))
    wanted.update(p for p in tracked if p.startswith('content/modernization/pr16_p08') and p.endswith('.json'))
    wanted.update(p for p in tracked if p.startswith(('config/', 'content/')) and 'wiki' in p and p.endswith('.json'))
    out = OUT/'artifact'/'context'
    out.mkdir(parents=True, exist_ok=True)
    index = {}
    for name in sorted(wanted & set(tracked)):
        path = ROOT/name
        need(path.is_file() and not path.is_symlink(), 'context regular text')
        raw = path.read_bytes()
        raw.decode('utf-8')
        need(b'\0' not in raw and len(raw) < 4_000_000, 'context bounded text')
        dest = out/name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(raw)
        index[name] = dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    (out/'source-index.json').write_text(json.dumps(dict(head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip(), files=index), ensure_ascii=False, indent=2)+'\n')
    # 索引はファイル名とサイズのみ。private/binaryの内容は取得しない。
    (out/'tracked-paths.json').write_text(json.dumps({p:(ROOT/p).stat().st_size for p in tracked if (ROOT/p).is_file() and not (ROOT/p).is_symlink()}, ensure_ascii=False, indent=2)+'\n')


if __name__ == '__main__':
    need(len(sys.argv) == 2, 'command required')
    if sys.argv[1] == 'accept':
        accept()
    elif sys.argv[1] == 'pack':
        sys.path.insert(0, str(ROOT/'scripts'))
        import pr16_p08_checkpoint as cp
        cp.pack(OUT, FILES)
        context()
    else:
        raise ValueError('unknown command')
