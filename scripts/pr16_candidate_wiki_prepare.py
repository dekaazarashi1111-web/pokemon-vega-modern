#!/usr/bin/env python3
"""固定上流textと採用V4の意味modelを作る一度限りの準備。network/build/nativeなし。"""
from __future__ import annotations
import argparse
from pathlib import Path
import re
import sys
sys.dont_write_bytecode=True
from pr16_candidate_wiki_inputs import Inputs, ROOT, digest, need, stable

SOURCE_MODEL='content/modernization/pr16_candidate_wiki_source_model.json'
P07_MODEL='content/modernization/pr16_candidate_wiki_p07_source_rows.json'


def prepare(directory: Path, v4: Path) -> dict:
    inp=Inputs(); lock=inp.json('state/source-lock.json')
    ref=next(s for s in lock['sources'] if s['name']=='cfru')['resolved_commit']
    bindings={}; texts={}
    for name in ('charmap.tbl','src/set_z_effect.c','src/Tables/battle_moves.c',
                 'assembly/data/move_tables.s','include/constants/battle_move_effects.h',
                 'src/dynamax.c','include/constants/pokemon.h','src/defines_battle.h'):
        raw=(directory/name).read_bytes(); text=raw.decode('utf-8-sig')
        need(b'\0' not in raw,'source NUL')
        bindings[name]={'size':len(raw),'sha256':digest(raw),'source_commit':ref}
        texts[name]=text
    ids={domain:{r['dpe_symbol' if domain=='species' else 'cfru_symbol']:r
                 for r in inp.csv(f'manifests/{domain}_ids.csv')
                 if r['dpe_symbol' if domain=='species' else 'cfru_symbol']}
         for domain in ('species','item','move')}
    def mid(symbol):
        need(symbol in ids['move'],'unmapped move '+symbol)
        return int(ids['move'][symbol]['id'])
    text=texts['src/set_z_effect.c'].split('sSpecialZMoveTable[] =',1)[1].split('};',1)[0]
    special=[]
    for species,item,move,zmove in re.findall(r'\{\s*(SPECIES_\w+)\s*,\s*(ITEM_\w+)\s*,\s*(MOVE_\w+)\s*,\s*(MOVE_\w+)\s*\}',text):
        row={'species_id':int(ids['species'][species]['id']),'item_id':int(ids['item'][item]['id']),
             'base_move_id':mid(move),'z_move_id':mid(zmove),'source_symbols':[species,item,move,zmove]}
        special.append(row)
    need(len(special)==31,'special Z table count')
    chart={}
    for line in texts['charmap.tbl'].splitlines():
        if re.match(r'^[0-9A-Fa-f]{2}=',line):chart[str(int(line[:2],16))]=line[3:]
    battle={}
    for symbol,body in re.findall(r'\[(MOVE_\w+)\]\s*=\s*\{(.*?)\}',texts['src/Tables/battle_moves.c'],re.S):
        if symbol in ids['move']:
            battle[str(mid(symbol))]={'source_symbol':symbol,'fields':dict(re.findall(r'\.(\w+)\s*=\s*([^,\n]+)',body))}
    powers={str(mid(s)):int(n) for s,n in re.findall(r'\[(MOVE_\w+)\]\s*=\s*(\d+)',texts['src/Tables/battle_moves.c']) if s in ids['move']}
    effects={name:int(value,0) for name,value in re.findall(r'^#define\s+(EFFECT_\w+)\s+(0x[0-9a-fA-F]+|[0-9]+)\b',texts['include/constants/battle_move_effects.h'],re.M)}
    methods={name:int(value,0) for name,value in re.findall(r'^#define\s+(EVO_\w+)\s+(0x[0-9a-fA-F]+|[0-9]+)\b',texts['include/constants/pokemon.h'],re.M)}
    categories={}
    asm=texts['assembly/data/move_tables.s']
    wanted={'gPunchingMoves','gSlicingMoves','gBallBombMoves','gSoundMoves','gDanceMoves',
            'gPowderMoves','gBitingMoves','gPulseAuraMoves','gWindMoves','gHealingMoves'}
    for name,body in re.findall(r'^(\w+):\s*\n(.*?)(?=^\w+:|\Z)',asm,re.M|re.S):
        if name in wanted:
            symbols=re.findall(r'^\s*\.hword\s+(MOVE_\w+)',body,re.M)
            need(symbols and symbols[-1]=='MOVE_TABLES_TERMIN','category terminator missing: '+name)
            categories[name]=[mid(s) for s in symbols[:-1]]
    need({'gPunchingMoves','gSlicingMoves','gBallBombMoves','gSoundMoves'}<=categories.keys(),'move category tables missing')
    model={'schema_version':1,'source_repository':'kapibarasan000/CFRU-JP','source_commit':ref,
           'source_bindings':bindings,'local_bindings':inp.bindings,'charmap':chart,'special_z_moves':special,
           'cfru_battle_fields':battle,'max_powers':powers,'effect_ids':effects,'evolution_methods':methods,
           'move_categories':categories,'evidence':'GENERATED_CANONICAL',
           'note':'固定上流の意味model。実候補ROM照合の成功した表だけをEXACT_CANDIDATE_ROMへ昇格する。'}
    (ROOT/SOURCE_MODEL).write_bytes(stable(model))
    import pr16_integration_continuation as p07
    raw=v4.read_bytes();need(digest(raw)==p07.V4_SHA,'V4 identity')
    species=inp.raw('manifests/species_ids.csv');moves=inp.raw('manifests/move_ids.csv')
    groups,members=p07.recover(raw,species,moves)
    need(len(groups['vega_to_official_historical_adoption'])==1073,'historical count')
    need(len(groups['official_to_vega_legacy_preservation'])==499,'preserved count')
    need(not groups['official_to_vega_explicit_v4_additions'],'unexpected adoption')
    value={'schema_version':1,'inputs':{'v4':p07.identity(raw),'species':p07.identity(species),'moves':p07.identity(moves)},
           'source_members':members,'groups':groups,'evidence':'GENERATED_CANONICAL'}
    (ROOT/P07_MODEL).write_bytes(stable(value))
    return {'special_z':len(special),'categories':{k:len(v) for k,v in categories.items()},
            'historical':1073,'preserved':499,'new_native_runs':0}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source-directory',type=Path,required=True)
    p.add_argument('--v4-archive',type=Path,required=True)
    args=p.parse_args()
    print(stable(prepare(args.source_directory,args.v4_archive)).decode(),end='')
