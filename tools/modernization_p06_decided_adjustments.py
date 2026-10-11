"""回収した既決2種の採用差分を、固定Stage82から別候補へ決定的に生成する。"""
from __future__ import annotations
import csv
import hashlib
import json
from pathlib import Path
import struct
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = 'content/modernization/p06_decided_adjustments.json'
PARENT_SHA = 'e9dcb375168c92cb4390aaf390b8278dbf08867dd7dc3b834561799ae021710d'
CANDIDATE_SHA = '09e9d8cf085d175299b58e93347e3beb2467c3c09016130f7d35ce033fa50096'
OFFSETS = {'ability.normal_1': (22, 2), 'ability.normal_2': (26, 2), 'base_stat.attack': (1, 1)}


def require(ok: bool, text: str) -> None:
    if not ok:
        raise ValueError(text)


def strict_json(raw: bytes) -> Any:
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, 'duplicate JSON key: '+key)
            out[key] = value
        return out
    def constant(text):
        raise ValueError('nonfinite JSON: '+text)
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=constant)


def identity(data: bytes) -> dict:
    return {'size': len(data), 'sha256': hashlib.sha256(data).hexdigest()}


def safe_read(root: Path, name: str) -> bytes:
    p = Path(name)
    require(not p.is_absolute() and '..' not in p.parts, 'unsafe source path')
    q = root
    for part in p.parts:
        q /= part
        require(not q.is_symlink(), 'symlink source')
    q.resolve().relative_to(root.resolve())
    return q.read_bytes()


def manifest(root: Path, name: str, key: str) -> dict:
    rows = list(csv.DictReader(safe_read(root, name).decode('utf-8').splitlines()))
    require(bool(rows), 'empty manifest')
    require(len({x[key] for x in rows}) == len(rows), 'duplicate manifest key')
    require(len({x['id'] for x in rows}) == len(rows), 'duplicate manifest ID')
    return {x[key]: x for x in rows}


def specification(root: Path = ROOT) -> dict:
    c = strict_json(safe_read(root, CONTRACT))
    require(type(c) is dict and c.get('schema_version') == 1, 'adoption schema')
    a = c['adoption']
    require(a['explicit_species_adjustment_spec_received'] is True and a['runtime_patch_authorized'] is True,
            'runtime delta not authorized')
    require(type(a['adopted_delta_count']) is int and a['adopted_delta_count'] == 2,
            'only the two recovered decisions are adopted')
    require(type(a['field_change_count']) is int and a['field_change_count'] == 3, 'only three fields adopted')
    require(len(a['records']) == 2, 'adoption record count')
    for s in c['sources'].values():
        data = safe_read(root, s['path'])
        require(identity(data) == {k:s[k] for k in ('size','sha256')}, 'source hash/size differs')
        require(s['adoption_section'] in data.decode('utf-8'), 'decision section missing')
    history = c['historical_contract']
    require(identity(safe_read(root, history['path']))['sha256'] == history['sha256'], 'historical P06 changed')
    require(c['policy']['full_p06_acceptance'] is False and c['policy']['release_ready'] is False,
            'narrow adoption is not full acceptance')
    require(c['parent'] == {'stage':82,'size':33554432,'sha256':PARENT_SHA,
                           'base_stats_pointer_site':444,'base_stats_address':0x09576c74,'stride':32},
            'parent binding differs')
    expected = [
        ('SPECIES_KEY_VEGA_220', 220, 'ジバクン', [
            {'field':'ability.normal_1','before_key':'ABILITY_KEY_WONDERGUARD','after_key':'ABILITY_KEY_CURSEDBODY'},
            {'field':'ability.normal_2','before_key':'ABILITY_KEY_SHADOWTAG','after_key':'ABILITY_KEY_FRISK'}]),
        ('SPECIES_KEY_VEGA_373', 373, 'カモナイツ', [{'field':'base_stat.attack','before':75,'after':45}])]
    for row, (key, sid, name, changes) in zip(a['records'], expected):
        require(row['species_key'] == key and type(row['expected_id']) is int and row['expected_id'] == sid
                and row['display_name'] == name and row['form_key'] == 'FORM_KEY_BASE', 'species/form identity differs')
        require(row['changes'] == changes, 'adopted field decision differs')
        for delta in row['changes']:
            for k in ('before', 'after'):
                if k in delta:
                    require(type(delta[k]) is int, 'numeric adoption is not integer')
    return c


def build(parent: bytes, root: Path = ROOT) -> tuple[bytes, dict]:
    require(type(parent) is bytes, 'parent must be immutable bytes')
    require(identity(parent) == {'size':33554432, 'sha256':PARENT_SHA}, 'exact Stage82 parent required')
    c = specification(root)
    species = manifest(root, 'manifests/species_ids.csv', 'species_key')
    abilities = manifest(root, 'manifests/ability_ids.csv', 'ability_key')
    table = struct.unpack_from('<I', parent, 444)[0]
    require(table == c['parent']['base_stats_address'], 'live BaseStats root differs')
    child = bytearray(parent)
    spans, permitted = [], set()
    for row in c['adoption']['records']:
        record = species[row['species_key']]
        sid = int(record['id'])
        require(sid == row['expected_id'] and record['display_name'] == row['display_name']
                and record['form_key'] == '', 'stable species manifest differs')
        start = table - 0x08000000 + sid * 32
        before_row = bytes.fromhex(row['expected_parent_row_hex'])
        require(len(before_row) == 32 and parent[start:start+32] == before_row, 'complete parent species row differs')
        for delta in row['changes']:
            off, size = OFFSETS[delta['field']]
            if size == 2:
                before = int(abilities[delta['before_key']]['id'])
                after = int(abilities[delta['after_key']]['id'])
                require(0 < before < 318 and 0 < after < 318, 'ability ID out of range')
            else:
                before, after = delta['before'], delta['after']
                require(1 <= before <= 255 and 1 <= after <= 255, 'base stat out of range')
            before_bytes, after_bytes = before.to_bytes(size, 'little'), after.to_bytes(size, 'little')
            at = start + off
            require(parent[at:at+size] == before_bytes, 'parent field mismatch')
            require(not permitted.intersection(range(at,at+size)), 'overlapping adoption spans')
            permitted.update(range(at,at+size))
            child[at:at+size] = after_bytes
            spans.append({'species_key':row['species_key'], 'species_id':sid, 'form_key':row['form_key'],
                          'field':delta['field'], 'offset':at,'before_hex':before_bytes.hex(),'after_hex':after_bytes.hex()})
    changed = [i for i, (a,b) in enumerate(zip(parent, child)) if a != b]
    require(len(child) == len(parent) and len(spans) == 3 and len(changed) == 3
            and set(changed) <= permitted, 'unexpected ROM footprint')
    result = bytes(child)
    require(identity(result)['sha256'] == CANDIDATE_SHA, 'fixed Stage83 output differs')
    report = {'schema_version':1,'status':'BUILT_NOT_ACCEPTED','stage':83,
              'scope':'TWO_PREVIOUSLY_DECIDED_SPECIES_ADJUSTMENTS',
              'parent':identity(parent),'candidate':identity(result),'adopted_species_count':2,
              'field_change_count':3,'changed_byte_count':len(changed),'changes':spans,
              'source_contract':{'path':CONTRACT, **identity(safe_read(root,CONTRACT))},
              'live_base_stats_root':table,'unrelated_bytes_preserved':True,
              'stable_ids_unchanged':True,'hidden_slots_unchanged':True,'learnsets_unchanged':True,
              'save_abi_unchanged':True,'active_baseline_changed':False,
              'full_p06_acceptance':False,'release_ready':False}
    return result, report
