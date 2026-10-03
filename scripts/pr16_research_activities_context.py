#!/usr/bin/env python3
"""研究の未受入活動用に、現在HEADのtracked textだけを読み取り専用で輸出する。"""
from __future__ import annotations
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
BRANCH = 'codex/modernization-followup-20260908'

def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT).decode().strip()

def api(path):
    request = urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+path,
        headers={'Authorization': 'Bearer '+os.environ['GITHUB_TOKEN'],
                 'Accept': 'application/vnd.github+json'})
    with urllib.request.urlopen(request, timeout=60) as response:
        return json.load(response)

def main():
    head = git('rev-parse', 'HEAD')
    assert head == os.environ['GITHUB_SHA']
    pr = api('pulls/16')
    assert pr['state'] == 'open' and not pr['merged']
    assert pr['head']['repo']['full_name'] == REPO and pr['head']['ref'] == BRANCH
    assert pr['head']['sha'] == head, 'concurrent HEAD update'
    tracked = set(git('ls-files').splitlines())
    explicit = {'AGENTS.md', 'CHATGPT_RESUME.md', 'config/active_play_baseline.json',
                'design/active_play_baseline.md', 'design/run_log.md', 'design/version_log.md',
                'content/modernization/p08_remaining_work.json',
                'content/modernization/pr16_bp_chooser_checkpoint.json',
                'content/modernization/pr16_native_supply_resume_20260913.json',
                'docs/PR16_NATIVE_SUPPLY_RESUME_20260913_JA.md',
                'docs/PR16_PHOTO_VISUAL_DIAGNOSIS_JA.md',
                'manifests/item_ids.csv', 'scripts/pr16_resume.py',
                'scripts/pr16_research_activities_context.py',
                '.github/workflows/pr16-research-activities-20260927.yml'}
    selected = set(explicit)
    for p in tracked:
        if p.endswith('/AGENTS.md'):
            selected.add(p)
        if (p.startswith(('scripts/pr16_research', 'tests/test_pr16_research',
                          'tools/mgba_pr16_research', 'content/research_economy_v1/',
                          'overlays/research_economy_v1/', 'config/research_',
                          'content/modernization/pr16_research', 'docs/PR16_RESEARCH_',
                          '.github/workflows/pr16-research-'))
                and Path(p).suffix in {'.py', '.c', '.h', '.json', '.md', '.csv', '.yml', '.txt'}):
            selected.add(p)
    # ASTによるローカルPython依存closure。モジュール実行・native実行はしない。
    pending = list(selected)
    while pending:
        p = pending.pop()
        if not p.endswith('.py') or p not in tracked:
            continue
        for node in ast.walk(ast.parse((ROOT/p).read_text(encoding='utf-8'), filename=p)):
            modules = []
            if isinstance(node, ast.Import):
                modules = [n.name for n in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module] + [node.module+'.'+n.name for n in node.names]
            for module in modules:
                for prefix in ('', 'scripts/', 'tools/'):
                    for suffix in ('.py', '/__init__.py'):
                        q = prefix+module.replace('.', '/')+suffix
                        if q in tracked and q not in selected:
                            selected.add(q); pending.append(q)
    assert explicit <= tracked, sorted(explicit-tracked)
    out = ROOT/'.local/pr16-research-activities/context'
    out.mkdir(parents=True, exist_ok=True)
    index = {'source_head': head, 'branch': BRANCH, 'files': {},
             'native_runs': 0, 'unit_runs': 0, 'arm_compiles': 0}
    with zipfile.ZipFile(out/'context.zip', 'w', zipfile.ZIP_DEFLATED) as archive:
        for p in sorted(selected):
            path = ROOT/p
            assert path.is_file() and not path.is_symlink(), p
            data = path.read_bytes(); data.decode('utf-8')
            assert b'\0' not in data and len(data) < 50_000_000, p
            index['files'][p] = {'size':len(data), 'sha256':hashlib.sha256(data).hexdigest(),
                                 'git_blob':git('rev-parse', 'HEAD:'+p)}
            archive.writestr(p, data)
        archive.writestr('index.json', json.dumps(index, ensure_ascii=False, indent=2)+'\n')
    runs = api('actions/runs?branch=codex%2Fmodernization-followup-20260908&per_page=100')['workflow_runs']
    live = {'source_head':head, 'pr':{k:pr[k] for k in ('number','state','draft','merged')},
            'runs':[{k:r[k] for k in ('id','name','head_sha','status','conclusion','created_at','updated_at')} for r in runs]}
    (out/'actions.json').write_text(json.dumps(live, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps({'source_head':head, 'files':len(selected), 'native_runs':0, 'unit_runs':0}))

if __name__ == '__main__':
    main()
