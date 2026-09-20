#!/usr/bin/env python3
"""取得済み固定sourceからWiki用の検証可能な最小原文を保存する。実装は実行しない。"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import sys
sys.dont_write_bytecode = True
from pr16_candidate_wiki_inputs import Inputs, ROOT, digest, need, stable

OUTPUT = 'content/modernization/pr16_candidate_wiki_consumer_sources.json'
LOCK = 'state/source-lock.json'
# 全sourceを複製しない。必要な関数と数値定義のみを行範囲・全file hash付きで保存。
FUNCTIONS = {
    'src/set_z_effect.c': ('GetTypeBasedZMove', 'GetSpecialZMove', 'CanUseZMove', 'SetZEffect',
                         'ReplaceWithZMoveRuntime', 'DoesZMoveUsageStopMegaEvolution'),
    'src/item.c': ('IsZCrystal', 'IsTypeZCrystal'),
    'src/battle_util.c': ('CalcMoveSplit',),
    'src/daycare.c': ('DetermineEggAbility',),
    'src/dexnav.c': ('DexNavGenerateHiddenAbility',),
    'src/wild_encounter.c': ('CreateWildMon', 'sp117_CreateRaidMon'),
    'src/build_pokemon.c': ('ScriptGiveMon',),
    'src/dynamax.c': ('GetRaidSpeciesAbilityNum', 'GetRaidEggMoveChance'),
}
HEADERS = {
    'include/constants/moves.h': ('MOVE_', 'FIRST_', 'LAST_'),
    'include/constants/pokemon.h': ('TYPE_',),
    'include/constants/hold_effects.h': ('ITEM_EFFECT_Z_CRYSTAL',),
    'include/new/z_move_effects.h': ('Z_EFFECT_',),
    'src/config.h': ('FLAG_HIDDEN_ABILITY', 'FLAG_WILD_CUSTOM_MOVES', 'GIVEPOKEMON_', 'OLD_MOVE_SPLIT'),
}
LOCAL_BINDINGS = ('scripts/build_battle_core.py', 'overlays/cfru/rom_bridge.c',
                  'overlays/collection_supply_v1/collection_supply_v1.c',
                  'overlays/modernization_p03_stage74_supply_runtime/modernization_p03_stage74_supply_runtime.c')


def mask_c(text: str) -> str:
    """位置・改行を維持し、コメントと文字列内の偽braceを無効化する。"""
    pattern = r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\''
    return re.sub(pattern, lambda m: ''.join('\n' if c == '\n' else ' ' for c in m[0]), text, flags=re.S)


def function_unit(text: str, name: str) -> dict:
    masked = mask_c(text)
    matches = list(re.finditer(r'\b' + re.escape(name) + r'\s*\([^;{}]*\)\s*\{', masked))
    need(len(matches) == 1, '関数定義が欠落/複数: ' + name)
    match = matches[0]; start = text.rfind('\n', 0, match.start()) + 1
    depth = 1; end = match.end()
    while depth and end < len(masked):
        depth += (masked[end] == '{') - (masked[end] == '}'); end += 1
    need(depth == 0, '関数braceが閉じない: ' + name)
    raw = text[start:end] + '\n'
    return {'symbol': name, 'start_line': text[:start].count('\n') + 1,
            'end_line': text[:end].count('\n') + 1, 'text': raw, 'sha256': digest(raw.encode())}


def defines(text: str, prefixes: tuple[str, ...]) -> list[dict]:
    result = []
    masked = re.sub(r'/\*.*?\*/', lambda m: '\n' * m[0].count('\n'), text, flags=re.S)
    for line, original in enumerate(masked.splitlines(), 1):
        match = re.match(r'^\s*#define\s+([A-Z][A-Z0-9_]*)(?:\s+(.*))?$', original.split('//', 1)[0])
        if match and match[1].startswith(prefixes):
            result.append({'symbol': match[1], 'expression': (match[2] or '').strip(), 'line': line})
    need(result, '必要なdefineがない')
    return result


def capture(consumer: Path, additional: Path, inputs: Inputs) -> dict:
    lock = next(r for r in inputs.json(LOCK)['sources'] if r['name'] == 'cfru')
    need(lock['configured_commit_verified'] and lock['actual_commit'] == lock['configured_commit'], 'source-lock不一致')
    roots = [(consumer, 'consumer-source-manifest.json'), (additional, 'additional-source-manifest.json')]
    available = {}; receipts = []
    for root, name in roots:
        raw = (root / name).read_bytes(); manifest = json.loads(raw)
        receipts.append({'run': manifest['run_id'], 'source_head': manifest['source_head'],
                         'manifest_sha256': digest(raw)})
        for key, binding in manifest['source_bindings'].items():
            if not key.startswith('upstream/CFRU-JP/'):
                continue
            path = binding['path']
            if path not in FUNCTIONS and path not in HEADERS:
                continue
            need(binding['commit'] == lock['configured_commit'], '固定上流commit違反: ' + path)
            value = (root / key).read_bytes()
            need(len(value) == binding['size'] and digest(value) == binding['sha256'], 'source hash不一致: ' + path)
            need(b'\0' not in value, 'NUL source'); value.decode('utf-8')
            if path in available:
                need(available[path][0] == value, '二重取得source不一致: ' + path)
            available[path] = (value, binding)
    need(set(available) == set(FUNCTIONS) | set(HEADERS), 'sourceが不足')
    sources = {}
    for path, (raw, binding) in sorted(available.items()):
        text = raw.decode()
        sources[path] = {'commit': binding['commit'], 'sha256': binding['sha256'], 'size': binding['size']}
        if path in FUNCTIONS:
            sources[path]['units'] = [function_unit(text, f) for f in FUNCTIONS[path]]
        if path in HEADERS:
            sources[path]['defines'] = defines(text, HEADERS[path])
    # 現HEADのlocal game sourceにbind。上流だけで候補固有のpolicyを説明しない。
    bindings = {}
    for name in LOCAL_BINDINGS:
        raw = inputs.raw(name); bindings[name] = {'size': len(raw), 'sha256': digest(raw)}
    builder = inputs.raw(LOCAL_BINDINGS[0]).decode()
    need('if (!VegaBattlePolicyCanZ(bank, TRUE))' in builder, 'Z policy注入がない')
    bridge = inputs.raw(LOCAL_BINDINGS[1]).decode()
    local_units = {
        LOCAL_BINDINGS[1]: [function_unit(bridge, x) for x in ('VegaBattlePolicyCanZ', 'VegaBattlePolicyMarkZ')],
        LOCAL_BINDINGS[2]: [function_unit(inputs.raw(LOCAL_BINDINGS[2]).decode(), 'deliver_gift')],
    }
    return {'schema_version': 1, 'source_repository': 'kapibarasan000/CFRU-JP',
            'source_commit': lock['configured_commit'], 'sources': sources,
            'local_bindings': bindings, 'local_units': local_units, 'input_receipts': receipts,
            'scope_ja': '固定原文の静的監査。候補の各consumerが実行済みという意味ではない。',
            'new_native_runs': 0, 'arm_builds': 0, 'rom_changes': 0}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--consumer-root', type=Path, required=True)
    parser.add_argument('--additional-root', type=Path, required=True)
    args = parser.parse_args()
    result = capture(args.consumer_root, args.additional_root, Inputs())
    output = ROOT / OUTPUT; raw = stable(result)
    if not output.exists() or output.read_bytes() != raw:
        output.write_bytes(raw)
    print(json.dumps({'status': 'PASS_SOURCE_SNAPSHOT', 'sources': len(result['sources']),
                      'output': OUTPUT, 'bytes': len(raw), 'sha256': digest(raw), 'new_native_runs': 0}))

if __name__ == '__main__':
    main()
