#!/usr/bin/env python3
"""T04変換器の実操作・固定上流宣言からeffect由来を分類する。新規nativeなし。"""
from __future__ import annotations
import ast
from collections import Counter
import importlib.util
import json
import re
import sys
sys.dont_write_bytecode = True
from pr16_candidate_wiki_inputs import Inputs, STATE, digest, need, stable

LOWERING = 'tools/engine/cfru_move_effect_lowering.py'
SELF = 'scripts/pr16_candidate_wiki_effect_origin.py'
DEFERRED = 'DEFERRED_AUDIT'
T04_KEY_ALIASES = {470: 'MOVE_KEY_SOUL_BITE', 509: 'MOVE_KEY_DARK_SNIPE'}


def load_lowering(inputs: Inputs):
    raw = inputs.raw(LOWERING)
    spec = importlib.util.spec_from_file_location('_wiki_t04_lowering', inputs.path(LOWERING))
    need(spec is not None and spec.loader is not None, 'T04変換器を読めない')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    need(digest(inputs.raw(LOWERING)) == digest(raw), 'T04変換器の読取中変更')
    return module, raw


def python_proof(raw: bytes, symbol: str) -> dict:
    text = raw.decode('utf-8'); lines = text.splitlines(keepends=True)
    nodes = [n for n in ast.parse(text).body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == symbol]
    need(len(nodes) == 1, 'Python source定義が欠落/複数: ' + symbol)
    node = nodes[0]
    unit = ''.join(lines[node.lineno - 1:node.end_lineno]).encode()
    return {'path': LOWERING, 'symbol': symbol, 'start_line': node.lineno, 'end_line': node.end_lineno,
            'file_sha256': digest(raw), 'unit_sha256': digest(unit), 'evidence': 'GENERATED_CANONICAL'}


def classify(commands: list[str], queries: list[str]) -> dict:
    """単なるeffect ID一致ではなく、実際の変換結果を分類する。"""
    need(bool(commands) and all(isinstance(c, str) and c for c in commands), 'adapter命令欠落')
    need(len(set(queries)) == len(queries), 'query操作重複')
    instructions = [c for c in commands if not c.endswith(':')]
    local_calls = [c.split()[1] for c in instructions if c.startswith('callasm ')]
    targets = sorted(set(re.findall(r'\bBS_[A-Za-z0-9_]+\b', '\n'.join(commands))))
    if local_calls:
        need(set(local_calls) == {'VegaMoveEffectPrepare'}, '未分類local callasm')
        kind = 'PROJECT_DYNAMIC_PREPARE_ADAPTER'
    elif len(instructions) == 1 and instructions[0].startswith('goto BS_'):
        kind = 'UPSTREAM_SCRIPT_DELEGATE'
    elif len(instructions) == 2 and instructions[0].startswith('setmoveeffect ') and instructions[1] == 'goto BS_STANDARD_HIT':
        kind = 'UPSTREAM_EFFECT_PARAMETER_ADAPTER'
    else:
        kind = 'PROJECT_COMPOSED_SCRIPT'
    return {'script_origin': kind, 'upstream_script_symbols': targets, 'local_callasm_symbols': local_calls,
            'project_central_query_operations': queries, 'has_project_central_query': bool(queries),
            'new_engine_opcode_claimed': False, 'candidate_compiled_callgraph': DEFERRED,
            'native_acceptance': DEFERRED}


def audit(model: dict, lowering, raw: bytes) -> dict:
    moves = model['moves']; by_id = {r['id']: r for r in moves}
    need(len(by_id) == len(moves), 'effect監査move ID重複')
    need(all(type(r['id']) is int and r['id'] >= 0 for r in moves), 'effect監査move ID不正')
    need(all(type(r['effect_id']) is int and 0 <= r['effect_id'] < 65536 for r in moves), 'effect ID不正')
    expected = lowering.EXPECTED_MOVE_PLANS
    need(set(expected) <= set(by_id), 'T04対象技の欠落')
    patches = lowering._required_patches()
    need(len({p['id'] for p in patches}) == len(patches), 'native patch ID重複')
    patch_rows = [{'id': p['id'], 'path': p['path'], 'expected_count': p['expected_count'],
                   'consumers': p['consumers'], 'needle_sha256': digest(p['needle'].encode()),
                   'replacement_sha256': digest(p['replacement'].encode()),
                   'installed_on_candidate': DEFERRED} for p in patches]
    result = []
    for move in moves:
        mid = move['id']
        row = {'move_id': mid, 'move_key': move['key'], 'candidate_effect_id': move['effect_id'],
               'candidate_evidence': move['evidence'], 'candidate_row_sha256': move['row_sha256'],
               'stage61_effect_id_comparison_not_handler_history': move['effect_novelty'],
               'native_acceptance': DEFERRED, 'new_native_runs': 0}
        if mid in expected:
            need(move['key'] == T04_KEY_ALIASES.get(mid, f'MOVE_KEY_VEGA_{mid}'), 'T04 stable key不一致')
            operations = expected[mid]; commands, eid = lowering._compile_commands(mid, operations)
            need(eid == move['effect_id'], 'T04 runtime effectと候補row不一致: ' + str(mid))
            queries = [op for op in operations if op in lowering.QUERY_OPERATIONS]
            row.update(status='T04_SOURCE_ADAPTER_CLASSIFIED', source_kind='PROJECT_GENERATED_ADAPTER',
                adapter_symbol=f'VegaMoveEffectScript_{mid}', operations=list(operations),
                field_operations=[op for op in operations if op in lowering.FIELD_OPERATIONS],
                script_commands=commands, runtime_effect_symbol=lowering.RUNTIME_EFFECT_SYMBOLS[eid],
                source_evidence='GENERATED_CANONICAL', origin=classify(commands, queries))
        elif mid == 0:
            row.update(status='MOVE_NONE_NOT_PLAYABLE', source_kind='SENTINEL')
        else:
            canonical = move['canonical_fields']; fields = canonical.get('fields', {})
            symbol = fields.get('effect')
            if symbol in model['source_model']['effect_ids']:
                need(model['source_model']['effect_ids'][symbol] == move['effect_id'], '固定上流effect宣言と候補の差分を未分類: ' + str(mid))
                row.update(status='LOCKED_UPSTREAM_EFFECT_DECLARATION', source_kind='UPSTREAM_DECLARATION',
                    upstream_move_symbol=canonical['source_symbol'], runtime_effect_symbol=symbol,
                    source_repository=model['source_model']['source_repository'],
                    source_commit=model['source_model']['source_commit'], source_evidence='GENERATED_CANONICAL',
                    full_handler_lineage=DEFERRED,
                    reason_ja='固定上流の技宣言と現候補effect値を照合。effect共通でもmove ID分岐・local patch・全呼出経路の同一性は主張しない。')
            else:
                row.update(status='UNRESOLVED_SOURCE_LINEAGE', source_kind=DEFERRED,
                    reason_ja='上流技宣言にもT04専用変換対象にも結合できない。表示名/同じeffect IDだけで既存流用と断定しない。')
        move['effect_origin'] = row
        result.append(row)
    return {'schema_version': 1, 'candidate': model['candidate'], 'records': result,
            'summary': {'effect_origin_records': len(result), 't04_source_adapters': len(expected),
                        'effect_origin_states': dict(sorted(Counter(r['status'] for r in result).items())),
                        't04_script_origins': dict(sorted(Counter(r['origin']['script_origin'] for r in result if 'origin' in r).items())),
                        't04_adapters_with_central_queries': sum(r.get('origin', {}).get('has_project_central_query', False) for r in result),
                        't04_required_source_patch_contracts': len(patch_rows)},
            'source_proofs': [python_proof(raw, s) for s in ('_compile_commands', '_required_patches', 'lower_t04_move_effects')],
            'source_patch_contracts': patch_rows,
            'upstream_source_bindings': model['source_model']['source_bindings'],
            'unresolved_move_ids': [r['move_id'] for r in result if r['status'] == 'UNRESOLVED_SOURCE_LINEAGE'],
            'full_handler_history_complete': False, 'candidate_native_acceptance': DEFERRED,
            'new_native_runs': 0, 'rom_changes': 0,
            'scope_ja': '現在の固定上流宣言とlocal変換sourceの構造的由来。Git全履歴・候補compiled全callerの証明ではない。T04の新規アダプターと新しいengine opcodeを区別する。'}


def enrich(model: dict, inputs: Inputs) -> dict:
    inputs.raw(SELF)
    registry = {int(r['id']): r['move_key'] for r in inputs.csv('manifests/move_ids.csv')}
    need(all(registry.get(r['id']) == r['key'] for r in model['moves']), '技registry stable key不一致')
    lowering, raw = load_lowering(inputs)
    value = audit(model, lowering, raw); model['effect_origin_audit'] = value
    model['followup_audit']['summary'].update(value['summary'])
    remaining = model['followup_audit']['remaining_work_ja']
    targets = [i for i, s in enumerate(remaining) if s.startswith('既存effect流用と新規handler')]
    need(len(targets) == 1, 'effect残件のanchor不一致')
    remaining[targets[0]] = ('T04全70アダプターのsource由来を分類済み。残りは未結合技' +
        str(value['unresolved_move_ids']) + 'の由来、上流宣言技のlocal patch/全handler履歴、候補compiled dispatch対応。source分類をnative受入にしない。')
    model['source_bindings'].update({k: v for k, v in inputs.bindings.items() if k != STATE})
    return model


def append_pages(files: dict[str, bytes], model: dict) -> None:
    from pr16_candidate_wiki_render import Link, jsonblock, table
    value = model['effect_origin_audit']
    intro = '# 技effectのsource由来\n\n[Wiki入口](README.md) / [全技](MOVE_INDEX.md)\n\n'
    intro += '候補 SHA-256 `' + model['candidate']['sha256'] + '`。effect ID比較ではなく、T04変換器の実命令・query操作を分類します。\n\n'
    intro += value['scope_ja'] + '\n\n## 集計\n\n' + jsonblock(value['summary'])
    intro += '\n## T04の専用アダプター\n\n'
    intro += table(['技', 'source由来', '既存script呼出', '独自central query'],
        [(Link(f'[{r["move_id"]}](moves/{r["move_id"]}.md)'), r['origin']['script_origin'],
          r['origin']['upstream_script_symbols'], r['origin']['project_central_query_operations'])
         for r in value['records'] if 'origin' in r])
    intro += '\n## 未結合・未検証\n\n未結合技: ' + str(value['unresolved_move_ids']) + '\n\n'
    intro += '固定上流のeffect宣言一致は、全handlerが無改変である証拠ではありません。compiled dispatch・move ID分岐・patchの実適用とnative受入は別です。\n\n'
    intro += jsonblock(value['source_proofs'])
    files['EFFECT_ORIGIN_AUDIT.md'] = intro.encode()
    files['data/effect_origins.jsonl'] = b''.join((json.dumps(r, ensure_ascii=False, sort_keys=True, separators=(',', ':'))+'\n').encode() for r in value['records'])
    files['data/effect_origin_audit.json'] = stable({k: v for k, v in value.items() if k != 'records'})
    for row in model['moves']:
        name = f'moves/{row["id"]}.md'
        files[name] += ('\n## effectのsource由来（新規nativeなし）\n\n[由来監査](../EFFECT_ORIGIN_AUDIT.md)\n\n'+jsonblock(row['effect_origin'])).encode()
    for name in ('README.md', 'MOVE_INDEX.md', 'CODEX_INDEX.md', 'RUNTIME_LIMITATIONS.md'):
        files[name] += '\n[技effectのsource由来・残件](EFFECT_ORIGIN_AUDIT.md)\n'.encode()
