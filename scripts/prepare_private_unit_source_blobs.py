#!/usr/bin/env python3
"""固定差分を未参照Git blobへ準備する。branch/commit/refは変更しない。"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import urllib.error
import urllib.request

from scripts.github_private_environment import SECRET_PATTERNS

ROOT = Path(__file__).resolve().parents[1]
REPO = 'dekaazarashi1111-web/pokemon-vega-modern'
TASK = 'USER-20260905-PRIVATE-FULL-UNIT-R2'
LOGS = {'design/run_log.md', 'design/version_log.md'}


def sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def prepare(root: Path, plan: dict) -> list[tuple[str, bytes]]:
    if plan.get('schema_version') != 1 or plan.get('task') != TASK:
        raise ValueError('source edit schema/task mismatch')
    prepared, seen = [], set()
    for row in plan['files']:
        name = row['path']
        rel = PurePosixPath(name)
        permitted = name in LOGS or name in {'Makefile', 'overlays/vega_adapter/build_module.py'} or re.fullmatch(r'(scripts|tests|tools|config|infra)/[A-Za-z0-9_/]+\.(py|json|sh)', name)
        if not permitted or rel.is_absolute() or '..' in rel.parts or '\\' in name or name in seen:
            raise ValueError('source edit path rejected')
        seen.add(name)
        path = root / name
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError('source edit symlink rejected')
        raw = path.read_bytes() if path.exists() else b''
        before = sha(raw) if path.exists() else None
        if before != row['before_sha256']:
            raise ValueError('source before SHA-256 mismatch')
        text = raw.decode('utf-8')
        if name in LOGS:
            if 'replacements' in row or not isinstance(row.get('append'), str) or not row['append'].startswith('\n'):
                raise ValueError('logs are append-only')
            text += row['append']
        else:
            for change in row['replacements']:
                if text.count(change['old']) != 1:
                    raise ValueError('source edit context is not unique')
                text = text.replace(change['old'], change['new'], 1)
        result = text.encode('utf-8')
        if sha(result) != row['after_sha256']:
            raise ValueError('source after SHA-256 mismatch')
        if any(pattern.search(result) for pattern in SECRET_PATTERNS.values()):
            raise ValueError('secret candidate rejected')
        prepared.append((name, result))
    return prepared


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan', type=Path, required=True)
    args = parser.parse_args()
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
    event = json.loads(Path(os.environ['GITHUB_EVENT_PATH']).read_text())
    repo = event['repository']
    pull = event['pull_request']
    if (repo['full_name'] != REPO or not repo['private'] or pull['number'] != 3
            or event['sender']['login'] != repo['owner']['login']
            or pull['head']['repo']['full_name'] != REPO
            or pull['head']['ref'] != 'chatgpt/fix-private-full-unit-20260905-r2'
            or pull['head']['sha'] != head):
        raise ValueError('source edit authorization mismatch')
    plan = json.loads(args.plan.read_text())
    prepared = prepare(ROOT, plan)
    rows = []
    for name, raw in prepared:
        expected_blob = hashlib.sha1(b'blob ' + str(len(raw)).encode() + b'\0' + raw).hexdigest()
        request = urllib.request.Request(
            'https://api.github.com/repos/' + REPO + '/git/blobs',
            data=json.dumps({'content': raw.decode(), 'encoding': 'utf-8'}).encode(),
            headers={'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
                     'Accept': 'application/vnd.github+json', 'Content-Type': 'application/json'},
            method='POST')
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                value = json.load(response)
        except (urllib.error.HTTPError, urllib.error.URLError):
            raise RuntimeError('Git blob preparation failed') from None
        if value.get('sha') != expected_blob:
            raise ValueError('prepared Git blob SHA mismatch')
        rows.append({'path': name, 'git_blob_sha': expected_blob, 'sha256': sha(raw)})
    out = ROOT / 'build/private-unit-source-blobs/result.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({'head': head, 'plan_sha256': sha(args.plan.read_bytes()),
                               'ref_changed': False, 'files': rows}, sort_keys=True, indent=2) + '\n')
    print('reviewed unreferenced source blobs prepared; no branch/commit/ref changed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
