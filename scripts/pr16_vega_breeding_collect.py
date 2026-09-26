#!/usr/bin/env python3
"""不足していた固定Vegaの進化表/孵化consumerだけを読み取る。Wiki/native再実行なし。"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.pr16_vega_original_baseline import OriginalRom, original_from_archive, identity, stable, require


def collect(archive: Path, output: Path) -> None:
    require(not any(p.is_symlink() for p in (output, *output.parents)), 'output symlink禁止')
    require(output.resolve().is_relative_to(ROOT / '.local'), '出力は.local限定')
    output.mkdir(parents=True, exist_ok=False)
    lock = json.loads((ROOT / 'content/modernization/pr16_vega_original_evidence/source_lock.json').read_bytes())
    expected = dict(lock['archive'])
    require(archive.name == expected['name'], '固定archive名不一致')
    before = (archive.stat().st_size, archive.stat().st_mtime_ns)
    raw = original_from_archive(archive, expected, {'rom_size': lock['rom']['size'], 'rom_sha256': lock['rom']['sha256']})
    rom = OriginalRom(raw)
    surface = json.loads((ROOT / 'config/species_surface.json').read_bytes())
    sites = [surface['pointer_sites']['evolution'], 272044, 272424, 282464, 850408]
    roots = {str(site): rom.pointer(site) for site in sites}
    require(len(set(roots.values())) == 1, '進化consumer root不一致')
    evolution_root = next(iter(roots.values()))
    require(evolution_root == 0x0821615C, '進化rootが既存ABIと相違')
    table = rom.read(evolution_root, 412 * 40)
    evolutions = []
    empty = 0
    for species in range(412):
        for slot in range(5):
            words = struct.unpack_from('<4H', table, species * 40 + slot * 8)
            if not any(words):
                empty += 1
                continue
            require(0 <= words[2] < 412, '進化先が原作範囲外')
            evolutions.append({'species_id': species, 'slot': slot, 'method': words[0], 'parameter': words[1],
                               'target_species_id': words[2], 'padding': words[3],
                               'source_offset': evolution_root - 0x08000000 + species * 40 + slot * 8})
    egg_sites = (0x45214, 0x4528C)
    egg_roots = {str(site): rom.pointer(site) for site in egg_sites}
    require(len(set(egg_roots.values())) == 1, '直接egg consumer root不一致')
    eggs = rom.eggs(next(iter(egg_roots.values())))
    start, end = 0x44F34, 0x45340
    span = raw[start:end]
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / 'consumer.bin'
        path.write_bytes(span)
        disassembly = subprocess.check_output(['arm-none-eabi-objdump', '-D', '-b', 'binary', '-m', 'arm',
                                               '-M', 'force-thumb', '--adjust-vma=' + hex(0x08000000 + start), str(path)])
    # tmp絶対pathを証拠へ残さない。
    lines = disassembly.decode().splitlines()
    disassembly = ('\n'.join(line for line in lines if 'file format' not in line) + '\n').encode()
    (output / 'consumer-disassembly.txt').write_bytes(disassembly)
    report = {'schema_version': 1, 'scope': 'FROZEN_VEGA_EVOLUTION_AND_EGG_CONSUMER_READONLY',
              'source_head': os.environ.get('GITHUB_SHA'), 'run_id': int(os.environ.get('GITHUB_RUN_ID', '0')),
              'rom_identity': identity(raw), 'archive_identity': expected,
              'evolution': {'pointer_sites': roots, 'root': evolution_root, 'species_count': 412,
                            'species_stride': 40, 'slots': 5, 'slot_stride': 8, 'identity': identity(table),
                            'empty_slots': empty, 'rows': evolutions},
              'direct_egg': {'pointer_sites': egg_roots, 'rows_by_species': eggs},
              'consumer_span': {'start_offset': start, 'end_offset': end, **identity(span), 'hex': span.hex()},
              'disassembly_identity': identity(disassembly),
              'source_identity': {name: identity((ROOT / name).read_bytes()) for name in
                  ('scripts/pr16_vega_breeding_collect.py', 'tools/pr16_vega_original_baseline.py',
                   'config/species_surface.json', 'content/modernization/pr16_vega_original_evidence/source_lock.json')},
              'wiki_pages_fetched': 0, 'official_baseline_reruns': 0, 'accepted_native_reruns': 0,
              'new_native_runs': 0, 'rom_changes': 0, 'runtime_applied': False}
    require(before == (archive.stat().st_size, archive.stat().st_mtime_ns), 'archive変更禁止')
    (output / 'original-breeding.json').write_bytes(stable(report))
    print(json.dumps({'status': 'CAPTURED_MISSING_CONSUMER_SCOPE_ONLY', 'evolution_rows': len(evolutions),
                      'egg_species': len(eggs), 'wiki_pages_fetched': 0, 'rom_changes': 0}, sort_keys=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--archive', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    collect(args.archive, args.output)
