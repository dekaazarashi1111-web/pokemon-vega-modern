#!/usr/bin/env python3
"""Read exact candidate tables and map-rooted scripts, never claim native success.

The ScriptWalker stops at unknown instructions. No byte-pattern match can become
an entrance proof, and absence in this bounded graph cannot prove no entrance.
"""
from pathlib import Path, PurePosixPath
import hashlib
import json
import struct
import sys
import zipfile
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_repaired_acceptance as repaired
from tools.t02.rom_inventory import RomImage, ScriptWalker
from tools.stage57_debug_suite import _collect_contactable_roots
LEVEL_SCOPE = {10, 11, 12, 13, 203, 324, 364, 608, 719, 724, 727, 503, 411, 957, 497, 787, 1526}


def restore_map_inputs():
    """Restore only fixed catalogue JSON, never ROM, save or arbitrary paths."""
    name = 'pokemon-vega-private-env-v1-state.zip'
    cfg = json.loads((ROOT / 'config/github_private_environment.json').read_text())
    expected = next(a for a in cfg['archives'] if a['name'] == name)
    archive = ROOT / '.local/pr16-inputs' / name
    raw = archive.read_bytes()
    repaired.need(len(raw) == expected['size'] and hashlib.sha256(raw).hexdigest() == expected['sha256'], 'state archive identity differs')
    bindings = {}
    with zipfile.ZipFile(archive) as z:
        selected = [n for n in z.namelist() if n == 'reports/generated/id_inventory.json' or
                    n.startswith('generated/maps/kanto/') and n.endswith('.json')]
        repaired.need(len(selected) == len(set(selected)) and len(selected) == 254, 'fixed map catalogue member set differs')
        for name in selected:
            path = PurePosixPath(name)
            repaired.need(not path.is_absolute() and '..' not in path.parts, 'unsafe catalogue path')
            data = z.read(name); json.loads(data)
            target = ROOT / name
            repaired.need(not any(p.is_symlink() for p in (target, *target.parents)), 'symlink catalogue target')
            if target.exists():
                repaired.need(target.read_bytes() == data, 'existing catalogue differs: ' + name)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(data); target.chmod(0o444)
            bindings[name] = repaired.identity(data)
    return {'archive': repaired.identity(raw), 'members': bindings}


def pools(raw):
    layer = repaired.layer
    # Reserved/unpopulated species are not silently decoded as live level rows.
    # Egg/shared/reminder indices are read for all species; level rows are scoped.
    tables = layer.source.RomTables(raw, layer.COUNT, selected_species=LEVEL_SCOPE)
    symbols = json.loads((ROOT / 'generated/runtime/modernization_p03_stage73_consumer_runtime_symbols.json').read_text())['symbols']
    index = int(symbols['Stage73_ExactEggIndex']['address'], 16) - layer.BASE
    moves = int(symbols['Stage73_ExactEggMoves']['address'], 16) - layer.BASE
    stats = struct.unpack_from('<I', raw, 0x1bc)[0] - layer.BASE
    pp = struct.unpack_from('<I', raw, 0x1cc)[0] - layer.BASE
    rows = {}
    for sid in range(layer.COUNT):
        shared = layer.indexed(raw, layer.SHARED_INDEX, layer.SHARED_MOVES, sid)
        exact = layer.indexed(raw, index, moves, sid) if sid in layer.EXACT_SPECIES else None
        if exact is not None and sid == 364:
            exact += [461, 464, 357]
        reminder = layer.indexed(raw, layer.REMINDER_INDEX, layer.REMINDER_MOVES, sid)
        if not shared and not reminder and sid not in LEVEL_SCOPE:
            continue
        at = stats + sid * 32
        rows[sid] = {'level': tables.level.get(sid), 'raw_egg': tables.egg.get(sid, []),
                     'exact_egg': exact, 'shared': shared, 'reminder': reminder,
                     'shared_not_exact': [m for m in shared if m not in exact] if exact is not None else None,
                     'stats': list(raw[at:at+32])}
    return {'species': rows, 'level_scope': sorted(LEVEL_SCOPE),
            'canonical_pp': {m: raw[pp+12*m+4] for m in range(1, 1201)},
            'note': 'Non-exact species raw_egg is NOT assumed to equal the original ancestral GetAllEggMoves pool.'}


class ReceiverWalker(ScriptWalker):
    def _decode_refs(self, address, opcode, size):
        refs, edges = super()._decode_refs(address, opcode, size)
        if opcode in (0x23, 0x24):
            refs.append(self._reference('native', self.rom.u32(address+1), 'call', address, opcode))
        return refs, edges


def receivers(raw):
    inputs = restore_map_inputs()
    rom = RomImage('PR16 frozen repaired candidate', raw)
    roots, counts = _collect_contactable_roots(rom)
    walker = ReceiverWalker(rom)
    for root in roots:
        walker.add_root(root)
    graph = walker.walk()
    selected = [r for r in graph['references'] if
                r['category'] == 'var' and r['value'] == 0x403A or
                r['category'] == 'special' and r['value'] == 0x72 or
                r['category'] == 'native' or
                r['category'] == 'item' and r['value'] in (580, 1016, 1012, 1031, 1029, 1014, 1035)]
    addresses = {r['script_address'] for r in selected}
    return {'status': 'ROOTED_STATIC_CANDIDATES_NOT_PHYSICAL_ADMISSION',
            'catalogue_inputs': inputs, 'root_counts': dict(counts), 'root_count': len(roots),
            'visited_scripts': graph['visited_script_count'],
            'references': selected, 'diagnostics': graph['diagnostics'],
            'nodes': [n for n in graph['nodes'] if n['address'] in addresses],
            'limitations': ['native calls are not recursively disassembled',
                           'unknown command paths stop, never resynchronize',
                           '0x403A and special 0x72 are candidates, not sufficient entrance proof',
                           'map/progress fixtures or flag writes do not count as physical admission']}


def wild(raw):
    rom = RomImage('PR16', raw)
    # Stage60 layout uses tagged pointers at all three pointer levels.
    root = rom.u32(0x0808257C) & ~1
    rows = []
    for i in range(2048):
        at = root + 20*i
        group, number = rom.u8(at), rom.u8(at+1)
        if (group, number) == (255, 255):
            return {'root': root, 'headers': rows}
        row = {'group': group, 'map': number, 'tables': {}}
        for j, (method, count) in enumerate((('land', 12), ('water', 5), ('rock', 5), ('fishing', 10))):
            info = rom.u32(at + 4 + 4*j) & ~1
            if not info:
                continue
            slots = rom.u32(info+4) & ~1
            row['tables'][method] = {'rate': rom.u8(info), 'slots': [
                {'min': rom.u8(slots+4*k), 'max': rom.u8(slots+4*k+1), 'species': rom.u16(slots+4*k+2)}
                for k in range(count)]}
        rows.append(row)
    raise ValueError('unterminated rooted wild headers')


def run():
    out = ROOT / '.local/pr16-receiver-audit'; out.mkdir(parents=True, exist_ok=True)
    raw = repaired.layer.source.checked(ROOT / repaired.ROM, repaired.ROM_SHA)
    report = {'status': 'EXACT_INPUT_AUDIT_NOT_NATIVE_ACCEPTANCE', 'candidate': repaired.identity(raw),
              'emulator_runs': 0, 'rom_changed': False, 'release_ready': False}
    for label, function in (('pools', pools), ('receivers', receivers), ('wild', wild)):
        try:
            value = function(raw)
            (out / (label+'.json')).write_bytes(repaired.stable(value))
            report[label] = {'status': 'AUDITED', 'output': repaired.identity((out / (label+'.json')).read_bytes())}
        except (ValueError, RuntimeError, OSError, KeyError, struct.error) as error:
            report[label] = {'status': 'INCOMPLETE', 'error': str(error)}
    (out / 'result.json').write_bytes(repaired.stable(report))
    repaired.layer.source.checked(ROOT / repaired.ROM, repaired.ROM_SHA)
    print(json.dumps(report, sort_keys=True))
    return report

if __name__ == '__main__':
    run()
