#!/usr/bin/env python3
"""Bounded ROM map graph for a physical purchased-gear route, not acceptance.

No candidate, save, prior evidence or current acceptance view is modified.
Invalid edges remain explicit; a missing decoded route never proves absence.
"""
from collections import deque
import hashlib
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
sys.path.insert(0, str(ROOT))
import pr16_shop_display_repair as repair
import pr16_p05_root_diagnostics as roots
import pr16_capture_geometry as geometry
from tools.t02.rom_inventory import RomImage

SHA = 'e630f7f199194fb4b531ff3a561da866902aea200770a832aec5c276e1636267'
OUT = ROOT / '.local/pr16-gear-route-probe'


def inspect(raw, max_depth=3, limit=80):
    if len(raw) != 33554432 or hashlib.sha256(raw).hexdigest() != SHA:
        raise ValueError('purchased-gear candidate identity differs')
    rom = RomImage('shop display repaired candidate', raw)
    pending = deque([(96, 5, 0)])
    seen, maps, errors = set(), [], []
    while pending and len(seen) < limit:
        group, number, depth = pending.popleft()
        if (group, number) in seen:
            continue
        seen.add((group, number))
        try:
            entry = roots.map_entry(rom, group, number)
            entry['depth'] = depth
            header = entry['header']
            pointer = rom.u32(header + 12)
            connections = []
            if pointer:
                count, table = rom.u32(pointer), rom.u32(pointer + 4)
                if not 0 <= count <= 32:
                    raise ValueError('connection count outside bound')
                for i in range(count):
                    at = table + 12 * i
                    connections.append(dict(direction=rom.u32(at), offset=rom.s32(at + 4),
                                            target_group=rom.u8(at + 8), target_map=rom.u8(at + 9)))
            entry['connections'] = connections
            try:
                entry['geometry'] = geometry.geometry(raw, group, number)
            except (ValueError, KeyError, struct.error) as exc:
                entry['geometry_error'] = str(exc)
            maps.append(entry)
            if depth < max_depth:
                for edge in entry['warps'] + connections:
                    target = edge['target_group'], edge['target_map']
                    if 255 not in target:
                        pending.append((*target, depth + 1))
        except (ValueError, KeyError, struct.error) as exc:
            errors.append(dict(group=group, map=number, depth=depth, error=str(exc)))
    wild = roots.wild_catalogue(raw)
    reachable = {(m['group'], m['map']) for m in maps}
    tables = [r for r in wild['headers'] if (r['group'], r['map']) in reachable]
    return dict(schema_version=1, status='STATIC_ROUTE_PROBE_NOT_NATIVE_ACCEPTANCE',
                candidate=dict(size=len(raw), sha256=SHA), start=[96, 5], max_depth=max_depth,
                map_limit=limit, queue_remaining=len(pending), maps=maps, errors=errors,
                reachable_wild_tables=tables, wild_diagnostics=wild['diagnostics'],
                no_match_proves_absence=False, new_emulator_runs=0,
                gear_to_battle_accepted=False, full_p05_acceptance=False, release_ready=False)


def run():
    if any(p.is_symlink() for p in (OUT, *OUT.parents)):
        raise ValueError('unsafe route probe output')
    OUT.mkdir(parents=True, exist_ok=True)
    recipe = repair.run()
    raw = (repair.OUTPUT / 'candidate.gba').read_bytes()
    report = inspect(raw)
    (OUT / 'route-graph.json').write_text(json.dumps(report, sort_keys=True, indent=2) + '\n')
    (OUT / 'candidate.json').write_text(json.dumps(recipe, sort_keys=True, indent=2) + '\n')
    print(json.dumps({k: report[k] for k in ('status', 'candidate', 'queue_remaining', 'new_emulator_runs', 'release_ready')}))
    print(json.dumps({'maps': [[m['group'], m['map']] for m in report['maps']], 'errors': report['errors']}))
    return report


if __name__ == '__main__':
    run()
