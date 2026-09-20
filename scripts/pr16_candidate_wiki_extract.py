#!/usr/bin/env python3
"""現候補からWiki用の意味付きtext modelだけを取り出す。ROM/画像byteを出力しない。"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode = True
from pr16_candidate_wiki_inputs import (Inputs, Rom, BASE, ROOT, ROCKRUFF, base_rows, candidate_bytes,
                                        digest, identity, move_rows, need, registries, roots, stable)


def learnsets(inputs: Inputs, rom: Rom, rt: dict, ids: dict) -> list[dict]:
    count, moves = len(ids['species']), len(ids['move'])
    eggs = rom.eggs(rt['egg_moves'], count, moves)
    symbols73 = inputs.json('generated/runtime/modernization_p03_stage73_consumer_runtime_symbols.json')['symbols']
    symbols74 = inputs.json('generated/runtime/modernization_p03_stage74_supply_runtime_symbols.json')['symbols']
    rock = inputs.json(ROCKRUFF)
    result = []
    for sid in range(count):
        item = {'species_id': sid, 'species_key': ids['species'][sid]['key'], 'routes': []}
        routes = item['routes']
        def add(route, mid, **details):
            need(0 < mid < moves, 'learnset move参照範囲外')
            routes.append({'route': route, 'move_id': mid, 'move_key': ids['move'][mid]['key'],
                           'evidence': 'EXACT_CANDIDATE_ROM', **details})
        for r in rom.level(rt['species_level_up_pointers'], sid, moves):
            add('level_up', r['move_id'], level=r['level'], order=r['order'])
        for order, mid in enumerate(eggs[sid]):
            add('egg', mid, order=order)
        # Native ABIはTM/HM 128slot、Tutor下位64slot。余剰tutor bitを供給扱いしない。
        for route, table, catalog, slots in [('machine', 'species_tmhm','tm_hm_move_catalog',128),
                                              ('tutor','species_tutor','tutor_move_catalog',64)]:
            bits = rom.read(rt[table]+sid*16, 16)
            for slot in range(slots):
                if bits[slot//8] & (1 << (slot%8)):
                    mid = rom.u16(rt[catalog]+slot*2)
                    if mid:
                        add(route, mid, slot=slot+1, availability='COMPATIBILITY_NOT_ITEM_SUPPLY')
        owner = rock['identity']['normal_species_id'] if sid == rock['identity']['species_id'] else sid
        for route, prefix, index, data, symbols in [
            ('shared_egg','Stage73','SharedIndex','SharedMoves',symbols73),
            ('move_memory_reminder','Stage73','ReminderIndex','ReminderMoves',symbols73),
            ('machine_archive','Stage74','MachineIndex','MachineMoves',symbols74),
            ('tutor_archive','Stage74','TutorIndex','TutorMoves',symbols74),
            ('build_learnable_preservation','Stage74','PreservationIndex','PreservationMoves',symbols74)]:
            a = int(symbols[prefix+'_'+index]['address'],16)
            b = int(symbols[prefix+'_'+data]['address'],16)
            for order, mid in enumerate(rom.indexed(a,b,owner,moves)):
                add(route,mid,order=order,owner_species_id=owner,
                    availability='HISTORY_NOT_DIRECT_TEACHING' if route=='build_learnable_preservation' else 'IMPLEMENTED_OWNER_ROUTE')
        if sid == rock['identity']['species_id']:
            for order, mid in enumerate(rock['breeding']['get_egg_moves_1670']):
                if mid not in eggs[sid]:
                    routes.append({'route':'conditional_egg','move_id':mid,'move_key':ids['move'][mid]['key'],
                                   'order':order,'source':ROCKRUFF,'evidence':'GENERATED_CANONICAL'})
        result.append(item)
    return result


def evolutions(rom: Rom, rt: dict, ids: dict) -> list[dict]:
    result = []
    for sid in range(len(ids['species'])):
        for slot in range(16):
            method, parameter, target, extra = struct.unpack('<HHHH',rom.read(rt['evolution']+sid*128+slot*8,8))
            if not method:
                continue
            need(target < len(ids['species']), '進化先ID範囲外')
            result.append({'species_id':sid,'species_key':ids['species'][sid]['key'],'slot':slot,
                           'method_id':method,'parameter':parameter,'target_id':target,
                           'target_key':ids['species'][target]['key'],'extra':extra,
                           'evidence':'EXACT_CANDIDATE_ROM'})
    return result


def mega_rows(inputs: Inputs, rom: Rom, rt: dict, ids: dict, stats: list, evos: list) -> list[dict]:
    mappings = inputs.json('content/modernization/p04_mega_runtime_mapping.json')['mappings']
    by_pair = {(r['source_species_id'],r['target_species_id']):r for r in mappings}
    out = []
    for row in evos:
        if row['method_id'] != 254 or row['parameter'] == 0:
            continue
        sid, target, item = row['species_id'],row['target_id'],row['parameter']
        need(item < len(ids['item']), 'メガitem ID範囲外')
        reverse = [r for r in evos if r['species_id']==target and r['target_id']==sid
                   and r['method_id']==254 and r['parameter']==0]
        assets = {}
        for key in ('front','back','palette','shiny_palette'):
            ptr = rom.u32(rt['species_'+key]+target*8)
            assets[key] = rom.lz_asset(ptr)
            if key in ('front','back'):
                coord = rom.read(rt['species_'+key+'_coords']+target*4,4)
                assets[key].update(canvas_width=64,canvas_height=64,format='GBA_4BPP',
                                   bounding_width=(coord[0]>>4)*8,bounding_height=(coord[0]&15)*8,
                                   y_offset=coord[1])
        ptr = rom.u32(rt['species_icon']+target*4)
        assets['icon']={'pointer':f'0x{ptr:08X}','size':1024,'sha256':digest(rom.read(ptr,1024)),
                        'width':32,'height':32,'frames':2,'format':'GBA_4BPP',
                        'palette_selector':rom.read(rt['species_icon_palette']+target,1)[0],
                        'evidence':'EXACT_CANDIDATE_ROM'}
        match = by_pair.get((sid,target))
        if match:
            need(item==match['mega_stone_id'] and bool(reverse), 'P04メガ正逆mapping不一致')
        out.append({'base_species_id':sid,'base_species_key':ids['species'][sid]['key'],
                    'mega_species_id':target,'mega_species_key':ids['species'][target]['key'],
                    'item_id':item,'item_key':ids['item'][item]['key'],'variant':row['extra'],
                    'mapping_scope':'P04_ADDED' if match else 'LEGACY',
                    'reverse_verified':bool(reverse),'reverse_entries':reverse,
                    'types_before':stats[sid]['types'],'types_after':stats[target]['types'],
                    'ability_ids':stats[target]['ability_ids'],
                    'stat_delta':{k:stats[target]['base_stats'][k]-v for k,v in stats[sid]['base_stats'].items()},
                    'assets':assets,'evidence':'EXACT_CANDIDATE_ROM'})
    need(len([r for r in out if r['mapping_scope']=='P04_ADDED'])==len(mappings),'P04メガmapping欠落')
    return out


def extract(inputs: Inputs, raw: bytes) -> dict:
    ids = registries(inputs); rom = Rom(raw); rt = roots(inputs,rom,ids)
    stats = base_rows(rom,rt['species_base_stats'],ids)
    moves = move_rows(rom,rt['move_battle'],ids)
    evos = evolutions(rom,rt,ids)
    return {'schema_version':1,'candidate':identity(raw),'counts':{k:len(v) for k,v in ids.items()},
            'registries':ids,'species':stats,'moves':moves,'learnsets':learnsets(inputs,rom,rt,ids),
            'evolutions':evos,'megas':mega_rows(inputs,rom,rt,ids,stats,evos),
            'tables':rom.tables,'roots':{k:f'0x{v:08X}' for k,v in rt.items()},
            'new_native_runs':0,'rom_changes':0,'source_bindings':inputs.bindings}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',default='.local/pr16-wiki/projection.json')
    args = parser.parse_args()
    inputs = Inputs()
    output = inputs.path(args.output)
    need(output.is_relative_to(ROOT/'.local'), '抽出text出力は.local内のみ')
    model = extract(inputs,candidate_bytes(inputs))
    output.parent.mkdir(parents=True,exist_ok=True); output.write_bytes(stable(model))
    print(json.dumps({'candidate':model['candidate'],'counts':model['counts'],
                      'megas':len(model['megas']),'routes':sum(len(r['routes']) for r in model['learnsets']),
                      'status':'PASS_EXACT_ROM_TEXT_EXTRACTION','new_native_runs':0},sort_keys=True))
    return 0


if __name__=='__main__':
    try:
        raise SystemExit(main())
    except (OSError,ValueError,KeyError,TypeError) as exc:
        print('candidate wiki extract: '+str(exc),file=sys.stderr);raise SystemExit(1)
