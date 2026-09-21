#!/usr/bin/env python3
"""汎用Zの実際のsplit分岐を固定sourceと候補tableに結合する。実行受入は付与しない。"""
from __future__ import annotations
from collections import Counter
import re
import struct
import sys
sys.dont_write_bytecode = True
from pr16_candidate_wiki_inputs import Inputs, STATE, BASE, digest, identity, need, stable
from pr16_candidate_wiki_consumers import load, key_for

INVENTORY = 'content/modernization/pr16_wiki_remaining_source_inventory.json'
PROFILE = 'config/cfru_vega_minimal.h'
# CFRU-JP@e24a16fe assembly/data/move_tables.s:11 (blob efadafd029731238469d204dbb0705a53a46efcd).
MOVE_TABLES_TERMIN = 0xFEFE


def physicality_symbols(text: str) -> list[str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    need(lines and lines[0] == 'gMovesThatChangePhysicality:', 'physicality label不一致')
    names = []
    for line in lines[1:]:
        match = re.fullmatch(r'\.hword\s+(MOVE_[A-Z0-9_]+)', line)
        need(match is not None, 'physicality directive未対応')
        names.append(match[1])
    need(names and names[-1] == 'MOVE_TABLES_TERMIN', 'physicality終端なし')
    names.pop()
    need(names and 'MOVE_TABLES_TERMIN' not in names and len(names) == len(set(names)), 'physicality重複/中間終端')
    return names


def aligned_matches(raw: bytes, pattern: bytes, alignment: int, limit: int = 64) -> list[int]:
    need(bool(pattern) and alignment in (2, 4), '署名/align不正')
    found = []; start = 0
    while True:
        pos = raw.find(pattern, start)
        if pos < 0:
            return found
        start = pos + 1
        if pos % alignment == 0:
            found.append(pos)
            need(len(found) <= limit, '署名候補が過度に曖昧')


def table_binding(raw: bytes, ids: list[int]) -> dict:
    need(ids and len(ids) == len(set(ids)) and all(type(x) is int and 0 < x < MOVE_TABLES_TERMIN for x in ids), 'physicality move ID不正')
    signature = struct.pack('<'+'H'*(len(ids)+1), *ids, MOVE_TABLES_TERMIN)
    matches = []
    for pos in aligned_matches(raw, signature, 2):
        address = BASE+pos
        references = aligned_matches(raw, struct.pack('<I', address), 4)
        matches.append({'address': f'0x{address:08X}',
                        'aligned_pointer_value_sites': [f'0x{BASE+p:08X}' for p in references]})
    return {'candidate_move_ids':ids, 'signature_sha256':digest(signature), 'signature_size':len(signature), 'terminator':MOVE_TABLES_TERMIN,
            'terminator_source':{'path':'assembly/data/move_tables.s','line':11,'definition':'.equ MOVE_TABLES_TERMIN, 0xFEFE'},
            'matches':matches, 'status':'BYTE_TABLE_FOUND' if matches else 'NO_CANDIDATE_BYTE_MATCH',
            'evidence':'EXACT_CANDIDATE_ROM', 'pointer_values_are_not_callgraph_proof':True,
            'compiled_consumer_entry_binding':'DEFERRED_AUDIT', 'candidate_native_acceptance':'DEFERRED_AUDIT'}


def split_rule(key: str, category: int, physicality_keys: set[str], old_split: bool = False) -> dict:
    need(category in (0,1,2), 'move分類不正')
    common = {'source_rule_evidence':'GENERATED_CANONICAL', 'candidate_native_acceptance':'DEFERRED_AUDIT',
              'caller':'GetTypeBasedZMove -> CalcMoveSplit(bank, move, bank)', 'same_bank_arguments':True}
    if category == 2:
        return dict(common, rule='STATUS_SENTINEL_NOT_DAMAGE_SPLIT', possible_categories=[],
                    explanation_ja='変化技はCanUseZMoveが0xFFFFを返す。攻撃Zのsplit算術に入れない。')
    tera = key in {'MOVE_KEY_TERABLAST', 'MOVE_KEY_TERASTARSTORM'}
    if key in physicality_keys or tera:
        return dict(common, rule='TERA_CONDITIONAL_STAT_COMPARISON' if tera else 'STAT_STAGE_COMPARISON',
                    possible_categories=[0,1], tie_category=1,
                    condition='TeraTypeActive(bank)' if tera else 'gMovesThatChangePhysicality membership',
                    comparison='stage-adjusted spAttack >= stage-adjusted attack -> SPECIAL; otherwise PHYSICAL',
                    inactive_tera_fallback=('TYPE_BASED_OLD_SPLIT' if old_split else 'CANDIDATE_BASE_SPLIT') if tera else None,
                    explanation_ja='攻撃・特攻に各能力段階を適用して比較。同値なら特殊。Tera条件付きの技は非Tera時には基礎分類へ戻る。')
    if old_split:
        return dict(common, rule='OLD_TYPE_BASED_SPLIT', possible_categories=[0,1],
                    explanation_ja='OLD_MOVE_SPLIT有効時はtype<炎が物理、それ以外が特殊。')
    shell = key == 'MOVE_KEY_SHELLSIDEARM'
    return dict(common, rule='SHELL_SIDE_ARM_SELF_BANK_BASE_SPLIT' if shell else 'CANDIDATE_BASE_SPLIT',
                possible_categories=[category],
                explanation_ja=('bankAtk == bankDefなので相手比較分岐を通らず候補tableの分類を使う。' if shell
                                else '候補tableの物理/特殊をそのまま使う。両方へ自由に変換できる意味ではない。'))


def refine(model: dict, source, inventory: dict, raw: bytes, profile: str) -> dict:
    need(inventory['candidate'] == model['candidate'] == identity(raw), 'physicality候補不一致')
    need(inventory['source_commit'] == source.value['source_commit'], 'physicality source-lock不一致')
    saved = inventory['units']['CalcMoveSplit']
    need(saved['text'] == source.code('CalcMoveSplit') and saved['proof'] == source.proof('CalcMoveSplit'), 'split原文不一致')
    code = source.code('CalcMoveSplit')
    for required in ('spAttack >= attack', 'bankAtk != bankDef', 'TeraTypeActive(bankAtk)', 'SPLIT(move) != SPLIT_STATUS'):
        need(required in code, 'split分岐契約変更: '+required)
    need('CalcMoveSplit(bank, move, bank)' in source.code('GetTypeBasedZMove'), 'Z caller引数変更')
    need('OLD_MOVE_SPLIT' not in source.symbols and not re.search(r'^\s*#\s*define\s+OLD_MOVE_SPLIT\b',profile,re.M), 'OLD_MOVE_SPLITが有効')
    symbols = physicality_symbols(inventory['physicality_table']['text'])
    by_key = {r['key']:r for r in model['moves']}
    keys = {key_for(symbol) for symbol in symbols}
    need(keys <= set(by_key), 'physicality stable key欠落')
    ids = [by_key[key_for(symbol)]['id'] for symbol in symbols]
    proof = table_binding(raw, ids)
    records = []
    for move in model['moves']:
        rule = split_rule(move['key'], move['category_id'], keys)
        row = move['generic_z']; row['split_audit'] = rule
        if row['status'] == 'DAMAGE_MOVE_SOURCE_RULE':
            row['targets'] = [target for target in row['targets'] if target['category_id'] in rule['possible_categories']]
            row['runtime_split_scope_ja'] = rule['explanation_ja']
        records.append(row)
    model['consumer_audit']['generic_z']['records'] = records
    result = {'schema_version':1,'candidate':model['candidate'],
              'physicality_source':inventory['physicality_table'], 'physicality_binding':proof,
              'physicality_move_keys':[key_for(s) for s in symbols],
              'rule_counts':dict(sorted(Counter(r['split_audit']['rule'] for r in records).items())),
              'records':len(records), 'old_move_split_enabled_in_locked_inputs':False,
              'source_proofs':[source.proof('CalcMoveSplit'),source.proof('GetTypeBasedZMove')],
              'new_native_runs':0,
              'limit_ja':'候補table署名とaligned pointer値を照合するが、命令の逆アセンブルによる全caller同定や全modeのnative受入へ昇格しない。'}
    model['runtime_z_audit'] = result
    summary = model['followup_audit']['summary']
    summary.update(runtime_z_records=len(records), runtime_z_rules=result['rule_counts'],
                   physicality_candidate_table_matches=len(proof['matches']))
    model['followup_audit']['remaining_work_ja'] = [
        ('汎用Zの実行時split規則・固定physicality表・候補署名を照合済み。残りはcompiled consumer入口のcallgraph同定であり、table/pointer値一致だけを実行証拠にしない。'
         if text.startswith('汎用Zの静的対応') else text)
        for text in model['followup_audit']['remaining_work_ja']]
    return model


def enrich(model: dict, inputs: Inputs, raw: bytes) -> dict:
    source = load(inputs)
    refine(model, source, inputs.json(INVENTORY), raw, inputs.raw(PROFILE).decode())
    inputs.raw('scripts/pr16_candidate_wiki_runtime_z.py')
    model['source_bindings'].update({name:value for name,value in inputs.bindings.items() if name != STATE})
    return model


def append_pages(files: dict[str,bytes], model: dict) -> None:
    from pr16_candidate_wiki_render import jsonblock, table, Link
    audit = model['runtime_z_audit']
    body = '# 汎用Zの実行時分類監査\n\n[Wiki入口](README.md) / [Z一覧](Z_MOVE_INDEX.md)\n\n'
    body += '候補SHA-256 `'+model['candidate']['sha256']+'`。技の元分類、条件付きの変化、候補署名を区別します。\n\n'
    body += '## 分岐別件数\n\n'+table(['分類規則','全技行数'],audit['rule_counts'].items())
    body += '\nシェルアームズはZ callerのbank引数が同じため相手比較を使いません。フォトンゲイザー等は能力段階適用後を比較し、同値なら特殊です。Tera条件付きの技は非Tera時に元分類へ戻ります。\n\n'
    body += table(['技','規則','可能な分類','候補Z変換先ID'],[
        (Link(f'[{r["id"]}](moves/{r["id"]}.md)'),r['generic_z']['split_audit']['rule'],
         r['generic_z']['split_audit']['possible_categories'],[x['move_id'] for x in r['generic_z']['targets']])
        for r in model['moves'] if r['generic_z']['split_audit']['rule'] not in {'CANDIDATE_BASE_SPLIT','STATUS_SENTINEL_NOT_DAMAGE_SPLIT'}])
    body += '\n## 短いtable署名の扱い\n\n2技+終端の6byteを2byte境界で検索し、候補内の4byte境界pointer値を別に記録します。pointer値はcallgraphや実行済みの証明ではありません。\n\n'+jsonblock(audit)
    files['RUNTIME_Z_AUDIT.md']=body.encode()
    files['data/runtime_z_audit.json']=stable(audit)
    for name in ('README.md','Z_MOVE_INDEX.md','CONSUMER_AUDIT.md','RUNTIME_LIMITATIONS.md','CODEX_INDEX.md'):
        files[name]+='\n[汎用Zの実行時split・候補table監査](RUNTIME_Z_AUDIT.md)\n'.encode()
