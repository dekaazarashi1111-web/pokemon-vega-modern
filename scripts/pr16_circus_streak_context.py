#!/usr/bin/env python3
"""Circus連勝の保存ownerと現HEADだけを安全に取り出す。ROM/nativeは起動しない。"""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / '.local/pr16-circus-streak-context'
EXACT = {
    'CHATGPT_RESUME.md', 'AGENTS.md', 'state/source-lock.json',
    'content/modernization/pr16_native_supply_resume_20260913.json',
    'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md',
    'content/modernization/p08_remaining_work.json',
    'content/modernization/pr16_bp_chooser_checkpoint.json',
    'content/modernization/pr16_circus_retention_checkpoint.json',
    'scripts/pr16_circus_checkpoint.py', 'scripts/pr16_circus_retention_record.py',
    'scripts/pr16_ring_followup_v2.py', 'scripts/pr16_ring_compiled_record.py',
    'scripts/pr16_circus_link.py', 'scripts/pr16_circus_record.py',
    'scripts/pr16_resume.py', 'tests/test_pr16_resume.py',
    'tools/mgba_pr16_circus_native.c', 'scripts/pr16_circus_streak_context.py',
    'tools/rom_allocator.py', 'tools/regression/rom_runtime.py',
}


def identity(raw):
    return {'size': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def run():
    if os.environ.get('GITHUB_REPOSITORY') != 'dekaazarashi1111-web/pokemon-vega-modern':
        raise ValueError('repository differs')
    if os.environ.get('GITHUB_REF') != 'refs/heads/codex/modernization-followup-20260908':
        raise ValueError('branch differs')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    if head != os.environ['GITHUB_SHA']:
        raise ValueError('checkout differs')
    names = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    # ファイル名による限定読取。マップrootやROM全走査ではない。
    chosen = sorted(n for n in names if n and (n in EXACT or n.endswith('/AGENTS.md') or
        (n.startswith(('overlays/', 'scripts/', 'config/', 'tests/')) and
         n.endswith(('.py', '.c', '.h', '.json', '.S')) and
         any(x in Path(n).name.lower() for x in ('save', 'parasite', 'sector', 'streak')))))
    if len(chosen) > 180:
        raise ValueError('bounded source count exceeded')
    OUT.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name in chosen:
        source = ROOT / name
        if source.is_symlink() or not source.is_file():
            raise ValueError('not regular tracked source: ' + name)
        raw = source.read_bytes()
        raw.decode('utf-8')
        if len(raw) > 3000000 or b'\0' in raw or re.search(rb'gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----', raw):
            raise ValueError('unsafe export: ' + name)
        target = OUT / 'source' / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        manifest[name] = identity(raw)
    for name in ('design/run_log.md', 'design/version_log.md'):
        raw = (ROOT / name).read_bytes()
        target = OUT / (Path(name).name + '.tail.txt')
        target.write_text('\n'.join(raw.decode().splitlines()[-65:]) + '\n')
        manifest[name] = identity(raw)
    def api(path):
        return json.loads(subprocess.check_output(['gh', 'api', 'repos/dekaazarashi1111-web/pokemon-vega-modern/' + path], cwd=ROOT))
    pr = api('pulls/16')
    if pr['state'] != 'open' or pr['merged'] or pr['head']['sha'] != head or pr['head']['repo']['full_name'] != os.environ['GITHUB_REPOSITORY']:
        raise ValueError('live PR changed')
    runs = api('actions/runs?per_page=30')['workflow_runs']
    report = dict(schema_version=1, status='SOURCE_CONTEXT_EXPORTED_NOT_ACCEPTANCE', source_head=head,
        pr=dict(state=pr['state'], draft=pr['draft'], merged=pr['merged'], head=pr['head']['sha']),
        runs=[{k:r[k] for k in ('id','name','head_branch','head_sha','status','conclusion')} for r in runs],
        source_bindings=manifest, new_emulator_processes=0, accepted_native_cases_replayed=0,
        rom_changes=0, release_ready=False)
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    subprocess.run(['git','diff','--exit-code'],cwd=ROOT,check=True)
    print(json.dumps({'status':report['status'],'source_head':head,'source_count':len(chosen),'new_emulator_processes':0}))

if __name__ == '__main__':
    run()
