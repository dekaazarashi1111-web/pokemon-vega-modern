#!/usr/bin/env python3
"""Circus接続の固定source/link metadataを限定採取する。入場受入ではない。"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT/'.local/pr16-circus-source'
SELF = 'scripts/pr16_circus_source_probe.py'
SOURCE = 'overlays/circus_admission/circus_admission.c'
HEADER = 'overlays/circus_admission/circus_admission.h'
WORKFLOW = '.github/workflows/pr16-circus-source.yml'
SYMBOLS = {
    'VegaFacilityStateGet', 'VegaFacilityStateSet', 'VegaFacilityStateIsActive',
    'VegaConfigureNextFacility', 'VegaBattlePolicyPrepareFacilityBattle',
    'cfru_integration_pending_copy', 'cfru_integration_pending_facility_set',
    'cfru_integration_pending_facility_get', 'cfru_integration_pending_clear',
    'BattleSetup_StartTrainerBattle', 'sp072_LoadBattleCircusEffects',
    'GetCurrentBattleTowerStreak', 'GetBattleTowerStreak', 'Random', 'StringCopy',
    'SetSav1Weather', 'gBattleCircusFlags', 'gBattleCircusStreaks', 'gBitTable',
    'sBattleCircusEffectDescriptions', 'gSpecialVar_LastResult', 'gStringVarC',
}
UPSTREAM = (
    'vendor/upstream/CFRU-JP/src/frontier.c',
    'vendor/upstream/CFRU-JP/src/overworld.c',
    'vendor/upstream/CFRU-JP/src/end_battle.c',
    'vendor/upstream/CFRU-JP/include/new/frontier.h',
    'vendor/upstream/CFRU-JP/include/constants/battle.h',
    'vendor/upstream/CFRU-JP/BPRJ.ld',
)
TRACKED = (SELF, SOURCE, HEADER, WORKFLOW, 'tests/test_pr16_circus_admission.py',
    'overlays/cfru/rom_bridge.c', 'overlays/cfru/integration.c',
    'overlays/cfru/integration.h', 'overlays/cfru/runtime.c', 'overlays/cfru/runtime.h',
    'scripts/build_battle_core.py', 'config/battle_core.json',
    'config/github_private_environment.json', 'infra/toolchain_manifest.json')


def need(ok, message):
    if not ok:
        raise ValueError(message)


def identity(data):
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def stable(value):
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n').encode()


def text(data):
    need(len(data) <= 2_000_000 and b'\0' not in data, 'bounded text required')
    result = data.decode('utf-8-sig')
    need(not re.search(r'gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{60,}', result), 'secret-like text')
    return result


def symbol_rows(value, path='', depth=0):
    need(depth <= 40, 'metadata nesting bound')
    rows = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in SYMBOLS and isinstance(item, (int, str, dict)) and len(str(item)) < 1000:
                rows.append({'path': path+'/'+key, 'symbol': key, 'value': item})
            if key in ('name', 'symbol') and isinstance(item, str) and item in SYMBOLS:
                rows.append({'path': path, 'symbol': item,
                    'value': {k:v for k,v in value.items() if isinstance(v, (int, str, bool)) and len(str(v)) < 1000}})
            if isinstance(item, (list, dict)):
                rows.extend(symbol_rows(item, path+'/'+key, depth+1))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            if isinstance(item, (list, dict)):
                rows.extend(symbol_rows(item, path+'/'+str(index), depth+1))
    need(len(rows) <= 2000, 'metadata match bound')
    return rows


def run(archive):
    OUT.mkdir(parents=True, exist_ok=True)
    need(not any(p.is_symlink() for p in (OUT, *OUT.parents)), 'unsafe output')
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    need(head == os.environ['GITHUB_SHA'], 'fixed checkout differs')
    cfg = json.loads((ROOT/'config/github_private_environment.json').read_bytes())
    bound = next(a for a in cfg['archives'] if a['name']=='pokemon-vega-private-env-v1-state.zip')
    need(identity(archive.read_bytes()) == {k:bound[k] for k in ('size', 'sha256')}, 'pinned archive differs')
    sources, metadata, index = {}, {}, []
    def save(name, raw):
        text(raw)
        p = PurePosixPath(name)
        need(not p.is_absolute() and '..' not in p.parts and '\\' not in name, 'unsafe text path')
        target = OUT/'source'/name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(raw)
        return identity(raw)
    with zipfile.ZipFile(archive) as z:
        names = z.namelist()
        need(len(names) == len(set(names)), 'duplicate archive member')
        for name in UPSTREAM:
            sources[name] = save(name, z.read(name))
        for info in z.infolist():
            name = info.filename
            if not name.startswith(('generated/', 'reports/generated/')):
                continue
            if not re.search('battle|cfru|offset|symbol', name, re.I):
                continue
            if PurePosixPath(name).suffix not in ('.json', '.txt', '.map', '.ld'):
                continue
            index.append({'path': name, 'size': info.file_size})
            if info.file_size > 2_000_000 or PurePosixPath(name).suffix != '.json':
                continue
            raw = z.read(info)
            rows = symbol_rows(json.loads(text(raw)))
            if rows:
                metadata[name] = {'identity': save('metadata/'+name, raw), 'symbols': rows}
        need(len(index) <= 600 and len(metadata) <= 60, 'source metadata bound')
    for name in TRACKED:
        p = ROOT/name
        need(p.is_file() and not p.is_symlink(), 'tracked input missing or symlink: '+name)
        sources[name] = save(name, p.read_bytes())
    objects = []
    for index_number in (1, 2):
        obj = OUT/('admission-'+str(index_number)+'.o')
        command = ['arm-none-eabi-gcc', '-std=c11', '-Os', '-mthumb', '-mcpu=arm7tdmi',
            '-ffreestanding', '-fno-builtin', '-ffunction-sections', '-fdata-sections',
            '-fno-unwind-tables', '-fno-asynchronous-unwind-tables', '-Wall', '-Wextra',
            '-Werror', '-c', str(ROOT/SOURCE), '-o', str(obj)]
        proc = subprocess.run(command, capture_output=True)
        (OUT/('arm-'+str(index_number)+'.stderr')).write_bytes(proc.stderr)
        need(proc.returncode == 0, 'new ARM object compilation failed')
        objects.append(obj.read_bytes())
    need(objects[0] == objects[1], 'independent ARM objects differ')
    dis = subprocess.check_output(['arm-none-eabi-objdump', '-dr', str(OUT/'admission-1.o')], text=True)
    (OUT/'admission-disassembly.txt').write_text(dis.replace(str(OUT), 'circus-source'))
    report = {'schema_version': 1, 'classification': 'CIRCUS_PENDING_IMPLEMENTED_SOURCE_LINK_PENDING',
        'source_head': head, 'run_id': int(os.environ['GITHUB_RUN_ID']),
        'archive': {k:bound[k] for k in ('name','size','sha256')}, 'source_bindings': sources,
        'metadata_index': index, 'symbol_metadata': metadata, 'arm_object': identity(objects[0]),
        'independent_arm_compiles': 2, 'rom_changes': 0, 'new_emulator_processes': 0,
        'accepted_native_cases_replayed': 0, 'physical_admission_accepted': False, 'release_ready': False}
    (OUT/'report.json').write_bytes(stable(report))
    for p in OUT.glob('*.o'):
        p.unlink()
    subprocess.run(['git', 'diff', '--exit-code'], cwd=ROOT, check=True)
    print(json.dumps({k:report[k] for k in ('classification','source_head','run_id','arm_object','independent_arm_compiles','rom_changes')}, ensure_ascii=False))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--archive', type=Path, required=True)
    run(parser.parse_args().archive)
