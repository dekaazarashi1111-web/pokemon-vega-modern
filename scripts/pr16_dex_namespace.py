#!/usr/bin/env python3
"""既存collection方針をstable keyで現runtimeへ再束縛。ROMと原本は更新しない。"""
from __future__ import annotations
import argparse
import csv
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = (
    'manifests/species_ids.csv',
    'vendor/vega_acquisition/content/collectible_species_registry.csv',
    'vendor/vega_acquisition/manifests/collection_ledger_bits.csv',
    'content/modernization/p04_capacity_allocation_manifest.json',
    'content/modernization/p04_candidate_manifest.json',
)
OUTPUT = 'content/modernization/pr16_dex_namespace.json'
COUNT = 1206
OWNER_SEMANTICS_V1 = 'c39e76c2db47ec22af37a2b101873253b44154f39e52d2b22c71f87624e685e3'
OWNER_ORDER_V1 = "4a0cb4d7c386ae62e69c16fa939bdadbd3bff683ea95e51d9c444bbca10a4072"

def need(condition, message):
    if not condition:
        raise ValueError(message)

def rows(root, path):
    with (root / path).open(encoding='utf-8', newline='') as file:
        return list(csv.DictReader(file))

def unique(items, key):
    result = {item[key]: item for item in items}
    need(len(result) == len(items), 'duplicate ' + key)
    return result

def identity(data):
    return dict(size=len(data), sha256=hashlib.sha256(data).hexdigest())

def build(root=ROOT):
    species = rows(root, SOURCES[0])
    registry = unique(rows(root, SOURCES[1]), 'species_key')
    ledger = rows(root, SOURCES[2])
    species_by_key = unique(species, 'species_key')
    need(set(species_by_key) == set(registry), 'registry key coverage')
    need(sorted(int(row['id']) for row in species) == list(range(1621)), 'current species slots')
    owners = [row for row in ledger if row['completion_weight'] == '1']
    need(len(owners) == COUNT, 'locked 1206 species owners')
    need([int(row['ledger_bit_index']) for row in owners] == list(range(COUNT)), 'stable owner order')
    by_owner = unique(owners, 'collection_key')
    for owner in owners:
        reg = registry[owner['species_key']]
        need(reg['collection_key'] == owner['collection_key']
             and reg['target_status'] == owner['target_status']
             and reg['completion_weight'] == owner['completion_weight']
             and reg['display_name'] == owner['display_name'], 'owner species binding')
    need(len(ledger) == 1216 and all(row['target_status'] == 'REQUIRED_ENABLING_FORM'
         and row['completion_weight'] == '0' for row in ledger[COUNT:]), 'separate ten form owners')
    official = {int(row['national_no']): row for row in registry.values()
                if row['target_status'] == 'REQUIRED_BASE'}
    need(set(official) == set(range(1, 1026)), 'all official base owners')
    need(all(row['collection_key'] == f'COLLECTION_NATIONAL_{n:04d}' for n,row in official.items()), 'official owner meaning')
    mapping = []
    for row in species:
        key = row['species_key']; reg = registry[key]
        national = int(row['canonical_national_dex'])
        need(national == int(reg['national_no'] or 0)
             and row['form_key'] == reg['form_key']
             and row['is_official'] == reg['is_official']
             and row['display_name'] == reg['display_name'], 'identity mismatch ' + key)
        if row['is_official'] == 'true':
            need(national in official, 'unbound official national')
            owner_key = official[national]['collection_key']
        elif reg['target_status'] == 'REQUIRED_VEGA_ORIGINAL':
            owner_key = reg['collection_key']
        else:
            need(reg['target_status'] in {'INTERNAL_EXCLUDED', 'INTERNAL_EXCLUDED_RESERVED', 'INTERNAL_EXCLUDED_CROSS_ROM_SLOT', 'BATTLE_ONLY_EXCLUDED_COPY'}, 'undeclared non-owner')
            owner_key = None
        owner = int(by_owner[owner_key]['ledger_bit_index']) + 1 if owner_key else 0
        mapping.append(dict(species_id=int(row['id']), species_key=key,
                            form_key=row['form_key'], owner=owner))
    by_key = unique(mapping, 'species_key')
    capacity = json.loads((root / SOURCES[3]).read_text())['id_reservations']['species_form']
    candidates = unique(json.loads((root / SOURCES[4]).read_text())['records'], 'record_key')
    need(capacity['current_count'] == 1621 and capacity['new_count'] == 1670
         and capacity['append_count'] == 49, 'bound Stage70 capacity')
    for row in capacity['rows']:
        candidate = candidates[row['source_record_key']]
        base = species_by_key[row['identity_species_key']]
        need(row['species_key'] == candidate['proposed_species_key']
             and row['identity_form_key'] == candidate['identity_form_key']
             and candidate['national_dex'] == int(base['canonical_national_dex'])
             and row['classification'] == 'BATTLE_ONLY_MEGA', 'P04 identity binding')
        mapping.append(dict(species_id=row['id'], species_key=row['species_key'],
                            form_key=row['identity_form_key'],
                            owner=by_key[row['identity_species_key']]['owner']))
    unique(mapping, 'species_key')
    mapping.sort(key=lambda row: row['species_id'])
    need([row['species_id'] for row in mapping] == list(range(1670)), 'complete runtime slots')
    need(set(row['owner'] for row in mapping) == set(range(COUNT + 1)), 'owner coverage')
    need(sum(row['owner'] == 0 for row in mapping) == 27, 'only NONE/Egg/internal25 excluded')
    owner_keys = [row['collection_key'] for row in owners]
    # 保存namespaceの意味はこの順序に固定。変更時は新version/移行を要求する。
    epoch = identity(('\n'.join(owner_keys) + '\n').encode())['sha256']
    semantics = identity(serialized([{k:row[k] for k in ('collection_key','species_key','target_status')} for row in owners]))['sha256']
    need(semantics == OWNER_SEMANTICS_V1, 'owner semantics needs namespace version migration')
    need(epoch == OWNER_ORDER_V1, 'owner order needs explicit namespace version migration')
    return dict(schema_version=1, namespace_version=1, owner_count=COUNT,
                owner_order_sha256=epoch, owner_semantics_sha256=semantics, runtime_slot_count=1670,
                excluded_slots=27, separate_form_collection_owners=10,
                source_bindings={p: identity((root / p).read_bytes()) for p in SOURCES},
                owner_keys=owner_keys, species=mapping,
                official_national_to_owner=[0] + [int(by_owner[official[n]['collection_key']]
                    ['ledger_bit_index']) + 1 for n in range(1, 1026)],
                official_national_to_representative_sid=[0] + [int(species_by_key[official[n]['species_key']]['id']) for n in range(1, 1026)],
                runtime_wired=False, native_accepted=False)

def lookup_sid(namespace, species_id):
    need(type(species_id) is int and 0 < species_id < namespace['runtime_slot_count'], 'species boundary')
    owner = namespace['species'][species_id]['owner']
    need(owner != 0, 'excluded species')
    return owner

def lookup_official(namespace, national):
    need(type(national) is int and 1 <= national <= 1025, 'official national boundary')
    return namespace['official_national_to_owner'][national]

def serialized(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode()

def main():
    parser = argparse.ArgumentParser(); parser.add_argument('command', choices=['build', 'check'])
    args = parser.parse_args(); result = serialized(build()); target = ROOT / OUTPUT
    if args.command == 'build':
        target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(result)
    else:
        need(target.read_bytes() == result, 'namespace generated bytes differ')
    print('図鑑namespace: PASS（1206 owner / 1670 slot、runtime未接続）')
if __name__ == '__main__':
    main()
