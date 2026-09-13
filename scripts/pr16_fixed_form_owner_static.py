#!/usr/bin/env python3
"""Read pinned native fixed-form owners; do not invent replacement-move policy.

No emulation, ROM edits, save writes, or acceptance promotion. Extract only
bounded UTF-8 source members from the existing hash-pinned private state input.
The private archive itself is never included in the output.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE_SUFFIXES = {'.c', '.h', '.s', '.ld', '.py', '.json'}
TOKENS = ('NECROZMA', 'Necrozma', 'SUNSTEELSTRIKE', 'SunsteelStrike', 'PHOTONGEYSER', 'PhotonGeyser', 'ZACIAN', 'ZAMAZENTA')


def need(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def identity(raw: bytes) -> dict:
    return dict(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def run(archive: Path, output: Path) -> dict:
    archive, output = archive.absolute(), output.absolute()
    need(not any(p.is_symlink() for p in (archive, *archive.parents, output, *output.parents)), 'symlink input/output')
    need(output.is_relative_to(ROOT / '.local') and output != ROOT / '.local' and not output.exists(), 'output must be a fresh dedicated .local directory')
    config = json.loads((ROOT / 'config/github_private_environment.json').read_bytes())
    bound = next(row for row in config['archives'] if row['name'] == 'pokemon-vega-private-env-v1-state.zip')
    raw_identity = identity(archive.read_bytes())
    need(raw_identity == {key: bound[key] for key in ('size', 'sha256')}, 'state archive identity differs')
    output.mkdir(parents=True)
    rows, payload = [], {}
    with zipfile.ZipFile(archive) as source:
        need(len(source.namelist()) == len(set(source.namelist())), 'duplicate archive members')
        for member in source.infolist():
            name = member.filename
            path = PurePosixPath(name)
            if not name.startswith('vendor/upstream/CFRU-JP/'):
                continue
            if path.suffix.lower() not in {'.c', '.h'} and not path.name.lower().startswith(('license', 'copying')):
                continue
            need(not path.is_absolute() and '..' not in path.parts and '\\' not in name, 'unsafe source member')
            need(not stat.S_ISLNK(member.external_attr >> 16) and member.file_size <= 3000000, 'unsafe or oversized source')
            data = source.read(member)
            text = data.decode('utf-8-sig')
            need(b'\0' not in data, 'nontext source')
            matches = [dict(line=index, text=line) for index, line in enumerate(text.splitlines(), 1) if any(token in line for token in TOKENS)]
            if matches or path.name.lower().startswith(('license', 'copying')):
                payload[name] = data
                rows.append(dict(path=name, origin='PINNED_STATE_SOURCE_MEMBER', **identity(data), matches=matches))
    tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=ROOT).decode().split('\0')
    for name in tracked:
        path = ROOT / name
        chosen = name.startswith(('overlays/modernization_p03_stage73_consumer_runtime/', 'overlays/collection_supply_v1/')) or name in (
            'tools/modernization_p03_stage73_runtime.py', 'config/modernization_p03_stage73_runtime.json',
            'scripts/build_collection_supply_v1.py', 'config/collection_supply_v1.json',
            'scripts/pr16_fixed_form_owner_static.py', '.github/workflows/pr16-fixed-form-owner-static.yml',
            'content/modernization/pr16_fixed_form_contract.json', 'content/modernization/pr16_fixed_form_acceptance.json',
            'content/modernization/p03_stage73_consumer_runtime_checkpoint.json',
        )
        if not chosen or path.suffix.lower() not in SOURCE_SUFFIXES and path.suffix != '.S':
            continue
        need(not path.is_symlink(), 'symlink tracked source')
        data = path.read_bytes(); text = data.decode('utf-8'); need(b'\0' not in data, 'nontext tracked source')
        payload[name] = data
        matches = [dict(line=index, text=line) for index, line in enumerate(text.splitlines(), 1) if any(token in line for token in TOKENS)]
        rows.append(dict(path=name, origin='TRACKED_CHECKOUT', **identity(data), matches=matches))
    need(len(payload) <= 100 and sum(map(len, payload.values())) <= 16000000, 'finite source budget exceeded')
    with zipfile.ZipFile(output / 'owner-sources.zip', 'w', zipfile.ZIP_DEFLATED) as target:
        for name, data in sorted(payload.items()):
            target.writestr(name, data)
    report = dict(schema_version=1, status='STATIC_OWNER_SOURCES_NOT_NATIVE_ACCEPTANCE', tested_head=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(), archive=raw_identity, sources=rows, source_zip=identity((output / 'owner-sources.zip').read_bytes()), new_emulator_runs=0, rom_changes=0, p03_fixed_form_gap_closed=False, release_ready=False)
    (output / 'owner-index.json').write_text(json.dumps(report, ensure_ascii=False, sort_keys=True, indent=2) + '\n')
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, default=ROOT / '.local/pr16-fixed-form-owner-static')
    args = parser.parse_args()
    print(json.dumps(run(args.archive, args.output), ensure_ascii=False))
