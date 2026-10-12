#!/usr/bin/env python3
"""固定cacheのELF・技正本を現候補へ照合する。復元byte読取だけでbuild/nativeなし。"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import zipfile
sys.dont_write_bytecode = True
from pr16_candidate_wiki_inputs import Inputs, ROOT, BASE, Rom, candidate_bytes, digest, identity, need, stable
from pr16_wiki_elf_symbols import Elf
from pr16_candidate_wiki_link_graph import structural_graph

TARGETS = ('HandleInputChooseMove', 'VegaBattlePolicyCanZ', 'VegaBattlePolicyMarkZ', 'CanUseZMove',
    'GetTypeBasedZMove', 'CalcMoveSplit', 'GetSpecialZMove', 'SetZEffect', 'ReplaceWithZMoveRuntime',
    'GiveBoxMonInitialMoveset', 'GiveMoveToBoxMon', 'CreateBoxMon', 'CreateMon', 'GetHiddenAbility',
    'GetAbility1', 'GetAbility2', 'GetMonAbility', 'GetBoxMonAbility', 'FieldUseFunc_AbilityCapsule',
    'ItemUseCB_AbilityCapsule', 'Task_HandleAbilityChangeYesNoInput', 'Task_ChangeAbility',
    'DetermineEggAbility', 'CreateEgg', 'GiveEggFromDaycare', 'CreateWildMon', 'ScriptGiveMon',
    'VegaResolveMoveEffectScript', 'VegaMoveEffectPrepare', 'gMovesThatChangePhysicality',
    'gBattleScriptsForMoveEffects')


def archived(path: Path, name: str, cfg: dict) -> zipfile.ZipFile:
    expected = next(r for r in cfg['archives'] if r['name'] == name)
    raw = path.read_bytes()
    need(len(raw) == expected['size'] and digest(raw) == expected['sha256'], '固定archive hash/size不一致: ' + name)
    archive = zipfile.ZipFile(io.BytesIO(raw))
    names = archive.namelist(); need(len(names) == len(set(names)), 'archive名重複')
    return archive


def text_member(archive: zipfile.ZipFile, name: str) -> bytes:
    info = archive.getinfo(name); path = PurePosixPath(name)
    need(not path.is_absolute() and '..' not in path.parts and '\\' not in name, 'archive path不正')
    need(info.file_size <= 4000000 and info.external_attr >> 28 != 0xA, 'text size/symlink不正')
    raw = archive.read(info); raw.decode('utf-8'); need(b'\0' not in raw, 'text NUL')
    return raw


def collect(cache: Path, state: Path) -> dict:
    inputs = Inputs(); candidate = candidate_bytes(inputs); cfg = inputs.json('config/github_private_environment.json')
    meta_raw = inputs.raw('build/stages/06_battle_core.json'); meta = json.loads(meta_raw)
    expected = {r['linked_object']['sha256'] for r in meta['upstream_runs']}
    need(len(expected) == 1, 'Stage06 ELF identityが一意でない')
    index = []; chosen = []
    with archived(cache, 'pokemon-vega-private-env-v1-build-cache.zip', cfg) as archive:
        for info in archive.infolist():
            name = info.filename
            if not name.startswith('build/battle-core/') or not name.endswith('/linked.o'): continue
            need('..' not in PurePosixPath(name).parts and '\\' not in name and info.external_attr >> 28 != 0xA, 'ELF member不正')
            need(info.file_size <= 32000000, 'ELF member size超過')
            raw = archive.read(info); sha = digest(raw)
            index.append({'member': name, 'size': len(raw), 'sha256': sha, 'stage06_identity_match': sha in expected})
            if sha in expected: chosen.append((name, raw))
    need(bool(chosen), '固定cache内にStage06と同一hashのELFなし。再compileで代用しない')
    name, raw = sorted(chosen, key=lambda p:p[0])[0]; elf = Elf(raw)
    bindings = {symbol: elf.bind(symbol, candidate) for symbol in TARGETS}
    by_address = {}
    for symbol, rows in elf.symbols.items():
        if len(rows) == 1 and rows[0]['type'] == 2:
            by_address.setdefault(rows[0]['address'] & ~1, []).append(symbol)
    graphs = {}; callees = {}
    for symbol, row in bindings.items():
        if row['status'] != 'EXACT_CANDIDATE_SYMBOL_BODY' or row['elf_symbol']['type'] != 2: continue
        start = row['address']; end = start + row['size']
        graph = structural_graph(Rom(candidate), start, start, end)
        graph['saved_elf_full_extent_verified'] = True
        for call in graph['direct_calls']:
            target = int(call['target'], 16) if isinstance(call['target'], str) else call['target']
            names = sorted(by_address.get(target, [])); call['saved_symbol_names'] = names
            for callee in names:
                if callee not in callees: callees[callee] = elf.bind(callee, candidate)
            call['candidate_body_matched_names'] = [n for n in names if callees[n]['status'] == 'EXACT_CANDIDATE_SYMBOL_BODY']
        graphs[symbol] = graph
    out = ROOT/'.local/pr16-wiki-saved-link'; out.mkdir(parents=True, exist_ok=True)
    source_text = {}; move_rows = {}; state_members = []
    with archived(state, 'pokemon-vega-private-env-v1-state.zip', cfg) as archive:
        model_name = 'generated/engine/moves/move_port.json'
        need(model_name in archive.namelist(), '保存技正本がない')
        model_raw = text_member(archive, model_name); model = json.loads(model_raw)
        for mid in (1, 511):
            rows = [r for r in model['moves'] if r['id'] == mid]
            need(len(rows) == 1, '保存技rowの欠落/重複')
            move_rows[str(mid)] = rows[0]
        move_rows['model_binding'] = {'member':model_name,'size':len(model_raw),'sha256':digest(model_raw)}
        move_rows['aliases'] = [r for r in model['aliases'] if r['cfru_symbol'] == 'MOVE_POUND']
        for logical in ('src/build_pokemon.c','src/daycare.c','src/party_menu.c','src/pokemon.c'):
            member = 'vendor/upstream/CFRU-JP/' + logical
            if member not in archive.namelist(): continue
            source = text_member(archive, member)
            source_text[logical] = {'size':len(source),'sha256':digest(source)}
            target = out/'source'/logical; target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(source)
        state_members = [{'member': n} for n in archive.namelist() if n.endswith('move_port.json')]
    report = {'schema_version':1,'source_head':os.environ['GITHUB_SHA'],'run_id':int(os.environ['GITHUB_RUN_ID']),
        'candidate':identity(candidate),'metadata':{'path':'build/stages/06_battle_core.json','size':len(meta_raw),'sha256':digest(meta_raw)},
        'archives':[{k:r[k] for k in ('name','size','sha256')} for r in cfg['archives'] if r['name'] in (cache.name,state.name)],
        'elf':{'member':name,'size':len(raw),'sha256':digest(raw),'equivalent_members':[n for n,_ in chosen]},
        'cache_index':index,'symbols':bindings,'direct_callees':dict(sorted(callees.items())), 'graphs':graphs,
        'move_rows':move_rows,'source_text_bindings':source_text,'state_move_model_members':state_members,
        'summary':{'requested_symbols':len(bindings),'symbol_states':dict(sorted(Counter(r['status'] for r in bindings.values()).items())),
                   'graphs':len(graphs),'direct_calls':sum(len(g['direct_calls']) for g in graphs.values()),'named_callees':len(callees)},
        'new_native_runs':0,'arm_builds':0,'rom_changes':0,'saved_byte_restoration_only':True,
        'runtime_reachability_proven':False,'all_indirect_edges_resolved':False}
    (out/'report.json').write_bytes(stable(report))
    registry = inputs.raw('manifests/move_ids.csv'); (out/'move_ids.csv').write_bytes(registry)
    print(json.dumps({'status':'PASS_SAVED_ELF_CANDIDATE_BINDING',**report['summary']},ensure_ascii=False))
    return report


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--cache',type=Path,required=True);parser.add_argument('--state',type=Path,required=True)
    args=parser.parse_args();collect(args.cache,args.state)
