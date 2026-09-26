#!/usr/bin/env python3
"""P08 Wiki用の読取専用入力解決。保存byteの復元は生成・受入の再実行ではない。"""
from __future__ import annotations
import csv
import hashlib
import io
import json
from pathlib import Path
import struct
import sys
import zlib
from typing import Any

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
BASE = 0x08000000
STATE = 'content/modernization/pr16_native_supply_resume_20260913.json'
TRANSFER = 'content/modernization/pr16_p08_candidate_transfer.json'
IMPACT = 'content/modernization/pr16_p08_candidate_impact.json'
REMAINING = 'content/modernization/p08_remaining_work.json'
CAPACITY = 'content/modernization/p04_capacity_allocation_manifest.json'
ROCKRUFF = 'config/modernization_rockruff_own_tempo_stage75.json'


def need(ok: Any, message: str) -> None:
    if not ok:
        raise ValueError(message)


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def identity(raw: bytes) -> dict:
    return {'size': len(raw), 'sha256': digest(raw), 'crc32': f'{zlib.crc32(raw):08X}'}


def stable(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + '\n').encode()


def strict(raw: bytes) -> Any:
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, 'JSONキー重複: ' + key)
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=lambda x: need(False, '非有限JSON値'))


class Inputs:
    """安全な相対pathから読み、使用したtext入力のhashを記録する。"""
    def __init__(self, root: Path = ROOT):
        self.root = root.resolve()
        self.bindings: dict[str, dict] = {}

    def path(self, name: str) -> Path:
        rel = Path(name)
        need(bool(name) and not rel.is_absolute() and '..' not in rel.parts and '\\' not in name,
             '入力pathが不正')
        path = self.root
        for part in rel.parts:
            path = path / part
            need(not path.is_symlink(), 'symlink入力は禁止: ' + name)
        need(path.resolve().is_relative_to(self.root), '入力がroot外')
        return path

    def raw(self, name: str) -> bytes:
        data = self.path(name).read_bytes()
        self.bindings[name] = {'size': len(data), 'sha256': digest(data)}
        return data

    def json(self, name: str) -> Any:
        return strict(self.raw(name))

    def csv(self, name: str) -> list[dict]:
        return list(csv.DictReader(io.StringIO(self.raw(name).decode('utf-8-sig'))))

    def jsonl(self, name: str) -> list[dict]:
        return [strict(line) for line in self.raw(name).splitlines() if line]


def selected_candidate(inputs: Inputs) -> dict:
    state = inputs.json(STATE)
    current = state['current_p08_candidate']
    expected = {key: current[key] for key in ('size', 'sha256', 'crc32')}
    need(current['native_transfer_complete'] is True, 'P08移送が未受入')
    transfer = inputs.json(TRANSFER)
    remaining = inputs.json(REMAINING)
    impact = inputs.json(IMPACT)
    for label, value in [('transfer', transfer['candidate']), ('impact', impact['candidate']),
                         ('remaining', remaining['p08_candidate_transfer']['candidate']),
                         ('resume', state['p08_candidate_transfer']['candidate'])]:
        need(all(value[k] == expected[k] for k in ('size', 'sha256')), label + '候補不一致')
    need(transfer['final_native_acceptance_complete'] is True, 'P08移送の完了記録なし')
    need(transfer['candidate_crc32'] == impact['candidate_crc32'] == expected['crc32'], '候補CRC不一致')
    return expected


def candidate_bytes(inputs: Inputs) -> bytes:
    """保存済み21層のbyteを前進適用するだけ。逆監査、ARM、mGBA、旧builderは呼ばない。"""
    import pr16_p08_impact as impact
    expected = selected_candidate(inputs)
    recipes = impact.load_model(inputs.root)
    raw = inputs.path(impact.ANCHOR_PATH).read_bytes()
    need(impact.saved.identity(raw) == impact.ANCHOR, '固定anchor不一致')
    for recipe in recipes:
        need(impact.saved.identity(raw) == recipe['parent'], '保存差分の親不一致')
        raw = impact.saved.patch(raw, recipe['patches'])
        need(impact.saved.identity(raw) == recipe['candidate'], '保存差分の出力不一致')
    need(identity(raw) == expected, '最終候補identity不一致')
    for name in ('scripts/pr16_saved_recipe.py', 'scripts/pr16_p08_impact.py',
                 impact.NORMAL, impact.GETTER):
        inputs.raw(name)
    return raw


def keyed(rows: list[dict], label: str) -> list[dict]:
    rows = sorted(rows, key=lambda row: row['id'])
    need([r['id'] for r in rows] == list(range(len(rows))), label + ' ID欠落/重複')
    need(len({r['key'] for r in rows}) == len(rows), label + ' stable key重複')
    need(all(isinstance(r['key'], str) and r['key'] for r in rows), label + ' stable key未設定')
    return rows


def registries(inputs: Inputs) -> dict[str, list[dict]]:
    result = {}
    for domain in ('species', 'move', 'ability', 'item'):
        result[domain] = [dict(row, id=int(row['id']), key=row[domain + '_key'], name=row['display_name'])
                          for row in inputs.csv(f'manifests/{domain}_ids.csv')]
    cap = inputs.json(CAPACITY)
    candidates = {r['record_key']: r for r in inputs.json('content/modernization/p04_candidate_manifest.json')['records']}
    for domain in ('species', 'ability', 'item'):
        reservation = cap['id_reservations']['species_form' if domain == 'species' else domain]
        need(len(result[domain]) == reservation['current_count'], domain + '予約元件数不一致')
        for row in reservation['rows']:
            key = row[domain + '_key']
            record = dict(row, key=key, name=key, evidence='GENERATED_CANONICAL')
            if domain == 'species':
                c = candidates[row['source_record_key']]
                base = next(r for r in result['species'] if r['key'] == row['source_species_key'])
                record.update(base_species_id=base['id'], form_key=c['identity_form_key'],
                              national_no=c['national_dex'], name=base['name']+'（'+c['name_en']+'）',
                              classification=c['classification'], candidate_record=c)
            result[domain].append(record)
        need(len(result[domain]) == reservation['new_count'], domain + '拡張件数不一致')
    rock = inputs.json(ROCKRUFF)['identity']
    result['species'].append({'id': rock['species_id'], 'key': rock['species_key'],
                             'name': result['species'][rock['normal_species_id']]['name']+'（マイペース）',
                             'form_key': rock['form_key'], 'classification': rock['classification'],
                             'base_species_id': rock['normal_species_id'], 'national_no': rock['national_dex']})
    for row in result['species']:
        row.setdefault('national_no', int(row.get('canonical_national_dex') or 0))
        row.setdefault('form_key', '')
        row.setdefault('base_species_id', row['id'])
    for domain, rows in result.items():
        result[domain] = keyed(rows, domain)
    return result


class Rom:
    """GBA table ABIの境界付きreader。すべての読み出しはimmutable bytesから行う。"""
    def __init__(self, raw: bytes):
        self.raw = raw
        self.tables: dict[str, dict] = {}

    def read(self, address: int, length: int) -> bytes:
        offset = address - BASE
        need(type(address) is int and type(length) is int and length >= 0
             and 0 <= offset <= len(self.raw)-length, 'ROM境界外: '+hex(address))
        return self.raw[offset:offset+length]

    def u16(self, address: int) -> int:
        return struct.unpack('<H', self.read(address, 2))[0]

    def u32(self, address: int) -> int:
        return struct.unpack('<I', self.read(address, 4))[0]

    def pointer(self, site: int) -> int:
        value = self.u32(BASE+site)
        self.read(value, 1)
        return value

    def table(self, name: str, site: int, count: int, stride: int) -> int:
        address = self.pointer(site)
        raw = self.read(address, count*stride)
        self.tables[name] = {'pointer_site': f'0x{BASE+site:08X}', 'address': f'0x{address:08X}',
                             'count': count, 'stride': stride, 'sha256': digest(raw),
                             'evidence': 'EXACT_CANDIDATE_ROM'}
        return address

    def indexed(self, index: int, values: int, species: int, move_count: int) -> list[int]:
        start, end = self.u16(index+species*2), self.u16(index+(species+1)*2)
        need(start <= end and end-start <= 1024, 'indexed route境界不正')
        result = [self.u16(values+i*2) for i in range(start, end)]
        need(all(0 < x < move_count for x in result), 'indexed move ID範囲外')
        return result

    def level(self, root: int, species: int, move_count: int) -> list[dict]:
        cursor = self.u32(root+species*4)
        result = []
        for order in range(256):
            move, level = struct.unpack('<HB', self.read(cursor+order*3, 3))
            if (move, level) == (0, 255):
                return result
            if move == 0:
                continue  # Native table padding; not a learnable MOVE_NONE row.
            need(0 < move < move_count and 0 <= level <= 100, f'level row不正: species={species} move={move} level={level}')
            result.append({'move_id': move, 'level': level, 'order': order})
        raise ValueError('level table終端なし')

    def eggs(self, root: int, species_count: int, move_count: int) -> dict[int, list[int]]:
        result = {i: [] for i in range(species_count)}
        active = None
        for index in range(50000):
            value = self.u16(root+index*2)
            if value == 65535:
                return result
            if value >= 20000:
                active = value-20000
                need(active in result, 'egg species範囲外')
            else:
                need(active is not None and 0 < value < move_count, 'egg move範囲外')
                result[active].append(value)
        raise ValueError('egg table終端なし')

    def lz_asset(self, address: int, expected_max: int = 8192) -> dict:
        """GBA LZ77をboundedに解凍しhashだけ返す。画像byteは出力しない。"""
        header = self.read(address, 4)
        need(header[0] == 0x10, 'GBA LZ77 header不正')
        size = int.from_bytes(header[1:], 'little')
        need(0 < size <= expected_max, '画像展開size範囲外')
        out = bytearray(); cursor = 4
        while len(out) < size:
            flags = self.read(address+cursor, 1)[0]; cursor += 1
            for bit in range(7, -1, -1):
                if len(out) >= size:
                    break
                if flags & (1 << bit):
                    a, b = self.read(address+cursor, 2); cursor += 2
                    length = (a >> 4)+3; distance = ((a & 15) << 8)+b+1
                    need(distance <= len(out) and len(out)+length <= size, 'LZ参照境界外')
                    for _ in range(length):
                        out.append(out[-distance])
                else:
                    out.extend(self.read(address+cursor, 1)); cursor += 1
                need(cursor <= expected_max*2+64, 'LZ入力上限超過')
        return {'pointer': f'0x{address:08X}', 'decoded_size': size, 'decoded_sha256': digest(bytes(out)),
                'stored_size': cursor, 'stored_sha256': digest(self.read(address, cursor)),
                'evidence': 'EXACT_CANDIDATE_ROM'}


def roots(inputs: Inputs, rom: Rom, ids: dict) -> dict[str, int]:
    cap = inputs.json(CAPACITY)
    capacity = {r['table_key']: r for r in cap['table_capacity']['fixed_tables']}
    consumers = cap['consumer_audit']['stage65_exact_literal_candidates']
    result = {}
    names = ('species_base_stats', 'species_front', 'species_back', 'species_palette',
             'species_shiny_palette', 'species_icon', 'species_icon_palette', 'species_front_coords',
             'species_back_coords', 'species_species_names', 'species_national_dex',
             'species_level_up_pointers', 'species_tmhm', 'species_tutor', 'evolution',
             'ability_names', 'ability_descriptions', 'item_data')
    for name in names:
        # 正本のprimary/最小literalを入口とし現候補のpointerを追う。旧table addressは使わない。
        site = min(consumers[name]['site_offsets'])
        domain = 'ability' if name.startswith('ability') else 'item' if name.startswith('item') else 'species'
        result[name] = rom.table(name, site, len(ids[domain]), capacity[name]['stride_bytes'])
    primary = cap['consumer_audit']['p01_verified_roots_on_active_stage']
    result['move_battle'] = rom.table('move_battle', min(primary['move_battle']['site_offsets']), len(ids['move']), 12)
    for name in ('egg_moves', 'tm_hm_move_catalog', 'tutor_move_catalog', 'move_names', 'move_descriptions', 'move_effects'):
        result[name] = rom.pointer(min(primary[name]['site_offsets']))
    return result


def base_rows(rom: Rom, address: int, ids: dict) -> list[dict]:
    result = []
    fields = ('hp','attack','defense','speed','sp_attack','sp_defense')
    for row in ids['species']:
        sid = row['id']; data = rom.read(address+sid*32, 32)
        stats = dict(zip(fields, data[:6])); stats['total'] = sum(stats.values())
        abilities = [struct.unpack_from('<H', data, pos)[0] for pos in (22,26,28)]
        held = list(struct.unpack_from('<HH', data, 12))
        need(all(a < len(ids['ability']) for a in abilities), 'ability参照範囲外')
        need(all(a < len(ids['item']) for a in held), 'item参照範囲外')
        ev = struct.unpack_from('<H', data, 10)[0]
        result.append({'id': sid, 'key': row['key'], 'name': row['name'], 'base_stats': stats,
                       'types': list(data[6:8]), 'ability_ids': abilities, 'capture_rate': data[8],
                       'ev_yield': {k:(ev >> (i*2)) & 3 for i,k in enumerate(fields)},
                       'held_item_ids': held, 'gender_ratio': data[16], 'egg_cycles': data[17],
                       'friendship': data[18], 'growth_id': data[19], 'egg_group_ids': list(data[20:22]),
                       'exp_yield': struct.unpack_from('<H',data,30)[0],
                       'row_sha256': digest(data), 'evidence': 'EXACT_CANDIDATE_ROM'})
    return result


def move_rows(rom: Rom, address: int, ids: dict) -> list[dict]:
    result = []
    fields = ('effect_id','power','type_id','accuracy','pp','secondary_percent','target_id',
              'priority','flags','z_power','category_id','z_effect')
    for row in ids['move']:
        data = rom.read(address+row['id']*12, 12)
        value = dict(zip(fields, data))
        if value['priority'] >= 128:
            value['priority'] -= 256
        result.append({'id': row['id'], 'key': row['key'], 'name': row['name'], **value,
                       'row_sha256': digest(data), 'evidence': 'EXACT_CANDIDATE_ROM'})
    return result
