#!/usr/bin/env python3
"""現候補の文字列・Z対応・技分類と、供給/受入正本の読取専用projection。"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode = True
from pr16_candidate_wiki_inputs import Inputs, Rom, BASE, ROOT, STATE, candidate_bytes, digest, need, stable
from pr16_candidate_wiki_extract import extract

SOURCE = 'content/modernization/pr16_candidate_wiki_source_model.json'
CANONICAL = (
    'content/collection_supply_v1/canonical_model.json',
    'content/modernization/p04_mega_runtime_mapping.json',
    'content/modernization/p04_candidate_manifest.json',
    'content/modernization/p05_battle_content_contract.json',
    'content/modernization/p08_native_mega_acceptance.json',
    'content/modernization/pr16_completion_acceptance.json',
    'content/modernization/pr16_p08_candidate_transfer.json',
    'content/modernization/pr16_generic_form_acceptance.json',
    'content/modernization/pr16_fixed_form_acceptance.json',
    'content/modernization/pr16_p05_route_acceptance.json',
    'content/modernization/mega_shop_catalog.json',
    'config/modernization_p05_ability_runtime.json',
    'config/modernization_rockruff_own_tempo_stage75.json',
)
CSV_INPUTS = (
    'vendor/vega_acquisition/content/collectible_species_registry.csv',
    'vendor/vega_acquisition/content/species_acquisition_routes.csv',
    'vendor/vega_acquisition/content/evolution_requirements_553.csv',
    'vendor/vega_acquisition/content/acquisition_events.csv',
)


def text_at(rom: Rom, address: int, charmap: dict, maximum: int = 1024) -> dict:
    """終端のない文字列は拒否。未知制御byteは欠落させず可視tokenにする。"""
    chars = []; data = bytearray()
    for index in range(maximum):
        value = rom.read(address + index, 1)[0]; data.append(value)
        if value == 255:
            return {'text': ''.join(chars), 'pointer': f'0x{address:08X}',
                    'size': len(data), 'sha256': digest(bytes(data)), 'evidence': 'EXACT_CANDIDATE_ROM'}
        chars.append({254: '\n', 250: '\n', 251: '\n\n'}.get(value, charmap.get(str(value), f'<0x{value:02X}>')))
    raise ValueError('文字列終端なし: ' + hex(address))


def locate(raw: bytes, pattern: bytes, label: str) -> dict:
    """上流tableのbyte署名一致とconsumerの実行証拠を混同しない。"""
    need(len(pattern) >= 8, '短すぎるtable署名')
    positions = []; start = 0
    while True:
        pos = raw.find(pattern, start)
        if pos < 0: break
        positions.append(pos); start = pos + 1
        need(len(positions) <= 32, 'table署名が過度に曖昧: ' + label)
    return {'matches': [f'0x{BASE+p:08X}' for p in positions], 'size': len(pattern),
            'sha256': digest(pattern), 'evidence': 'EXACT_CANDIDATE_ROM' if positions else 'GENERATED_CANONICAL',
            'consumer_proof': 'DEFERRED_AUDIT', 'byte_match_only': True}


def details(inputs: Inputs, raw: bytes) -> dict:
    model = extract(inputs, raw); rom = Rom(raw)
    rt = {k: int(v,16) for k,v in model['roots'].items()}
    source = inputs.json(SOURCE); chart = source['charmap']
    for name, expected in source['local_bindings'].items():
        value = inputs.raw(name)
        need(len(value) == expected['size'] and digest(value) == expected['sha256'], '意味sourceのlocal binding不一致: '+name)
    model['abilities'] = []
    for row in model['registries']['ability']:
        aid = row['id']
        name = text_at(rom,rt['ability_names']+aid*17,chart,17)
        description = text_at(rom,rom.u32(rt['ability_descriptions']+aid*4),chart)
        model['abilities'].append(dict(row, name=name['text'], description=description['text'],
            text_sources={'name':name,'description':description}, evidence='EXACT_CANDIDATE_ROM'))
    model['items'] = []
    for row in model['registries']['item']:
        iid = row['id']; address = rt['item_data']+iid*40
        name = text_at(rom,address,chart,14)
        description = text_at(rom,rom.u32(address+20),chart)
        model['items'].append(dict(row, name=name['text'], description=description['text'],
            price=rom.u16(address+16), hold_effect_id=rom.read(address+18,1)[0],
            hold_effect_parameter=rom.read(address+19,1)[0],
            text_sources={'name':name,'description':description}, evidence='EXACT_CANDIDATE_ROM'))
    for move in model['moves']:
        mid = move['id']
        name = text_at(rom,rt['move_names']+mid*16,chart,16)
        description = text_at(rom,rom.u32(rt['move_descriptions']+mid*4),chart)
        move.update(name=name['text'], description=description['text'], text_sources={'name':name,'description':description})
    for row in model['species']:
        name = text_at(rom,rt['species_species_names']+row['id']*11,chart,11)
        row.update(rom_name=name['text'], name_source=name)
    model['move_categories'] = {}
    for key, rows in source['move_categories'].items():
        signature = struct.pack('<'+'H'*(len(rows)+1),*rows,65535)
        model['move_categories'][key] = dict(move_ids=rows, **locate(raw,signature,key))
    zrows = source['special_z_moves']
    signature = b''.join(struct.pack('<HHHH',r['species_id'],r['item_id'],r['base_move_id'],r['z_move_id']) for r in zrows)
    proof = locate(raw,signature,'special Z')
    need(bool(proof['matches']), '専用Z対応tableが候補byteに存在しない')
    model['special_z_moves'] = {'rows': zrows, 'proof': proof}
    model['canonical'] = {p:inputs.json(p) for p in CANONICAL}
    model['canonical'].update({p:inputs.csv(p) for p in CSV_INPUTS})
    model['source_model'] = {k:source[k] for k in ('effect_ids','cfru_battle_fields','max_powers','source_commit','source_repository','source_bindings')}
    model['p07_source_rows'] = inputs.json('content/modernization/pr16_candidate_wiki_p07_source_rows.json')
    # 可変引継ぎの全文hashはWiki完了receiptとの自己参照になる。候補選択そのものは毎回検査する。
    for name in ('scripts/pr16_candidate_wiki_inputs.py','scripts/pr16_candidate_wiki_extract.py',
                 'scripts/pr16_candidate_wiki_details.py'):
        inputs.raw(name)
    model['source_bindings'] = {k:v for k,v in inputs.bindings.items() if k != STATE}
    model['selection_check'] = {'candidate':model['candidate'],'native_transfer_complete':True,
                               'state_path':STATE,'full_state_hash_excluded_to_avoid_receipt_cycle':True}
    return model


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',default='.local/pr16-wiki/details.json')
    args=p.parse_args(); inputs=Inputs(); output=inputs.path(args.output)
    need(output.is_relative_to(ROOT/'.local'), 'details出力は.local内のみ')
    value=details(inputs,candidate_bytes(inputs))
    output.parent.mkdir(parents=True,exist_ok=True); output.write_bytes(stable(value))
    print(json.dumps({'status':'PASS_DETAILS','candidate':value['candidate'],'counts':value['counts'],
                      'special_z_rows':len(value['special_z_moves']['rows']),'new_native_runs':0,'rom_changes':0},sort_keys=True))
    return 0


if __name__=='__main__':
    try: raise SystemExit(main())
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('candidate wiki details: '+str(exc),file=sys.stderr);raise SystemExit(1)
