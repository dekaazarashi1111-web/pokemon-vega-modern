#!/usr/bin/env python3
"""保存ELFの全body一致と技511の固定由来をWikiへ結合する。実行受入ではない。"""
from __future__ import annotations
import ast
from collections import Counter
import copy
from pr16_candidate_wiki_inputs import BASE, STATE, Inputs, Rom, digest, identity, need, stable
from pr16_candidate_wiki_link_graph import structural_graph
from pr16_wiki_saved_link_snapshot import load, OUTPUT

SELF = 'scripts/pr16_candidate_wiki_saved_link.py'
EXACT = 'EXACT_CANDIDATE_SYMBOL_BODY'
DIFFERS = 'CANDIDATE_BODY_DIFFERS'
DEFERRED = 'DEFERRED_AUDIT'
BATTLE_FIELDS = (('effect','effect_id'),('power','power'),('type','type_id'),('accuracy','accuracy'),
    ('pp','pp'),('secondary','secondary_percent'),('target','target_id'),('priority','priority'),
    ('flags','flags'),('z_move_power','z_power'),('split','category_id'),('z_move_effect','z_effect'))


def verify_symbol(row: dict, raw: bytes) -> None:
    need(row['native_acceptance'] == DEFERRED and row['source_equivalence_proven'] is False, 'symbolをnative/source受入に昇格しない')
    status = row['status']
    need(status in {EXACT,DIFFERS,'MISSING_SAVED_SYMBOL','AMBIGUOUS_SAVED_SYMBOL',
        'SYMBOL_WITHOUT_PROVEN_EXTENT','SYMBOL_WITHOUT_ALLOCATED_BODY','UNSUPPORTED_SYMBOL_TYPE',
        'SYMBOL_OUTSIDE_CANDIDATE'}, 'symbol状態不正')
    if status not in (EXACT, DIFFERS):
        return
    address, size = row['address'], row['size']; symbol = row['elf_symbol']
    need(type(address) is type(size) is int and 0 < size <= 65536, 'symbol型/size不正')
    need(symbol['type'] in (1,2) and symbol['size'] == size, 'symbol type/extent不一致')
    expected = symbol['address'] & ~1 if symbol['type'] == 2 else symbol['address']
    need(address == expected and BASE <= address <= BASE + len(raw) - size, 'symbol address範囲外')
    need(symbol['symbol'] == row['symbol'], 'symbol名不一致')
    actual = digest(raw[address-BASE:address-BASE+size])
    need(actual == row['candidate_sha256'], '現候補symbol body hash不一致')
    need((row['saved_sha256'] == actual) == (status == EXACT), 'symbol一致状態の誤分類')


def verify_calls(calls: list[dict], symbols: dict) -> None:
    for call in calls:
        names = call['saved_symbol_names']; matched = call['candidate_body_matched_names']
        need(names == sorted(set(names)) and matched == sorted(set(matched)), 'callee名重複/非決定順')
        need(set(names) <= symbols.keys(), 'callee symbol未保存')
        for name in names:
            row = symbols[name]; info = row['elf_symbol']
            need(info['type'] == 2 and info['address'] & ~1 == call['target'], 'callee address不一致')
        need(matched == [n for n in names if symbols[n]['status'] == EXACT], '不一致calleeを現候補名へ昇格')


def verify_graph(name: str, graph: dict, row: dict, raw: bytes, symbols: dict) -> dict:
    need(row['status'] == EXACT and row['elf_symbol']['type'] == 2, '未結合bodyからgraphを命名しない')
    verify_calls(graph['direct_calls'], symbols)
    start = row['address']
    actual = structural_graph(Rom(raw), start, start, start+row['size'])
    actual['saved_elf_full_extent_verified'] = True
    compact = {k:v for k,v in actual.items() if k != 'nodes'}
    expected = copy.deepcopy(graph)
    expected['direct_calls'] = [{k:c[k] for k in ('site','target')} for c in expected['direct_calls']]
    need(compact == expected, '候補graphと保存report不一致: '+name)
    actual['direct_calls'] = copy.deepcopy(graph['direct_calls'])
    actual['saved_symbol'] = name
    actual['extent_basis'] = 'SAVED_ELF_ST_SIZE_AND_FULL_CANDIDATE_BODY_SHA256'
    return actual


def move511_lineage(rows: dict, moves: list[dict], policy: dict) -> dict:
    need(type(policy.get('frozen_vega_end')) is int and policy['frozen_vega_end'] == 511
         and policy['frozen_vega_start'] == 0 and policy['append_start'] == 512, 'Vega frozen範囲変更')
    choice = policy['duplicate_name_resolution']['1']
    need(choice == {'duplicate_vega_ids':[1,511], 'cfru_symbol':'MOVE_POUND', 'canonical_vega_id':1,
        'policy':'CFRU_ALIAS_TO_LOWEST_VEGA_ID_KEEP_ALL_FROZEN_ROWS'}, 'Pound重複解決規約変更')
    one, duplicate = rows['1'], rows['511']
    need(one['id'] == one['vega_id'] == 1 and duplicate['id'] == duplicate['vega_id'] == 511, '保存技ID不一致')
    need(one['cfru_symbol'] == 'MOVE_POUND' and one['move_key'] == 'MOVE_KEY_POUND'
         and one['classification'] == 'VEGA_CFRU_CANONICAL', 'Pound正本不一致')
    need(duplicate['classification'] == 'VEGA_COMPAT_DUPLICATE' and duplicate['move_key'] == 'MOVE_KEY_VEGA_511', '511互換row不一致')
    need(duplicate['cfru_symbol'] is None and duplicate['cfru_source_id'] is None
         and duplicate['effect_adapter'] is None, '511を上流別名/T04へ昇格しない')
    need(duplicate['effect_map']['mapping_kind'] == 'VEGA_ROM_POINTER'
         and duplicate['effect_map']['symbol'] is None and duplicate['effect_map']['script_symbol'] is None
         and duplicate['effect_map']['id'] == duplicate['battle']['effect'], '511元effect由来不一致')
    need(rows['aliases'] == [{'canonical_id':1,'canonical_key':'MOVE_KEY_POUND','cfru_source_id':1,
        'cfru_symbol':'MOVE_POUND','mapping':'VEGA_FROZEN_EXACT_NAME'}], '511をMOVE_POUND aliasへ付け替えない')
    by_id = {r['id']:r for r in moves}
    need(len(by_id) == len(moves) and {1,511} <= by_id.keys(), '現候補技重複/欠落')
    for saved in (one, duplicate):
        current = by_id[saved['id']]
        need(current['key'] == saved['move_key'], '技stable key不一致')
        need(set(saved['battle']) == {a for a,b in BATTLE_FIELDS}, '保存battle field変更')
        need(all(type(current[b]) is int and current[b] == saved['battle'][a] for a,b in BATTLE_FIELDS), '候補12fieldと保存由来row不一致')
        encoded = bytes(saved['battle'][a] & 255 for a,b in BATTLE_FIELDS)
        need(digest(encoded) == current['row_sha256'], '技12byte hash不一致')
    differences = [a for a,b in BATTLE_FIELDS if one['battle'][a] != duplicate['battle'][a]]
    return {'status':'FROZEN_VEGA_COMPAT_DUPLICATE_BOUND','move_id':511,'move_key':'MOVE_KEY_VEGA_511',
        'source_kind':'FROZEN_VEGA_ROW','canonical_pound_id':1,'canonical_pound_alias_does_not_target_511':True,
        'source_model':rows['model_binding'],'source_row_sha256':digest(stable(duplicate)),
        'candidate_row_sha256':by_id[511]['row_sha256'],'candidate_fields':duplicate['battle'],
        'different_fields_from_canonical_pound':differences,'saved_original_effect_mapping':duplicate['effect_map'],
        'full_handler_lineage':DEFERRED,'candidate_compiled_handler_execution':DEFERRED,'native_acceptance':DEFERRED,
        'reason_ja':'511は凍結Vega行を保持する互換重複。MOVE_POUNDは1だけへaliasする。元modelのVEGA_ROM_POINTERを記録するが、現候補でその旧pointerを実行するとは主張しない。'}


def source_proof(inputs: Inputs, path: str, names: tuple[str,...]) -> list[dict]:
    raw = inputs.raw(path); text = raw.decode(); lines = text.splitlines(keepends=True)
    nodes = [n for n in ast.parse(text).body if isinstance(n,ast.FunctionDef)]
    result = []
    for name in names:
        selected = [n for n in nodes if n.name == name]; need(len(selected) == 1, 'source関数定義欠落/重複')
        node = selected[0]; unit = ''.join(lines[node.lineno-1:node.end_lineno]).encode()
        result.append({'path':path,'symbol':name,'file_sha256':digest(raw),'unit_sha256':digest(unit),
                       'start_line':node.lineno,'end_line':node.end_lineno,'evidence':'GENERATED_CANONICAL'})
    return result


def enrich(model: dict, inputs: Inputs, raw: bytes) -> dict:
    for path in (SELF,'scripts/pr16_wiki_saved_link_snapshot.py','scripts/pr16_wiki_elf_symbols.py'):
        inputs.raw(path)
    saved = load(inputs)
    need(saved['candidate'] == model['candidate'] == identity(raw), '保存ELF候補identity不一致')
    meta_raw = inputs.raw(saved['metadata']['path'])
    need(len(meta_raw) == saved['metadata']['size'] and digest(meta_raw) == saved['metadata']['sha256'], 'Stage06 metadata変更')
    meta = inputs.json(saved['metadata']['path'])
    need({r['linked_object']['sha256'] for r in meta['upstream_runs']} == {saved['elf']['sha256']}, 'Stage06とELF原本hash不一致')
    need(saved['new_native_runs'] == saved['arm_builds'] == saved['rom_changes'] == 0
         and saved['runtime_reachability_proven'] is False and saved['all_indirect_edges_resolved'] is False, '保存読取scope不正')
    all_symbols = dict(saved['direct_callees'])
    for name,row in saved['symbols'].items():
        need(name not in all_symbols or all_symbols[name] == row, 'symbol重複定義不一致')
        all_symbols[name] = row
    for name,row in all_symbols.items():
        need(name == row['symbol'], 'symbol key不一致'); verify_symbol(row, raw)
    need(set(saved['graphs']) == {n for n,r in saved['symbols'].items() if r['status'] == EXACT and r['elf_symbol']['type'] == 2}, 'graph集合不一致')
    graphs = {n:verify_graph(n,g,saved['symbols'][n],raw,all_symbols) for n,g in saved['graphs'].items()}
    config = inputs.json('config/move_port.json')
    lineage = move511_lineage(saved['move_rows'], model['moves'], config['mapping_policy'])
    lineage['source_proofs'] = source_proof(inputs, 'scripts/build_move_port.py', ('build_move_model','_vega_battle','validate_move_model'))
    lineage['policy_binding'] = dict(path='config/move_port.json', **inputs.bindings['config/move_port.json'])
    audit = model['effect_origin_audit']; row = next(r for r in audit['records'] if r['move_id'] == 511)
    need(row['status'] == 'UNRESOLVED_SOURCE_LINEAGE', '511既存受入への上書き禁止')
    row.update(lineage)
    audit['unresolved_move_ids'] = [r['move_id'] for r in audit['records'] if r['status'] == 'UNRESOLVED_SOURCE_LINEAGE']
    audit['summary']['effect_origin_states'] = dict(sorted(Counter(r['status'] for r in audit['records']).items()))
    model['followup_audit']['summary'].update(audit['summary'])
    summary = {'saved_elf_requested_symbols':len(saved['symbols']),
        'saved_elf_target_states':dict(sorted(Counter(r['status'] for r in saved['symbols'].values()).items())),
        'saved_elf_exact_function_graphs':len(graphs),'saved_elf_direct_call_sites':sum(len(g['direct_calls']) for g in graphs.values()),
        'saved_elf_exact_named_call_sites':sum(bool(c['candidate_body_matched_names']) for g in graphs.values() for c in g['direct_calls']),
        'frozen_compatibility_move_lineages':1}
    value = {'schema_version':1,'candidate':model['candidate'],'summary':summary,'symbols':saved['symbols'],
        'direct_callees':saved['direct_callees'],'graphs':graphs,'move_511':lineage,'saved_elf':saved['elf'],
        'metadata':saved['metadata'],'capture_receipt':saved['capture_receipt'],
        'new_native_runs':0,'arm_builds':0,'rom_changes':0,'complete_callgraph':False,
        'scope_ja':'保存ELFの宣言extent全byteと現候補を比較。一致したbodyだけに保存名を結合し、BL先も全body一致を要求する。条件分岐は構造上の両側で、実到達・間接辺・source/macros一致・native受入は別。差分bodyを旧関数と同一と断定しない。'}
    model['saved_link_audit'] = value
    model['followup_audit']['summary'].update(summary)
    replacements = {
        '追加野生95行': '追加野生95行・collection配布18/Floette1・raid292の初期技source規則に加え、GiveBoxMonInitialMoveset/GiveMoveToBoxMon・ScriptGiveMon/CreateEggの全body一致を確認。残りは全通常野生header/既存story配布、CreateBoxMon/CreateWildMon/GiveEggFromDaycareの差分body・マクロ・生成後form/custom技。実生成技受入とは別。',
        '汎用Zのsplit/候補表': '保存ELFでGetTypeBasedZMove→CalcMoveSplitの直接BLと両関数全body一致を確認。CanUseZMove/HandleInputChooseMoveは保存bodyとの差分あり。残りはその差分の由来・間接辺・現在の実到達条件。元3入口graphや受入nativeは再実行しない。',
        '夢特性パッチは全1671slot': '夢特性パッチの全1671slot条件・BP供給sourceに加え、field入口と3 UI callbackの全body一致を確認。GetAbility1/2/GetHiddenAbility/GetMonAbility・GiveEggFromDaycareは保存bodyとの差分あり、DetermineEggAbilityは独立symbolなし。残りは差分accessor・育て屋・通常初回供給caller・実使用条件。native未受入のまま。',
        'T04全70アダプター': 'T04全70アダプターのsource由来、技511の凍結Vega互換重複由来・候補12byte、VegaResolveMoveEffectScript/VegaMoveEffectPrepareの全body一致を確認。技由来の未結合は解消。残りは上流宣言技のlocal patch/全handler履歴・dispatch間接辺と個別handler対応。source/byte一致をnative受入にしない。'}
    todo = model['followup_audit']['remaining_work_ja']
    for prefix,text in replacements.items():
        selected = [i for i,s in enumerate(todo) if s.startswith(prefix)]
        need(len(selected) == 1, '残件anchor不一致: '+prefix); todo[selected[0]] = text
    model['link_graph_audit']['later_saved_elf_audit'] = 'data/saved_link_audit.json'
    for name in ('runtime_z_audit','hidden_patch_audit','creation_audit','effect_origin_audit'):
        model[name]['later_saved_elf_audit'] = 'data/saved_link_audit.json'
    model['source_bindings'].update({k:v for k,v in inputs.bindings.items() if k != STATE})
    return model


def append_pages(files: dict[str,bytes], model: dict) -> None:
    from pr16_candidate_wiki_render import jsonblock, table
    value = model['saved_link_audit']
    body = '# 保存ELFの全body照合と名前付きcallee\n\n[Wiki入口](README.md) / [技511](MOVE_511_LINEAGE.md)\n\n'
    body += value['scope_ja']+'\n\n'+jsonblock(value['summary'])
    body += '\n## 31対象の同一性\n\n'+table(['保存symbol','状態','address','bytes'],
        [(n,r['status'],hex(r['address']) if 'address' in r else '未結合',r.get('size','extentなし')) for n,r in value['symbols'].items()])
    body += '\n## 名前付き直接BL（全body一致calleeだけ）\n\n'+table(['caller','site','target','一致callee'],
        [(n,hex(c['site']),hex(c['target']),c['candidate_body_matched_names']) for n,g in value['graphs'].items() for c in g['direct_calls'] if c['candidate_body_matched_names']])
    body += '\n## 残件\n\nCanUseZMoveとHandleInputChooseMove、種族accessor、CreateBoxMon/CreateWildMon/GiveEggFromDaycareは旧bodyとの差分を別途追跡します。DetermineEggAbilityは独立symbolがなく、inline化と断定しません。全handler・間接辺・通常初回供給/使用の実行受入は未完です。\n\n'
    body += '[全命令graph・不一致・原本hash・取得受入](data/saved_link_audit.json)\n\n'+jsonblock(value['capture_receipt'])
    files['SAVED_LINK_AUDIT.md'] = body.encode()
    files['data/saved_link_audit.json'] = stable(value)
    files['MOVE_511_LINEAGE.md'] = ('# 技511の凍結互換由来\n\n[技511](moves/511.md) / [技1](moves/1.md) / [effect由来](EFFECT_ORIGIN_AUDIT.md)\n\n'
        '同じ表示名でも511を1へ統合しません。flagsとZ威力も異なり、MOVE_POUNDのaliasは1のみです。旧effect pointerは保存modelの由来情報であり、現候補の実行先証明ではありません。\n\n'+jsonblock(value['move_511'])).encode()
    files['moves/511.md'] += '\n[凍結互換rowの原本・12byte照合](../MOVE_511_LINEAGE.md)\n'.encode()
    old = '今回調べた保存先に実体なし。再コンパイルや近傍prologueからの命名はしていません。'
    page = files['LINK_GRAPH_AUDIT.md'].decode(); need(page.count(old) == 1, '旧link説明anchor不一致')
    page = page.replace('## 未保存link表', '## 初回metadata監査時点のlink表')
    page = page.replace(old, '初回の限定snapshotでは実体未取得でした。後続の固定cache読取で同一hashのELFを確認済みです。[全body一致・不一致を分けた最新監査](SAVED_LINK_AUDIT.md)を参照してください。再コンパイルや近傍prologueからの命名はしていません。')
    files['LINK_GRAPH_AUDIT.md'] = page.encode()
    for name in ('README.md','CODEX_INDEX.md','RUNTIME_LIMITATIONS.md','RUNTIME_Z_AUDIT.md','Z_MOVE_INDEX.md',
                 'HIDDEN_PATCH_AUDIT.md','HIDDEN_ABILITY_INDEX.md','CREATION_MOVESET_AUDIT.md','EFFECT_ORIGIN_AUDIT.md'):
        files[name] += '\n[保存ELFの全body照合・名前付きcallee・未解決差分](SAVED_LINK_AUDIT.md)\n'.encode()
