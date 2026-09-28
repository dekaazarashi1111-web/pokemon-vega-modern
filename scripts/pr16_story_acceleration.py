#!/usr/bin/env python3
"""Save14を保存したまま、キー/現候補ABIから分離fixtureの入力を作る。"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[1]
PLAN = 'content/modernization/pr16_story_acceleration_plan.json'
CHECKPOINT = 'content/modernization/pr16_story_save14_checkpoint.json'
EVOLUTION = 'content/modernization/p02_evolution_contract.json'
CHARMAP = 'content/modernization/pr16_candidate_wiki_source_model.json'
ROM_BASE = 0x08000000


def need(value, message):
    if not value:
        raise ValueError(message)


def identity(raw):
    return {'sha256': hashlib.sha256(raw).hexdigest(), 'size': len(raw)}


def read_json(root, path):
    return json.loads((root / path).read_text(encoding='utf-8'))


def registry(root, kind):
    with (root / f'manifests/{kind}_ids.csv').open(encoding='utf-8', newline='') as f:
        rows = list(csv.DictReader(f))
    need(rows and len({r[kind + '_key'] for r in rows}) == len(rows), 'duplicate registry key')
    need(len({r['id'] for r in rows}) == len(rows), 'duplicate registry ID')
    return rows


def unique(rows, field, key):
    found = [r for r in rows if r[field] == key]
    need(len(found) == 1, 'unresolved or ambiguous key: ' + key)
    return found[0]


def resolve_move(rows, key):
    """計画の区切り差だけを許す。類似名・数値IDへのfallbackは禁止。"""
    need(bool(re.fullmatch(r'MOVE_[A-Z0-9_]+', key)), 'invalid move symbol')
    matches = [r for r in rows if r['cfru_symbol'].replace('_', '') == key.replace('_', '')]
    need(len(matches) == 1, 'unresolved or ambiguous move: ' + key)
    return matches[0]


def rom_bytes(raw, address, size):
    at = address - ROM_BASE
    need(type(address) is int and 0 <= at <= len(raw) - size, 'ROM address bounds')
    return raw[at:at + size]


def pointer(raw, site):
    value = struct.unpack_from('<I', raw, site)[0]
    need(value % 4 == 0, 'unaligned table')
    rom_bytes(raw, value, 4)
    return value


def decode_name(raw, chart):
    need(255 in raw, 'item name without terminator')
    return ''.join(chart[str(b)] for b in raw[:raw.index(255)])


def audit(root, rom, save):
    plan = read_json(root, PLAN)
    cp = read_json(root, CHECKPOINT)
    need(identity(rom) == cp['candidate'], 'not the accepted Save14 candidate')
    need(identity(save) == cp['output_save'], 'not the immutable Save14 input')
    species, moves, items = (registry(root, k) for k in ('species', 'move', 'item'))
    chart = read_json(root, CHARMAP)['charmap']
    roots = {'base_stats': pointer(rom, 0x1bc), 'moves': pointer(rom, 0x1cc),
             'items': pointer(rom, 0x1c8)}
    changes = []

    def mon(p):
        r = unique(species, 'species_key', p['species_key'])
        sid = int(r['id'])
        hint = p.get('current_canonical_id')
        if hint is not None and hint != sid:
            changes.append({'key': p['species_key'], 'plan_hint': hint, 'resolved_id': sid})
        b = rom_bytes(rom, roots['base_stats'] + 32 * sid, 32)
        need(all(b[:6]) and b[19] < 6, 'invalid species base stats')
        result = {'key': p['species_key'], 'id': sid, 'name': r['display_name'],
                  'base_stats': list(b[:6]), 'growth': b[19], 'base_exp': struct.unpack_from('<H', b, 30)[0],
                  'abilities': [struct.unpack_from('<H', b, n)[0] for n in (22, 26, 28)],
                  'row': identity(b), 'moves': []}
        for q in p.get('moves', []):
            row = resolve_move(moves, q['key'])
            mid = int(row['id'])
            mb = rom_bytes(rom, roots['moves'] + 12 * mid, 12)
            need(0 < mb[4] <= 64, 'move has no usable base PP')
            result['moves'].append({'plan_key': q['key'], 'key': row['move_key'],
                                    'symbol': row['cfru_symbol'], 'id': mid, 'pp': mb[4], 'row': identity(mb)})
        return result

    party = [mon(p) for p in plan['story_fast']['party']]
    progression = mon(dict(plan['progression'], species_key=plan['progression']['primary_soak_species_key']))
    opponents = [mon(p) for p in plan['progression']['opponent_ladder']]
    evo = read_json(root, EVOLUTION)['current_table']['rows']
    rows = [r for r in evo if r['source']['species_key'] == progression['key'] and r['method']['key'] == 'EVO_LEVEL']
    need(len(rows) == 1, 'Axew evolution not unique')
    e = rows[0]
    target = unique(species, 'species_key', e['target']['species_key'])
    need(e['source']['canonical_id'] == progression['id'] and e['target']['canonical_id'] == int(target['id']), 'evolution registry mismatch')
    expected = (4, e['condition']['parameter']['value'], int(target['id']), 0)
    eb = rom_bytes(rom, e['layout']['runtime_address'], 8)
    need(struct.unpack('<HHHH', eb) == expected, 'candidate evolution row differs')
    need(progression['growth'] == 5 and 2 <= expected[1] <= 100, 'first slice requires the bound slow growth class')
    threshold = expected[1] ** 3 * 5 // 4
    # 残存表もあるためbyte一致をconsumer同定とは主張しない。native CreateMonで閾値を追加照合する。
    pattern = struct.pack('<99I', *(n ** 3 * 5 // 4 for n in range(2, 101)))
    positions = []
    start = 0
    while True:
        at = rom.find(pattern, start)
        if at < 0:
            break
        need(at >= 8, 'growth table prefix bounds')
        positions.append(at - 8)
        start = at + 1
    need(positions, 'candidate lacks the expected complete slow growth sequence')
    progression['evolution'] = {'level': expected[1], 'target_id': expected[2], 'target_key': target['species_key'],
                                'threshold_exp': threshold, 'initial_exp': threshold - 1,
                                'row_address': e['layout']['runtime_address'], 'row': identity(eb),
                                'growth_sequence_matches': positions, 'native_threshold_readback_required': True}
    item_results = []
    for key in ('WISE_GLASSES', 'MUSCLE_BAND', 'SMOKE_BALL', 'LUCKY_EGG', 'MAX_REPEL', 'FULL_RESTORE', 'MAX_ELIXIR', 'ESCAPE_ROPE'):
        row = unique(items, 'item_key', 'ITEM_KEY_' + key)
        iid = int(row['id'])
        b = rom_bytes(rom, roots['items'] + 40 * iid, 40)
        need(struct.unpack_from('<H', b, 10)[0] == iid, 'item ABI ID mismatch')
        need(decode_name(b[:10], chart) == row['display_name'], 'item ABI name mismatch')
        need(b[22] == 1 and row['pocket'] == 'POCKET_ITEMS', 'only ordinary item pocket allowed')
        if row['hold_effect_key'].startswith('VEGA_HOLD_EFFECT_'):
            need(b[14] == int(row['hold_effect_key'].rsplit('_', 1)[1]), 'Vega held effect ABI mismatch')
        item_results.append({'key': row['item_key'], 'id': iid, 'name': row['display_name'], 'row': identity(b),
                             'held_effect': b[14], 'parameter': b[15], 'runtime_effect_accepted': False})
    source_paths = [PLAN, CHECKPOINT, EVOLUTION, CHARMAP] + [f'manifests/{k}_ids.csv' for k in ('species', 'move', 'item')]
    return {'schema_version': 1, 'status': 'PASS_SOURCE_ABI_ONLY', 'candidate': identity(rom), 'source_save': identity(save),
            'source_bindings': {p: identity((root / p).read_bytes()) for p in source_paths}, 'roots': roots,
            'plan_hint_corrections': changes, 'story_party': party, 'progression': progression, 'opponents': opponents,
            'items': item_results, 'utility_moves_initially_installed': False, 'accepted_case_reruns': 0,
            'rom_changes': 0, 'release_ready': False, 'native_acceptance': False}


def prepare(root, rom_path, save_path, output):
    rom, save = rom_path.read_bytes(), save_path.read_bytes()
    result = audit(root, rom, save)
    # 全検証が済むまで出力を作らず、既存作業結果も上書きしない。
    output.mkdir(parents=True, exist_ok=False)
    for lane in ('story-fast', 'progression'):
        (output / (lane + '.srm')).write_bytes(save)
    (output / 'abi.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--save', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    data = prepare(ROOT, args.rom, args.save, args.output)
    print(json.dumps({'status': data['status'], 'plan_hint_corrections': data['plan_hint_corrections']}, ensure_ascii=False))
