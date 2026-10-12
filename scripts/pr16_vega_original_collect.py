#!/usr/bin/env python3
"""Issue19の原作ROMと181個別Wikiを一度だけ採取する。原本は変更しない。"""
from __future__ import annotations
import argparse
import datetime
import json
import os
from pathlib import Path
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.pr16_vega_original_baseline import (
    INDEX_URL, PENDING, TASK, capture_rom, identity, index_records, join_roster,
    original_from_archive, page_url, parse_tables, require, stable,
)


def fetch(url):
    url = page_url(url)
    request = urllib.request.Request(url, headers={'User-Agent': 'Vega-Original-Learnset-Audit/1.0 (source-only; one request/second)'})
    with urllib.request.urlopen(request, timeout=25) as response:
        require(page_url(response.geturl()) == url, 'Wiki転送先が変更された')
        raw = response.read(4000001)
        require(len(raw) <= 4000000, 'Wiki pageが上限超過')
        raw.decode('utf-8')
        return raw, {'url': url, 'fetched_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
                     'last_modified': response.headers.get('Last-Modified'), **identity(raw)}


def run(archive, output):
    require(not any(p.is_symlink() for p in (output, *output.parents)), 'output symlink禁止')
    output = output.resolve()
    require(output.is_relative_to(ROOT / '.local') and output != ROOT / '.local', '出力は専用.localだけ')
    output.mkdir(parents=True, exist_ok=False)
    source = output / 'source'; source.mkdir()
    tables = output / 'tables'; tables.mkdir()
    inputs = ('manifests/species_ids.csv', 'manifests/move_ids.csv', PENDING,
              'config/species_surface.json', 'config/species_port.json', 'config/move_port.json')
    locked = {}
    for name in inputs:
        raw = (ROOT / name).read_bytes()
        locked[name] = identity(raw)
        destination = output / 'repository' / name
        destination.parent.mkdir(parents=True, exist_ok=True); destination.write_bytes(raw)
    raw, meta = fetch(INDEX_URL)
    (source / '19.html').write_bytes(raw)
    index = index_records(parse_tables(raw))
    (output / 'index.json').write_bytes(stable(index))
    roster = join_roster((ROOT / inputs[0]).read_bytes(), json.loads((ROOT / PENDING).read_bytes()), index)
    (output / 'roster.json').write_bytes(stable(roster))
    config = json.loads((ROOT / 'config/github_private_environment.json').read_bytes())
    bound = next(a for a in config['archives'] if a['name'] == archive.name)
    move = json.loads((ROOT / 'config/move_port.json').read_bytes())
    rom = original_from_archive(archive, bound, move['vega'])
    observation = capture_rom(rom, roster, json.loads((ROOT / 'config/species_surface.json').read_bytes()))
    del rom
    (output / 'original_rom_tables.json').write_bytes(stable(observation))
    pages, failures = {'19': meta}, []
    for row in roster:
        page_id = row['url'].rsplit('/', 1)[1].split('.')[0]
        time.sleep(1)
        try:
            raw, metadata = fetch(row['url'])
            parsed = parse_tables(raw)
            require(parsed, 'Wiki個別ページに表がない')
            (source / (page_id + '.html')).write_bytes(raw)
            (tables / (page_id + '.json')).write_bytes(stable(parsed))
            pages[page_id] = metadata
        except (OSError, ValueError) as exc:
            failures.append({'species_key': row['species_key'], 'url': row['url'], 'error_type': type(exc).__name__})
        report = {'schema_version': 1, 'task': TASK, 'source_head': os.environ.get('GITHUB_SHA'),
                  'run_id': int(os.environ.get('GITHUB_RUN_ID', '0')), 'repository_inputs': locked,
                  'archive': {'name': archive.name, 'size': bound['size'], 'sha256': bound['sha256']},
                  'original_rom': observation['rom'], 'roster_count': len(roster),
                  'pages': pages, 'failures': failures, 'rom_changes': 0, 'new_native_runs': 0,
                  'official_baseline_reruns': 0, 'issue19_complete': False, 'release_ready': False}
        (output / 'capture.json').write_bytes(stable(report))
    require(not failures and len(pages) == 182, 'Wiki原本採取が未完。成功原本は保持する')
    print(json.dumps({'status': 'CAPTURED_NOT_ADJUDICATED', 'species': len(roster), 'pages': len(pages)}, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    run(args.archive, args.output)
