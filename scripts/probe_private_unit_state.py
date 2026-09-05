#!/usr/bin/env python3
"""既知の非秘密hash・定数だけを抽出する（ROM/save本文は取得しない）。"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
HEX = re.compile(r'[0-9a-f]{64}')


def sha(path: Path) -> str:
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def main() -> int:
    from scripts import build_test_ready_save as builder
    config = builder._read_json(builder.DEFAULT_CONFIG)
    report_path = ROOT / config['output']['report']
    report = builder._read_json(report_path)
    current = builder._source_hashes()
    saved = report.get('source_hashes', {})
    sources = []
    for path, digest in sorted(current.items()):
        old = saved.get(path)
        if not HEX.fullmatch(digest) or not isinstance(old, str) or not HEX.fullmatch(old):
            raise ValueError('source hash is not a digest')
        sources.append({'path': path, 'published_sha256': old, 'current_sha256': digest})
    namespaces = {'status': report.get('status') == 'PASS',
                  'expected_output': report.get('output', {}).get('sha256') == 'f6bfdb107196ca22b012c1d12ee4bcdc8f5add309bbd3538447cd6e39c449bcb',
                  'determinism': report.get('determinism') == {'byte_identical': True, 'process_runs': 2},
                  'source_keys_match': set(saved) == set(current), 'sources': sources,
                  'report_sha256': sha(report_path)}
    wanted = {'nature_ids.csv', 'species_catalog.csv', 'trainer_changekit_final.json',
              'stage61_event_semantic_relocation.json', 'stage61_state_namespace_collision_audit.json'}
    archives = []
    for root in (ROOT / 'userfile', ROOT / '.local/github-private-environment/PRIVATE_INPUTS'):
        for path in sorted(root.rglob('*.zip')):
            if not zipfile.is_zipfile(path):
                continue
            with zipfile.ZipFile(path) as archive:
                members = []
                for info in archive.infolist():
                    name = Path(info.filename).name
                    if name in wanted:
                        members.append({'role': name, 'member_name_sha256': hashlib.sha256(info.filename.encode()).hexdigest(),
                                        'content_sha256': hashlib.sha256(archive.read(info)).hexdigest(), 'size': info.file_size})
                if members:
                    archives.append({'archive_sha256': sha(path), 'members': members})
    output = {'head_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip(),
              'stage60_fixture': namespaces, 'nested_sources': archives}
    path = ROOT / 'build/private-unit-focus/state-probe.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
