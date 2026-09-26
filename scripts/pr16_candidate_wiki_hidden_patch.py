#!/usr/bin/env python3
"""固定party consumer・候補slot・現供給sourceを結合する。実入手/使用受入は増やさない。"""
from __future__ import annotations
from collections import Counter
import copy
import re
import sys
sys.dont_write_bytecode = True
from pr16_candidate_wiki_inputs import Inputs, STATE, digest, need, stable
from pr16_candidate_wiki_consumers import Source
from pr16_wiki_source_snapshot import function_unit, mask_c

SNAPSHOT = 'content/modernization/pr16_candidate_wiki_hidden_patch_sources.json'
SELF = 'scripts/pr16_candidate_wiki_hidden_patch.py'
COLLECTION = 'overlays/collection_supply_v1/collection_supply_v1.c'
QOL = 'tools/engine/cfru_qol_runtime.py'
PROFILE = 'config/cfru_vega_minimal.h'
DEFERRED = 'DEFERRED_AUDIT'


def read_source(inputs: Inputs) -> Source:
    data = inputs.json(SNAPSHOT)
    need(data['schema_version'] == 1, 'patch source schema不一致')
    lock = next(r for r in inputs.json('state/source-lock.json')['sources'] if r['name'] == 'cfru')
    need(data['source_commit'] == lock['configured_commit'] == lock['actual_commit'], 'patch source-lock不一致')
    # 同じ固定party_menuを使う実生成器のsource hash契約と照合する。
    code = inputs.raw(QOL).decode()
    need(data['sources']['src/party_menu.c']['sha256'] in code and data['source_commit'] in code,
         'patch原文と現QOL生成器の固定source契約不一致')
    profile = mask_c(inputs.raw(PROFILE).decode())
    directives = re.findall(r'^\s*#\s*(define|undef)\s+UNBOUND\b', profile, re.M)
    need(directives and directives[-1] == 'undef', 'UNBOUND追加条件を無効と判定できない')
    return Source(data)


def verify_contract(source: Source) -> None:
    required = {
        'FieldUseFunc_AbilityCapsule': ['gItemUseCB = ItemUseCB_AbilityCapsule;', 'SetUpItemUseCallback(taskId);'],
        'ItemUseCB_AbilityCapsule': ['GetAbilityCapsuleNewAbility(mon)', 'changeTo != ABILITY_NONE',
                                   'gTasks[taskId].func = Task_OfferAbilityChange;', 'gText_WontHaveEffect'],
        'GetAbilityCapsuleNewAbility': ['ItemId_GetHoldEffectParam(item)', 'GetMonAbility(mon)', 'GetHiddenAbility(species)',
                                      'abilityType != 0', 'ability != hiddenAbility', 'hiddenAbility != ABILITY_NONE',
                                      'changeTo = hiddenAbility;', '#ifdef UNBOUND'],
        'Task_OfferAbilityChange': ['PartyMenuDisplayYesNoMenu();', 'Task_HandleAbilityChangeYesNoInput;'],
        'Task_HandleAbilityChangeYesNoInput': ['case 0:', 'Task_ChangeAbility;', 'case MENU_B_PRESSED:',
                                              'case 1:', 'Task_ClosePartyMenuAfterText;'],
        'Task_ChangeAbility': ['abilityType != 0', 'mon->hiddenAbility = TRUE;', 'mon->hiddenAbility = FALSE;',
                               'RemoveBagItem(item, 1);'],
    }
    for name, snippets in required.items():
        code = mask_c(source.code(name))
        need(all(s in code for s in snippets), 'patch consumer契約変更: ' + name)
    for name in ('ItemUseCB_AbilityCapsule', 'Task_HandleAbilityChangeYesNoInput'):
        code = mask_c(source.code(name))
        need('RemoveBagItem' not in code and 'SetMonData' not in code and 'hiddenAbility =' not in code,
             'patch取消/効果なし分岐に書込を検出')


def slot_rule(normal: list[int], hidden: int) -> dict:
    need(len(normal) == 2 and all(type(x) is int and 0 <= x < 65536 for x in [*normal, hidden]), 'ability slot型/範囲不正')
    known = sorted(set(normal) - {0})
    eligible = [a for a in known if a != hidden]
    same = [a for a in known if a == hidden]
    if hidden == 0:
        status = 'NO_HIDDEN_ABILITY_ASSIGNED'; eligible = []
    elif not known:
        status = 'NORMAL_ABILITY_RESOLUTION_REQUIRED'
    elif not eligible:
        status = 'NORMAL_ABILITY_ALREADY_EQUALS_HIDDEN_ID'
    elif same:
        status = 'DEPENDS_ON_CURRENT_NORMAL_ABILITY'
    else:
        status = 'DISTINCT_NORMAL_ABILITY_CAN_TARGET_HIDDEN'
    return {'status': status, 'normal_ability_ids': normal, 'hidden_ability_id': hidden,
            'eligible_nonzero_normal_ability_ids': eligible, 'no_effect_same_ability_ids': same,
            'zero_normal_slot_requires_engine_resolution': 0 in normal,
            'already_hidden_ability_has_no_effect': True,
            'condition_ja': '現在のGetMonAbilityが隠れIDと異なり、隠れIDが0でないときだけ候補。hidden flagの有無だけでは判定しない。',
            'candidate_native_acceptance': DEFERRED, 'first_supply_proven': False}


def local_proof(inputs: Inputs, path: str, symbol: str) -> dict:
    raw = inputs.raw(path); unit = function_unit(raw.decode(), symbol)
    return {'path': path, 'symbol': symbol, 'start_line': unit['start_line'], 'end_line': unit['end_line'],
            'file_sha256': digest(raw), 'unit_sha256': unit['sha256'], 'evidence': 'GENERATED_CANONICAL'}


def supply_contract(model: dict, inputs: Inputs) -> dict:
    items = [r for r in model['items'] if r['key'] == 'ITEM_KEY_ABILITY_PATCH']
    need(len(items) == 1, 'Ability Patch stable key欠落/重複')
    item = items[0]
    need(item['field_use_callback_key'] == 'FieldUseFunc_AbilityCapsule' and item['hold_effect_parameter'] == 1
         and item['consume_policy'] == 'ON_EFFECT', '候補Patch metadata契約変更')
    canonical = inputs.json('content/collection_supply_v1/canonical_model.json')
    rows = [r for r in canonical['items'] if r['item_key'] == item['key']]
    need(len(rows) == 1 and rows[0]['item_id'] == item['id'], 'Patch供給stable ID不一致')
    supply = rows[0]
    need(supply['source'] == 'BP_SHOP' and supply['unlock'] == 'HIDDEN_ABILITY_DEXNAV_UNLOCKED', 'Patch供給owner変更')
    need(supply['price'] > 0 and supply['quantity'] == 1, 'Patch供給数量/価格不正')
    text = mask_c(inputs.raw(COLLECTION).decode())
    unlock = mask_c(function_unit(text, 'unlock_satisfied')['text'])
    # test_modeは通常解禁の証明から除外。hidden unlock名をDexNav捕獲条件と読み違えない。
    need('G_STATE->test_mode' in unlock and 'case COLLECTION_UNLOCK_HIDDEN_ABILITY:' in unlock,
         'collection unlock分岐変更')
    match = re.search(r'case COLLECTION_UNLOCK_HIDDEN_ABILITY:\s*return\s*\(u8\)\(gVegaModernSaveData->vega_hall_of_fame\s*\|\| FN_FLAG_GET\(\(u16\)\(COLLECTION_FLAG_BADGE_1 \+ 7u\)\)\);', unlock)
    need(match is not None, '通常Patch解禁条件変更')
    flag = re.search(r'\bCOLLECTION_FLAG_BADGE_1\s*=\s*(0x[0-9a-fA-F]+)u', text)
    need(flag is not None, 'badge flag基点がない')
    acquire = mask_c(function_unit(text, 'acquire_item')['text'])
    for token in ('!unlock_satisfied(row->unlock)', 'balance < row->price', 'bag_add(row->item_id, row->quantity)',
                  'currency_set(currency, balance - row->price)', 'COLLECTION_RESULT_BAG_FULL', 'COLLECTION_RESULT_PERSIST_FAILED'):
        need(token in acquire, 'Patch取得transaction契約変更: ' + token)
    currency = function_unit(text, 'source_currency')['text']
    need('COLLECTION_SOURCE_BP' in currency and 'COLLECTION_CURRENCY_BP' in currency, 'BP通貨owner変更')
    return {'item_id': item['id'], 'item_key': item['key'], 'rom_price_field': item['price'],
            'bp_shop_cost': supply['price'], 'quantity': supply['quantity'],
            'unlock_name': supply['unlock'], 'normal_unlock': 'VEGA_HALL_OF_FAME_OR_EIGHTH_BADGE_FLAG',
            'eighth_badge_flag': hex(int(flag[1], 16) + 7), 'test_mode_excluded': True,
            'secondary_source_declared_not_caller_proof': supply['secondary_source'],
            'field_callback_declaration': item['field_use_callback_key'],
            'exact_hold_effect_parameter': item['hold_effect_parameter'],
            'candidate_field_callback_binding': DEFERRED, 'shop_to_bag_to_patch_native': DEFERRED,
            'input_runtime_binding_label_not_current_acceptance': item['runtime_binding'],
            'source_proofs': [local_proof(inputs, COLLECTION, n) for n in ('unlock_satisfied', 'source_currency', 'acquire_item', 'eligible_at')]}


def audit(model: dict, source: Source, supply: dict) -> dict:
    verify_contract(source)
    species = model['species']; hidden_rows = model['hidden_abilities']
    by_id = {r['species_id']: r for r in hidden_rows}
    need(len(by_id) == len(hidden_rows) == len(species), 'hidden mirror ID重複/件数不一致')
    need(len({r['id'] for r in species}) == len(species), 'species ID重複')
    records = []
    for row in species:
        sid = row['id']; hidden = row['hidden_ability']; slots = row['ability_ids']
        need(sid in by_id and len(slots) == 3 and hidden['species_id'] == sid
             and hidden['species_key'] == row['key'] and hidden['ability_id'] == slots[2], 'hidden slot結合不一致')
        mirror = by_id[sid]
        need(mirror['ability_id'] == hidden['ability_id'] and mirror['species_key'] == row['key'], 'hidden mirror不一致')
        rule = slot_rule(slots[:2], slots[2])
        patch = {'species_id': sid, 'species_key': row['key'], 'patch_item_id': supply['item_id'],
                 'slot_evidence': row['evidence'], 'rule_evidence': 'GENERATED_CANONICAL', **rule}
        hidden['patch'] = copy.deepcopy(patch); mirror['patch'] = copy.deepcopy(patch)
        records.append(patch)
    common = {'status': 'SOURCE_CONDITION_JOINED_TO_CANDIDATE_SLOTS', 'item_supply': supply,
              'current_ability_compared_not_only_hidden_flag': True,
              'confirm_sets_hidden_flag': True, 'confirm_consumes_one': True,
              'cancel_and_no_effect_do_not_consume': True, 'unbound_extra_conditions_disabled_by_project_profile': True,
              'compiled_patch_and_species_accessors': DEFERRED, 'new_native_runs': 0,
              'source_proofs': [source.proof(n) for n in source.units]}
    model['consumer_audit']['hidden_supply_rules']['patch'] = common
    return {'schema_version': 1, 'candidate': model['candidate'], 'records': records, 'rules': common,
            'summary': {'hidden_patch_records': len(records), 'hidden_patch_states': dict(sorted(Counter(r['status'] for r in records).items()))},
            'new_native_runs': 0, 'rom_changes': 0, 'all_first_supply_routes_complete': False,
            'scope_ja': '固定consumerと現candidate slot・local供給sourceの対応。現在の個体の有効特性はGetMonAbilityで決まる。供給/使用callerのcompiled対応・実到達/保存/Continueを受入したものではない。'}


def enrich(model: dict, inputs: Inputs) -> dict:
    inputs.raw(SELF)
    source = read_source(inputs); value = audit(model, source, supply_contract(model, inputs))
    model['hidden_patch_audit'] = value
    model['followup_audit']['summary'].update(value['summary'])
    todo = model['followup_audit']['remaining_work_ja']
    indices = [i for i, s in enumerate(todo) if s.startswith('夢特性は上流の継承')]
    need(len(indices) == 1, '夢特性残件anchor不一致')
    todo[indices[0]] = '夢特性パッチは全1671slotの適用条件とBP供給source/解禁を分類済み。残りは現候補のcompiled field callback・種族accessor・通常初回供給caller・育て屋の対応。source分類を実入手/使用受入にしない。'
    model['source_bindings'].update({k: v for k, v in inputs.bindings.items() if k != STATE})
    return model


def append_pages(files: dict[str, bytes], model: dict) -> None:
    from pr16_candidate_wiki_render import jsonblock, table, Link
    value = model['hidden_patch_audit']; rules = value['rules']; supply = rules['item_supply']
    body = '# 夢特性パッチの適用条件と供給source\n\n[Wiki入口](README.md) / [夢特性一覧](HIDDEN_ABILITY_INDEX.md)\n\n'
    body += '候補 SHA-256 `' + model['candidate']['sha256'] + '`。' + value['scope_ja'] + '\n\n'
    body += '## 条件\n\n同じ特性IDなら通常slotでも効果なしです。隠れflagを持つかだけでは判定しません。取消・効果なしでは消費せず、承諾後だけ隠れflagを立てて1個消費します。\n\n'
    body += '## 供給\n\n供給定義は **' + str(supply['bp_shop_cost']) + ' BP**。道具ROMの価格field **' + str(supply['rom_price_field']) + '** とは別です。通常sourceの解禁はベガ殿堂入りledgerまたは8個目badge flag。`HIDDEN_ABILITY_DEXNAV_UNLOCKED`という名前だけからDexNavの捕獲条件を追加しません。test_modeを通常供給証拠に使いません。\n\n'
    body += jsonblock(supply) + '\n## 全Speciesのslot判定\n\n' + jsonblock(value['summary'])
    body += table(['Species', '通常1/2', '隠れID', '適用条件（source分類）'],
                  [(Link(f'[{r["species_id"]}](pokemon/{r["species_id"]}.md)'), r['normal_ability_ids'], r['hidden_ability_id'], r['status']) for r in value['records']])
    body += '\n## 原文と未受入境界\n\n' + jsonblock(rules)
    files['HIDDEN_PATCH_AUDIT.md'] = body.encode()
    files['data/hidden_patch_audit.json'] = stable(value)
    for name in ('README.md', 'HIDDEN_ABILITY_INDEX.md', 'RUNTIME_LIMITATIONS.md', 'CODEX_INDEX.md'):
        files[name] += '\n[夢特性パッチ：種族別適用条件・供給source・未受入範囲](HIDDEN_PATCH_AUDIT.md)\n'.encode()
    files[f'items/{supply["item_id"]}.md'] += ('\n## パッチ適用とBP供給\n\n[種族別適用監査](../HIDDEN_PATCH_AUDIT.md)\n\n'+jsonblock(supply)).encode()
