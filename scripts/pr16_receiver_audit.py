#!/usr/bin/env python3
"""Read exact candidate tables and map-rooted scripts, never claim native success.

The ScriptWalker stops at unknown instructions. No byte-pattern match can become
an entrance proof, and absence in this bounded graph cannot prove no entrance.
"""
from pathlib import Path
import json
import struct
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_repaired_acceptance as repaired
from tools.t02.rom_inventory import RomImage, ScriptWalker
from tools.stage57_debug_suite import _collect_contactable_roots


def pools(raw):
    layer = repaired.layer
    tables = layer.source.RomTables(raw, layer.COUNT, selected_species=set(range(layer.COUNT)))
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
        if not shared and not reminder and sid not in (503, 411, 957, 497, 787, 1526):
            continue
        at = stats + sid * 32
        rows[sid] = {'level': tables.level[sid], 'raw_egg': tables.egg.get(sid, []),
                     'exact_egg': exact, 'shared': shared, 'reminder': reminder,
                     'shared_not_exact': [m for m in shared if m not in exact] if exact is not None else None,
                     'stats': list(raw[at:at+32])}
    return {'species': rows, 'canonical_pp': {m: raw[pp+12*m+4] for m in range(1, 1201)},
            'note': 'Non-exact species raw_egg is NOT assumed to equal the original ancestral GetAllEggMoves pool.'}


class ReceiverWalker(ScriptWalker):
    def _decode_refs(self, address, opcode, size):
        refs, edges = super()._decode_refs(address, opcode, size)
        if opcode in (0x23, 0x24):
            refs.append(self._reference('native', self.rom.u32(address+1), 'call', address, opcode))
        return refs, edges


def receivers(raw):
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
            'root_counts': dict(counts), 'root_count': len(roots),
            'visited_scripts': graph['visited_script_count'],
            'references': selected, 'diagnostics': graph['diagnostics'],
            'nodes': [n for n in graph['nodes'] if n['address'] in addresses],
            'limitations': ['native calls are not recursively disassembled',
                           'unknown command paths stop, never resynchronize',
                           '0x403A and special 0x72 are candidates, not sufficient entrance proof',
                           'map/progress fixtures or flag writes do not count as physical admission']}


def wild(raw):
    rom = RomImage('PR16', raw)
    root = rom.u32(0x0808257C)
    rows = []
    for i in range(2048):
        at = root + 20*i
        group, number = rom.u8(at), rom.u8(at+1)
        if (group, number) == (255, 255):
            return {'root': root, 'headers': rows}
        row = {'group': group, 'map': number, 'tables': {}}
        for j, (method, count) in enumerate((('land', 12), ('water', 5), ('rock', 5), ('fishing', 10))):
            info = rom.u32(at + 4 + 4*j)
            if not info:
                continue
            slots = rom.u32(info+4)
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
