#!/usr/bin/env python3
"""現候補の追加野生95行・配布/raid sourceを初期技規則に結合。native受入は増やさない。"""
from __future__ import annotations
from collections import Counter, defaultdict
import re
import struct
import sys
sys.dont_write_bytecode = True
from pr16_candidate_wiki_inputs import Inputs, Rom, STATE, digest, need, stable
from pr16_candidate_wiki_consumers import Source
from pr16_wiki_source_snapshot import mask_c, function_unit

SNAPSHOT = 'content/modernization/pr16_candidate_wiki_creation_sources.json'
SELF = 'scripts/pr16_candidate_wiki_creation.py'
WILD = 'overlays/wild_overlay/wild_overlay.c'
COLLECTION = 'overlays/collection_supply_v1/collection_supply_v1.c'
FLOETTE = 'overlays/modernization_floette_gift/modernization_floette_gift.c'
POLICY = 'config/stage61_wild_overlay_rate_policy.json'
DEFERRED = 'DEFERRED_AUDIT'


def integer(value, low: int, high: int, label: str) -> int:
    need(type(value) is int and low <= value <= high, label + '型/範囲不正')
    return value


def verify_source(value: dict) -> Source:
    source = Source(value)
    a = mask_c(source.code('GiveBoxMonInitialMoveset'))
    b = mask_c(source.code('GiveMoveToBoxMon'))
    for token in ('lvlUpMove.level > level', 'moveStack[k++] = move;', 'index = k - MAX_MON_MOVES;',
                  'index = 0;', 'GiveMoveToBoxMon(boxMon, moveStack[index++]) != 0xFFFF'):
        need(token in a, '初期技source規則変更: ' + token)
    for token in ('if (!existingMove)', 'if (existingMove == move)', 'return -2;', 'return 0xFFFF;',
                  'move == MOVE_SECRETSWORD', 'SPECIES_KELDEO_RESOLUTE'):
        need(token in b, '技付与source規則変更: ' + token)
    need(value['initial_move_capacity'] == 40, '初期技stack容量変更')
    return source


def read_levels(rom: Rom, root: int, sid: int, species_count: int, move_count: int) -> dict:
    integer(sid, 0, species_count - 1, 'species')
    address = rom.u32(root + 4 * sid); rows = []
    for index in range(256):
        move, level = struct.unpack('<HB', rom.read(address + 3 * index, 3))
        if (move, level) == (0, 255):
            return {'species_id': sid, 'address': hex(address), 'rows': rows,
                    'sha256': digest(rom.read(address, 3 * (index + 1))), 'evidence': 'EXACT_CANDIDATE_ROM'}
        integer(move, 0, move_count - 1, 'level move'); integer(level, 0, 100, 'level')
        # MOVE_NONE paddingも消さない。末尾4行の選択位置に影響する。
        rows.append({'move_id': move, 'level': level, 'order': index})
    raise ValueError('初期技table終端なし')


def predict(rows: list[dict], level: int) -> dict:
    integer(level, 1, 100, '生成level')
    eligible = []
    for row in rows:
        integer(row['level'], 0, 100, '行level'); integer(row['move_id'], 0, 65534, 'move')
        if row['level'] > level:
            break  # 全行filter/level順sortではない。
        eligible.append(row['move_id'])
    if len(eligible) > 40:
        return {'status': 'SOURCE_STACK_CAPACITY_EXCEEDED', 'eligible_prefix_rows': len(eligible),
                'candidate_native_acceptance': DEFERRED}
    selected = eligible[-4:]; slots = [0, 0, 0, 0]
    for move in selected:
        for i, existing in enumerate(slots):
            if existing == 0:
                slots[i] = move
                break
            if existing == move:
                break  # -2 != 0xFFFFなので次の行の付与は続く。
    return {'status': 'SOURCE_RULE_APPLIED_TO_CANDIDATE_ROWS', 'selected_raw_move_ids': selected,
            'move_ids': slots, 'eligible_prefix_rows': len(eligible), 'candidate_native_acceptance': DEFERRED}


def overlay_rows(data: bytes, species_count: int) -> list[dict]:
    need(len(data) > 0 and len(data) % 104 == 0, 'wild table stride不一致')
    rows = []
    for index in range(len(data) // 104):
        unit = data[index*104:(index+1)*104]
        group, number, area, layer, rate, count = unit[:6]
        integer(area, 0, 4, 'wild area'); integer(layer, 0, 5, 'wild layer'); integer(count, 1, 12, 'wild候補数')
        candidates = []
        for slot in range(count):
            sid = struct.unpack_from('<H', unit, 8 + slot * 2)[0]
            integer(sid, 1, species_count - 1, 'wild species')
            pre = [unit[32+slot], unit[44+slot]]; post = [unit[56+slot], unit[68+slot]]
            for low, high in (pre, post):
                integer(low, 1, 100, 'wild最小level'); integer(high, low, 100, 'wild最大level')
            badge = unit[80+slot]; rod = unit[92+slot]
            integer(badge & 127, 0, 8, 'wild badge'); integer(rod, 0, 3, 'wild rod')
            candidates.append({'slot': slot, 'species_id': sid, 'pre_hall_of_fame_levels': pre,
                'post_hall_of_fame_levels': post, 'minimum_badges': badge & 127,
                'night_radar_badge_override': bool(badge & 128), 'minimum_rod': rod})
        rows.append({'entry_index': index, 'map_group': group, 'map_number': number, 'area': area, 'layer': layer,
            'roll_threshold_u8': rate, 'roll_denominator': 256, 'forced_hidden_scan_bypasses_roll': layer == 5,
            'row_sha256': digest(unit), 'evidence': 'EXACT_CANDIDATE_ROM', 'candidates': candidates})
    return rows


def c_unit(text: str, name: str) -> dict:
    """行頭の型付き定義だけを選ぶ。if (!f() || g()) の呼出を定義と誤認しない。"""
    masked = mask_c(text)
    pattern = r'^(?:static\s+)?(?:[A-Za-z_]\w*[\t *]+)+'+re.escape(name)+r'\s*\([^;{}]*\)\s*\{'
    matches = list(re.finditer(pattern, masked, re.M))
    need(len(matches) == 1, 'local定義欠落/重複: '+name)
    match = matches[0]; end = match.end(); depth = 1
    while depth and end < len(masked):
        depth += (masked[end] == '{') - (masked[end] == '}'); end += 1
    need(depth == 0, 'local定義brace不正')
    unit = text[match.start():end]+'\n'
    return {'text':unit,'sha256':digest(unit.encode()),'start_line':text[:match.start()].count('\n')+1,
            'end_line':text[:end].count('\n')+1}


def local_proofs(inputs: Inputs) -> list[dict]:
    spec = {WILD: ('select_from_entry', 'select_encounter', 'VegaWildOverlay_TryGenerateWildMon', 'VegaWildOverlay_GenerateFishingEncounter'),
            COLLECTION: ('deliver_gift', 'start_prepared_raid'), FLOETTE: ('create_gift',)}
    proofs = []
    for path, names in spec.items():
        raw = inputs.raw(path)
        for name in names:
            unit = c_unit(raw.decode(), name)
            proofs.append({'path': path, 'symbol': name, 'file_sha256': digest(raw), 'unit_sha256': unit['sha256'],
                           'start_line': unit['start_line'], 'end_line': unit['end_line'], 'evidence': 'GENERATED_CANONICAL'})
    wild = mask_c(inputs.raw(WILD).decode())
    need('OVERLAY_ENTRY_SIZE = 104' in wild and 'OVERLAY_SPECIES_OFFSET = 8' in wild
         and '(uint8_t)random >= entry[4]' in wild and 'FLAG_HALL_OF_FAME = 0x082C' in wild,
         '野生ABI/roll/gate規則変更')
    for offset, expected in (('PRE_MIN',32),('PRE_MAX',44),('POST_MIN',56),('POST_MAX',68),('MIN_BADGES',80),('MIN_ROD',92)):
        need(f'OVERLAY_{offset}_OFFSET = {expected}' in wild, 'wild offset変更')
    gift = mask_c(c_unit(inputs.raw(COLLECTION).decode(), 'deliver_gift')['text'])
    need('gift->kind == COLLECTION_GIFT_RESEARCH_EGG ? 1u : 50u' in gift, '配布level規則変更')
    for name, code in (('collection gift', gift), ('Floette', mask_c(c_unit(inputs.raw(FLOETTE).decode(), 'create_gift')['text']))):
        need('FN_CREATE_MON(' in code and not re.search(r'\b(?:SetMonMoveSlot|FN_SET_MON_MOVE_SLOT|GiveMoveToMon)\s*\(', code), name+'技上書き契約変更')
    return proofs


def declared_routes(model: dict, inputs: Inputs) -> list[dict]:
    species = {r['id']: r['key'] for r in model['species']}
    c = inputs.json('content/collection_supply_v1/canonical_model.json'); result = []
    for index, gift in enumerate(c['gifts']):
        integer(gift['form_index'], 0, len(c['forms']) - 1, 'gift form index')
        form = c['forms'][gift['form_index']]
        need(gift['kind'] in ('RESEARCH_EGG', 'FIXED') and form['distributable'], 'gift kind変更')
        level = 1 if gift['kind'] == 'RESEARCH_EGG' else 50
        result.append({'route_key': 'COLLECTION_GIFT_'+str(index), 'kind': 'FIXED_GIFT' if gift['kind'] == 'FIXED' else gift['kind'], 'source_gift_kind': gift['kind'], 'species_id': form['target_species'],
            'species_key': form['species_key'], 'level_min': level, 'level_max': level, 'unlock': gift['unlock'],
            'claim_bit': gift['claim_bit'], 'explicit_moves_override': False, 'breeding_inheritance_claimed': False})
    gift = inputs.json('config/modernization_floette_gift.json')['gift']
    header = mask_c(inputs.raw('overlays/modernization_floette_gift/modernization_floette_gift.h').decode())
    for symbol, value in (('SPECIES', gift['species_id']), ('LEVEL', gift['level'])):
        need(re.search(r'#define MODERNIZATION_FLOETTE_GIFT_'+symbol+r'\s+'+str(value)+r'u\b', header) is not None, 'Floette定数不一致')
    result.append({'route_key': 'FLOETTE_ETERNAL_GIFT', 'kind': 'FIXED_GIFT', 'species_id': gift['species_id'],
        'species_key': gift['species_key'], 'level_min': gift['level'], 'level_max': gift['level'],
        'unlock_item_id': gift['unlock_item_id'], 'claim_flag': gift['claim_flag'], 'explicit_moves_override': False})
    for pool in c['pool_entries']:
        result.append({'route_key': pool['entry_key'], 'kind': 'COLLECTION_RAID', 'species_id': pool['species'],
            'species_key': pool['species_key'], 'level_min': pool['level_min'], 'level_max': pool['level_max'],
            'pool_key': pool['pool_key'], 'unlock': pool['unlock'], 'gmax_chance': pool['gmax_chance'],
            'source_raid_key': pool['source_raid_key'], 'upstream_sp117_route_assumed': False})
    need(len({r['route_key'] for r in result}) == len(result), 'creation route key重複')
    for row in result:
        need(species.get(row['species_id']) == row['species_key'], 'creation stable species不一致')
        integer(row['level_min'], 1, 100, '最小level'); integer(row['level_max'], row['level_min'], 100, '最大level')
        row.update(evidence='GENERATED_CANONICAL', compiled_caller_binding=DEFERRED, native_acceptance=DEFERRED)
    return result


def enrich(model: dict, inputs: Inputs, raw: bytes) -> dict:
    inputs.raw(SELF); snapshot = inputs.json(SNAPSHOT); source = verify_source(snapshot)
    lock = next(r for r in inputs.json('state/source-lock.json')['sources'] if r['name'] == 'cfru')
    need(source.value['source_commit'] == lock['actual_commit'] == lock['configured_commit'], 'creation source-lock不一致')
    need(snapshot['entry_inventory']['candidate'] == model['candidate'], 'creation入口候補不一致')
    proofs = local_proofs(inputs); routes = declared_routes(model, inputs); rom = Rom(raw)
    policy = inputs.json(POLICY)['table']; address = int(policy['address'],16)
    need(policy['entry_size'] == 104 and policy['size'] == policy['entry_count'] * 104, 'wild table契約不一致')
    table = rom.read(address, policy['size']); wild = overlay_rows(table, len(model['species']))
    need(len(wild) == policy['entry_count'], 'wild table件数不一致')
    species = {r['id']: r for r in model['species']}; required = defaultdict(set); refs = defaultdict(list)
    for row in routes:
        required[row['species_id']].update(range(row['level_min'], row['level_max']+1))
        refs[row['species_id']].append(row['route_key'])
    wild_refs = defaultdict(list)
    for entry in wild:
        for row in entry['candidates']:
            sid = row['species_id']; row['species_key'] = species[sid]['key']
            wild_refs[sid].append({'entry_index': entry['entry_index'], **row})
            for name in ('pre_hall_of_fame_levels', 'post_hall_of_fame_levels'):
                low, high = row[name]; required[sid].update(range(low, high+1))
    root = int(model['roots']['species_level_up_pointers'], 16)
    need(rom.u32(0x0804346C) == root, '初期技level root不一致')
    profiles = []; row_proofs = []
    secret = next(r['id'] for r in model['moves'] if r['key'] == 'MOVE_KEY_SECRETSWORD')
    keldeo = next(r['id'] for r in species.values() if r['key'] == 'SPECIES_KEY_KELDEO')
    resolute = next(r['id'] for r in species.values() if r['key'] == 'SPECIES_KEY_KELDEO_RESOLUTE')
    for sid, levels in sorted(required.items()):
        info = read_levels(rom, root, sid, len(species), len(model['moves']))
        row_proofs.append({k:v for k,v in info.items() if k!='rows'})
        for level in sorted(levels):
            prediction = predict(info['rows'], level)
            profiles.append({'profile_key': f'{sid}:{level}', 'species_id': sid, 'species_key': species[sid]['key'],
                'level': level, **prediction, 'level_table_sha256': info['sha256'],
                'source_rule_species_after_move_giving': resolute if sid == keldeo and secret in prediction.get('move_ids', []) else sid,
                'after_create_form_adjustments': DEFERRED, 'randomizer_and_compiled_macro_state': DEFERRED})
    for row in species.values():
        sid = row['id']
        row['fixed_gift_moves'] = {'status': 'SCOPED_DECLARED_ROUTES_WITH_SOURCE_RULE_PROFILES', 'route_keys': refs[sid],
            'scope': 'COLLECTION_18_AND_FLOETTE_1_PLUS_COLLECTION_RAID_292', 'all_legacy_gift_scripts_complete': False,
            'profiles': f'../data/creation_profiles.jsonl', 'candidate_native_acceptance': DEFERRED}
        row['wild_initial_moves'] = {'status': 'SCOPED_OVERLAY_TABLE_WITH_SOURCE_RULE_PROFILES', 'overlay_slots': wild_refs[sid],
            'all_native_wild_headers_complete': False, 'post_creation_form_consumers': DEFERRED,
            'profiles': '../data/creation_profiles.jsonl', 'candidate_native_acceptance': DEFERRED}
    value = {'schema_version':1, 'candidate':model['candidate'], 'routes':routes, 'wild_overlay':wild, 'profiles':profiles,
        'level_table_proofs':row_proofs, 'source_proofs': [source.proof(n) for n in source.units] + proofs,
        'entry_inventory':snapshot['entry_inventory'], 'overlay_table':{'address':hex(address),'size':len(table),'sha256':digest(table),'evidence':'EXACT_CANDIDATE_ROM'},
        'summary':{'creation_declared_routes':len(routes),'creation_route_kinds':dict(sorted(Counter(r['kind'] for r in routes).items())),
            'wild_overlay_entries':len(wild),'wild_overlay_slots':sum(len(r['candidates']) for r in wild),
            'creation_profile_species':len(required),'creation_profiles':len(profiles),
            'creation_profile_states':dict(sorted(Counter(r['status'] for r in profiles).items()))},
        'new_native_runs':0,'rom_changes':0,'all_creation_callers_complete':False,
        'limitations_ja':['初期技は現候補tableに固定source規則を適用した条件付き計算。現compiled初期化caller/マクロ/乱数化の実適用は未受入。',
            '末尾4 raw行を選んでから付与する。重複/MOVE_NONEを先に除去しない。最初のlevel超過で停止。容量40超過は計算結果を捏造しない。',
            '上流終端条件は同一levelの0と255のAND。修正せず、level1..100で255が超過する範囲だけを計算する。',
            'Secret Sword付与時のKeldeo変化を別field化。CreateBoxMon後段のToxtricity、生成後Rockruff/collectionform変化は実caller未結合。',
            '95行は追加overlayだけ。全通常野生header・既存story配布・custom技の網羅ではない。研究タマゴ配布に両親由来の技を足さない。']}
    model['creation_audit'] = value; model['followup_audit']['summary'].update(value['summary'])
    todo = model['followup_audit']['remaining_work_ja']; targets = [i for i,s in enumerate(todo) if s.startswith('野生初期技と固定配布')]
    need(len(targets)==1,'生成技残件anchor不一致')
    todo[targets[0]] = '追加野生95行・collection配布18/Floette1・collection raid292を現候補level表の初期技source規則に結合済み。残りは全通常野生header/既存story配布、現compiled初期化caller・マクロ、生成後form変更/custom技。条件付き計算を実生成技受入にしない。'
    model['source_bindings'].update({k:v for k,v in inputs.bindings.items() if k!=STATE})
    return model


def append_pages(files: dict[str, bytes], model: dict) -> None:
    from pr16_candidate_wiki_render import jsonblock, table, Link
    value = model['creation_audit']
    body = '# 野生・配布・raidの初期技監査\n\n[Wiki入口](README.md)\n\n'
    body += '現候補 `'+model['candidate']['sha256']+'`。実moveset受入ではなく、取得tableと固定source規則を分けた監査です。\n\n'
    body += jsonblock(value['summary'])+'\n## 判定境界\n\n'+'\n\n'.join(value['limitations_ja'])+'\n\n'
    body += '野生rollはu8値とthresholdの比較（分母256）。force hidden scanはrollを迂回します。badge/rod・昼夜/群れ・殿堂入り前後を省略しません。\n\n'
    body += '## 配布/raid宣言\n\n'+table(['経路','種別','Species','level','解禁'],[(r['route_key'],r['kind'],Link(f'[{r["species_id"]}](pokemon/{r["species_id"]}.md)'),f'{r["level_min"]}–{r["level_max"]}',r.get('unlock',r.get('unlock_item_id'))) for r in value['routes']])
    body += '\n[レベル別初期技profile](data/creation_profiles.jsonl) / [追加野生slot](data/wild_overlay_creation.json) / [source証拠と入口](data/creation_audit.json)\n'
    files['CREATION_MOVESET_AUDIT.md']=body.encode()
    files['data/creation_profiles.jsonl']=b''.join(stable(r).replace(b'\n',b'')+b'\n' for r in value['profiles'])
    files['data/wild_overlay_creation.json']=stable({'candidate':model['candidate'],'table':value['overlay_table'],'entries':value['wild_overlay']})
    files['data/creation_audit.json']=stable({k:v for k,v in value.items() if k not in ('profiles','wild_overlay')})
    for name in ('README.md','RUNTIME_LIMITATIONS.md','CODEX_INDEX.md'):
        files[name]+='\n[野生・配布・raid初期技のsource規則と残件](CREATION_MOVESET_AUDIT.md)\n'.encode()
