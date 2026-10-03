#!/usr/bin/env python3
"""候補tableと固定consumer原文を結合する静的監査。native受入を新規付与しない。"""
from __future__ import annotations
import ast
from collections import Counter
import re
import sys
sys.dont_write_bytecode = True
from pr16_candidate_wiki_inputs import Inputs, STATE, digest, need, stable
from pr16_wiki_source_snapshot import OUTPUT, LOCK, mask_c

CANONICAL = 'GENERATED_CANONICAL'
EXACT = 'EXACT_CANDIDATE_ROM'
DEFERRED = 'DEFERRED_AUDIT'
UNKNOWN = 'SUPPLY_NOT_FOUND_IN_CURRENT_SOURCES'


class Source:
    def __init__(self, value: dict):
        self.value = value
        self.symbols = {}
        self.units = {}
        for path, entry in value['sources'].items():
            need(entry['commit'] == value['source_commit'], 'consumer commit不一致')
            for row in entry.get('defines', []):
                name = row['symbol']
                need(name not in self.symbols, 'define重複: ' + name)
                self.symbols[name] = row['expression']
            for row in entry.get('units', []):
                need(digest(row['text'].encode()) == row['sha256'], 'consumer原文hash不一致')
                need(row['start_line'] > 0 and row['end_line'] >= row['start_line'], 'consumer行範囲不正')
                name = row['symbol']; need(name not in self.units, 'consumer定義重複')
                self.units[name] = (path, row)
        self.resolved = {}

    def number(self, name: str, seen: frozenset = frozenset()) -> int:
        need(name not in seen, 'define循環: ' + name)
        if name in self.resolved:
            return self.resolved[name]
        need(name in self.symbols, 'define欠落: ' + name)
        def value(node):
            if isinstance(node, ast.Constant) and type(node.value) is int:
                return node.value
            if isinstance(node, ast.Name):
                return self.number(node.id, seen | {name})
            if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub)):
                left, right = value(node.left), value(node.right)
                return left + right if isinstance(node.op, ast.Add) else left - right
            raise ValueError('define未対応式: ' + name)
        try:
            result = value(ast.parse(self.symbols[name], mode='eval').body)
        except SyntaxError as exc:
            raise ValueError('define構文不正: ' + name) from exc
        self.resolved[name] = result
        return result

    def code(self, name: str) -> str:
        need(name in self.units, 'consumer欠落: ' + name)
        return self.units[name][1]['text']

    def proof(self, name: str) -> dict:
        path, row = self.units[name]
        return {'repository': self.value['source_repository'], 'commit': self.value['source_commit'],
                'path': path, 'symbol': name, 'start_line': row['start_line'], 'end_line': row['end_line'],
                'unit_sha256': row['sha256'], 'file_sha256': self.value['sources'][path]['sha256'],
                'evidence': CANONICAL, 'candidate_native_acceptance': DEFERRED}


def load(inputs: Inputs) -> Source:
    data = inputs.json(OUTPUT)
    need(data['schema_version'] == 1, 'consumer schema不一致')
    lock = next(r for r in inputs.json(LOCK)['sources'] if r['name'] == 'cfru')
    need(data['source_commit'] == lock['configured_commit'] == lock['actual_commit'], 'consumer source-lock不一致')
    for path, expected in data['local_bindings'].items():
        raw = inputs.raw(path)
        need(len(raw) == expected['size'] and digest(raw) == expected['sha256'], 'consumer local source変更: ' + path)
    for path, units in data['local_units'].items():
        text = inputs.raw(path).decode()
        for unit in units:
            need(unit['text'].rstrip('\n') in text and digest(unit['text'].encode()) == unit['sha256'], 'local consumer原文不一致')
    return Source(data)


def key_for(symbol: str) -> str:
    need(symbol.startswith('MOVE_'), 'move symbolでない')
    return 'MOVE_KEY_' + symbol.removeprefix('MOVE_')


def z_effects(source: Source) -> list[dict]:
    code = source.code('SetZEffect')
    named = {name: source.number(name) for name in source.symbols if name.startswith('Z_EFFECT_')}
    need(sorted(named.values()) == list(range(29)), 'Z status定義範囲変更')
    descriptions = {
        'Z_EFFECT_NONE': '追加効果なし', 'Z_EFFECT_RESET_STATS': '使用者の下がった能力段階を標準値へ戻す',
        'Z_EFFECT_ALL_STATS_UP_1': '使用者の攻撃・防御・特攻・特防・素早さを各1段階上げる（命中・回避を除く）',
        'Z_EFFECT_BOOST_CRITS': '使用者へきあいだめ状態を付与', 'Z_EFFECT_FOLLOW_ME': '使用者をこのターンの攻撃誘導先に設定',
        'Z_EFFECT_CURSE': '使用者がゴーストタイプならHP全回復、それ以外は攻撃1段階上昇',
        'Z_EFFECT_RECOVER_HP': '使用者のHPを最大値まで回復', 'Z_EFFECT_RESTORE_REPLACEMENT_HP': '次に交代で入る味方を回復する予約を設定',
    }
    stats = {'ATK': '攻撃', 'DEF': '防御', 'SPD': '素早さ', 'SPATK': '特攻', 'SPDEF': '特防', 'ACC': '命中', 'EVSN': '回避'}
    result = []
    for name, eid in sorted(named.items(), key=lambda p: p[1]):
        if eid:
            need(name in code, 'Z effectに対応するconsumer分岐がない: ' + name)
        match = re.fullmatch(r'Z_EFFECT_(ATK|DEF|SPD|SPATK|SPDEF|ACC|EVSN)_UP_([123])', name)
        description = descriptions.get(name)
        if match:
            description = f'使用者の{stats[match[1]]}を{match[2]}段階上げる'
        need(description is not None, 'Z effect意味未定義')
        result.append({'id': eid, 'key': name, 'description_ja': description, 'consumer': source.proof('SetZEffect')})
    return result


def generic_z(model: dict, source: Source) -> dict:
    moves, items = model['moves'], model['items']
    by_key = {r['key']: r for r in moves}
    need(len(by_key) == len(moves), 'move key重複')
    code = source.code('GetTypeBasedZMove')
    for expression in ('moveType * 2', '(moveType - TYPE_FAIRY) * 2', '(moveType - 1) * 2', 'CalcMoveSplit(bank, move, bank)'):
        need(expression in code, '汎用Z算術式変更: ' + expression)
    eligibility = source.code('CanUseZMove')
    need('zMove != 0xFFFF' in eligibility and 'SPLIT(move) == SPLIT_STATUS' in eligibility
         and 'gBattleMoves[move].type == ItemId_GetHoldEffectParam(item)' in eligibility, '汎用Z分岐契約変更')
    effects = z_effects(source)
    generic_items = [r for r in items if r['hold_effect_id'] == source.number('ITEM_EFFECT_Z_CRYSTAL')
                     and r['id'] not in {z['item_id'] for z in model['z_moves']}]
    types = sorted({r['hold_effect_parameter'] for r in generic_items})
    old_ids = {}
    for symbol in source.symbols:
        if symbol.startswith('MOVE_') and key_for(symbol) in by_key:
            old_ids.setdefault(source.number(symbol), []).append(symbol)
    mappings = []
    for typ in types:
        for split in (0, 1):
            base = 'MOVE_TWINKLE_TACKLE_P' if typ >= source.number('TYPE_FAIRY') else 'MOVE_BREAKNECK_BLITZ_P'
            offset = typ - source.number('TYPE_FAIRY') if typ >= source.number('TYPE_FAIRY') else typ if typ < source.number('TYPE_FIRE') else typ - 1
            upstream_id = source.number(base) + 2 * offset + split
            matches = [by_key[key_for(s)] for s in old_ids.get(upstream_id, [])]
            unique = {r['id']: r for r in matches}
            need(len(unique) == 1, 'Z対象stable keyが一意でない')
            target = next(iter(unique.values()))
            # Header ID再割当後にもconsumerの算術が同じstable keyへ着地することを検査。
            need(target['id'] == by_key[key_for(base)]['id'] + 2 * offset + split, 'canonical Z連続配置契約違反')
            need(target['type_id'] == typ and target['category_id'] == split, 'Z変換先の候補type/split不一致')
            mappings.append({'type_id': typ, 'category_id': split, 'move_id': target['id'], 'move_key': target['key'],
                             'upstream_move_id_not_candidate_id': upstream_id,
                             'crystal_item_ids': [r['id'] for r in generic_items if r['hold_effect_parameter'] == typ],
                             'candidate_evidence': EXACT, 'rule_evidence': CANONICAL})
    lookup = {(r['type_id'], r['category_id']): r for r in mappings}
    dynamic_types = re.findall(r'move == (MOVE_[A-Z0-9_]+)', code)
    internal_keys = {key_for(s) for s in source.symbols if s.startswith(('MOVE_MAX_', 'MOVE_G_MAX_'))}
    internal_keys |= {key_for(s) for number, symbols in old_ids.items()
                      if source.number('FIRST_Z_MOVE') <= number <= source.number('LAST_Z_MOVE') for s in symbols}
    records = []
    for move in moves:
        mid = move['id']; typ = move['type_id']; split = move['category_id']
        row = {'move_id': mid, 'move_key': move['key'], 'power_field': move['z_power'],
               'shared_effect_field': move['z_effect'], 'candidate_evidence': EXACT,
               'consumer': 'CanUseZMove -> GetSpecialZMove -> GetTypeBasedZMove / SetZEffect',
               'candidate_native_acceptance': DEFERRED,
               'required_crystal_item_ids': [r['id'] for r in generic_items if r['hold_effect_parameter'] == typ]}
        if mid == 0:
            row.update(status='MOVE_NONE_NOT_A_BASE_MOVE', status_effect=None, targets=[])
        elif move['key'] in internal_keys:
            row.update(status='INTERNAL_Z_MAX_ROW_NOT_ORDINARY_BASE_MOVE', status_effect=None, targets=[],
                       shared_field_note_ja='Z/Max生成技の共用field。数値をZ変化技の追加効果と誤読しない。')
        elif split == 2:
            need(0 <= move['z_effect'] < len(effects), '変化技のZ effect範囲外')
            row.update(status='STATUS_MOVE_WITH_ADDITIONAL_EFFECT', status_effect=effects[move['z_effect']]['key'],
                       status_effect_description_ja=effects[move['z_effect']]['description_ja'],
                       return_sentinel='0xFFFF', base_move_retained=True, targets=[])
        else:
            row.update(status='DAMAGE_MOVE_SOURCE_RULE', status_effect=None,
                       targets=[lookup[(typ, s)] for s in (0, 1) if (typ, s) in lookup],
                       static_split=split, runtime_split='CalcMoveSplit(bank, move, bank)',
                       dynamic_type=move['key'] in {key_for(s) for s in dynamic_types},
                       dynamic_type_rule='GetMoveTypeSpecial' if move['key'] in {key_for(s) for s in dynamic_types} else None,
                       dynamic_targets_index='generic_z_type_mappings',
                       runtime_split_scope_ja='物理/特殊の候補を列挙。CalcMoveSplitの実行時条件を満たす側だけを使用。')
        if not row['required_crystal_item_ids']:
            row['crystal_supply_status'] = UNKNOWN
        row['target_mapping_audit'] = 'CANDIDATE_IDS_JOINED_TO_LOCKED_SOURCE_RULES'
        move['generic_z'] = row; records.append(row)
    return {'records': records, 'generic_z_type_mappings': mappings, 'status_effects': effects,
            'source_proofs': [source.proof(n) for n in ('GetTypeBasedZMove', 'GetSpecialZMove', 'CanUseZMove', 'SetZEffect', 'CalcMoveSplit', 'IsTypeZCrystal')],
            'policy_ja': '専用クリスタルの条件不一致では汎用へfallbackしない。道具type一致は元技tableのtype。動的typeの変換と混同しない。候補独自のVegaBattlePolicyCanZ gateも先行する。',
            'unresolved_ja': '全実行時type/split・modeのnative E2Eは追加実行していない。固定上流sourceと候補tableの結合を実行証拠へ昇格しない。'}


def hidden_supply(model: dict, source: Source) -> dict:
    code = mask_c(source.code('DetermineEggAbility'))
    match = re.search(r'Random\(\)\s*%\s*100\s*<\s*(\d+)', code)
    need(match is not None and 'mother = father;' in code and 'mother)->hiddenAbility' in code, '夢特性継承契約変更')
    percent = int(match[1]); need(0 <= percent <= 100, '継承率範囲外')
    common = {
        'breeding': {'status': 'UPSTREAM_CONDITIONAL_INHERITANCE', 'percent': percent,
                     'requires_hidden_parent': True, 'ditto_mother_uses_father': True,
                     'is_first_supply': False, 'consumer': source.proof('DetermineEggAbility'),
                     'current_project_daycare_caller': DEFERRED},
        'wild': {'status': 'UPSTREAM_FLAG_GATED_NOT_UNIVERSAL_RATE', 'flag_symbol': 'FLAG_HIDDEN_ABILITY',
                 'flag_number_in_upstream_not_project_assignment': source.number('FLAG_HIDDEN_ABILITY'),
                 'species_specific_flag_setter': UNKNOWN, 'consumer': source.proof('CreateWildMon')},
        'dexnav': {'status': 'UPSTREAM_SEARCH_LEVEL_AND_CAUGHT_GATED', 'requires_previously_caught': True,
                   'current_project_entry_and_config': DEFERRED, 'consumer': source.proof('DexNavGenerateHiddenAbility')},
        'raid': {'status': 'UPSTREAM_RAID_TABLE_POLICY_NOT_COLLECTION_POOL_POLICY',
                 'forced_hidden_or_random_all_percent': 50,
                 'consumer': source.proof('sp117_CreateRaidMon'),
                 'species_policy_consumer': source.proof('GetRaidSpeciesAbilityNum'),
                 'collection_pool_does_not_prove_this_caller': True},
        'script_gift': {'status': 'UPSTREAM_FLAG_GATED_AND_FLAG_CLEARED',
                        'consumer': source.proof('ScriptGiveMon'), 'species_specific_flag_setter': UNKNOWN},
        'patch': {'status': DEFERRED, 'reason_ja': '道具の存在と使用consumer、解禁・供給・個体slot変更を別々に照合する必要がある。'},
    }
    need('Random() & 1' in source.code('sp117_CreateRaidMon') and 'RAID_ABILITY_HIDDEN' in source.code('sp117_CreateRaidMon'), 'raid条件変更')
    need('FLAG_GET_CAUGHT' in source.code('DexNavGenerateHiddenAbility'), 'DexNav捕獲条件変更')
    for row in model['species']:
        hidden = row['hidden_ability']
        hidden.update(breeding={'reference': 'hidden_supply_rules.breeding', 'percent_if_hidden_parent': percent,
                               'candidate_native_acceptance': DEFERRED, 'is_first_supply': False},
                      wild_probability={'status': DEFERRED, 'reason': 'slotから共通の野生確率を推測しない'},
                      source_rule_reference='data/hidden_supply_rules.json',
                      acquisition_routes_reviewed=len(row['acquisition']),
                      acquisition_records_are_not_hidden_slot_proof=True)
    return common


def enrich(model: dict, inputs: Inputs) -> dict:
    source = load(inputs)
    z = generic_z(model, source); hidden = hidden_supply(model, source)
    model['consumer_audit'] = {'generic_z': z, 'hidden_supply_rules': hidden}
    model['source_bindings'].update({k: v for k, v in inputs.bindings.items() if k != STATE})
    model['followup_audit'] = {
        'schema_version': 1, 'issue18_complete': False, 'new_native_runs': 0,
        'summary': {'generic_z_records': len(z['records']), 'type_split_mappings': len(z['generic_z_type_mappings']),
                    'z_status_effects': len(z['status_effects']), 'hidden_slot_records': len(model['hidden_abilities']),
                    'generic_z_states': dict(sorted(Counter(r['status'] for r in z['records']).items()))},
        'remaining_work_ja': [
            '野生初期技と固定配布の実movesetを全経路抽出し、推測と区別する。',
            '汎用Zの静的対応は追加済み。実行時physicality tableと候補consumer bindingを追加照合する（native再実行は不要）。',
            '夢特性は上流の継承/flag/DexNav/raid条件を分離済み。現候補の種族別初回供給caller・patch・育て屋を照合する。',
            '既存effect流用と新規handlerをsource履歴で区分する。native未受入を無断で再実行しない。'],
    }
    return model


def append_pages(files: dict[str, bytes], model: dict) -> None:
    from pr16_candidate_wiki_render import jsonblock, table, Link
    audit = model['consumer_audit']; z = audit['generic_z']
    intro = '# 固定consumerと候補tableの対応\n\n[Wiki入口](README.md) / [Z一覧](Z_MOVE_INDEX.md) / [隠れ特性一覧](HIDDEN_ABILITY_INDEX.md)\n\n'
    intro += '候補 SHA-256 `' + model['candidate']['sha256'] + '`。静的な対応付けであり、新規native受入ではありません。\n\n'
    body = intro + '## 汎用Zのtype・物理/特殊対応\n\n' + z['policy_ja'] + '\n\n'
    body += table(['type ID', '分類ID', '変換先', 'stable key', '候補クリスタルID'],
                  [(r['type_id'], r['category_id'], Link(f'[{r["move_id"]}](moves/{r["move_id"]}.md)'), r['move_key'], r['crystal_item_ids']) for r in z['generic_z_type_mappings']])
    body += '\n## Z変化技の追加効果\n\n0xFFFFは元技を維持する返り値であり、技ID65535へのリンクではありません。Max/G-Max共用欄の数値をこの表へ混ぜません。\n\n'
    body += table(['effect ID', 'key', '効果'], [(r['id'], r['key'], r['description_ja']) for r in z['status_effects']])
    body += '\n## 夢特性の条件付きsource規則\n\n初回入手経路と、既に隠れ特性の親を持つ場合の継承を分離します。上流のraid生成処理と本プロジェクトのcollection poolは同じ入口とは限りません。\n\n' + jsonblock(audit['hidden_supply_rules'])
    body += '\n## 根拠と残件\n\n' + jsonblock(z['source_proofs']) + '\n' + jsonblock(model['followup_audit'])
    files['CONSUMER_AUDIT.md'] = body.encode()
    files['data/generic_z.jsonl'] = b''.join((__import__('json').dumps(r, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n').encode() for r in z['records'])
    files['data/generic_z_type_mappings.json'] = stable(z['generic_z_type_mappings'])
    files['data/z_status_effects.json'] = stable(z['status_effects'])
    files['data/hidden_supply_rules.json'] = stable(audit['hidden_supply_rules'])
    files['data/followup_audit.json'] = stable(model['followup_audit'])
    replacements = {
        'Z_MOVE_INDEX.md': [
            ('各技の実候補z_powerとz_effectを機械可読データに保持します。汎用変換先consumerの全組合せ監査はDEFERRED_AUDITであり、専用Zの対応表受入と混同しません。',
             '各技の実候補fieldと固定consumer規則を結合しました。36のtype/split対応、動的type、専用クリスタルの除外、変化技の0xFFFF返値を個別ページとconsumer監査に記録します。全組合せnative受入ではありません。'),
            ('Z変化effect', 'Z/Max共用effect byte（適用区分は個別頁）')],
        'RUNTIME_LIMITATIONS.md': [
            ('野生初期技と固定配布の全実moveset、隠れ特性の種族別初回供給率・継承・patch、汎用Z変換先の全consumer、専用Z全組合せのnative E2E、',
             '野生初期技と固定配布の全実moveset、隠れ特性の種族別初回供給caller・patch、専用Z全組合せのnative E2E、')],
    }
    for name, pairs in replacements.items():
        text = files[name].decode()
        for before, after in pairs:
            need(text.count(before) == 1, 'consumer監査の表示anchor変更: ' + name)
            text = text.replace(before, after, 1)
        files[name] = text.encode()
    for name in ('README.md', 'Z_MOVE_INDEX.md', 'HIDDEN_ABILITY_INDEX.md', 'RUNTIME_LIMITATIONS.md', 'CODEX_INDEX.md'):
        files[name] += '\n[今回追加の固定consumer監査・正確な残件](CONSUMER_AUDIT.md)\n'.encode()
