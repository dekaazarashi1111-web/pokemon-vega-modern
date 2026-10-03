"""後継表の未選択Speciesを、既存正本の明示契約へ結び付ける。

sourceのない枠を空表や旧候補表で補わない。非学習枠は型付きの非採用結果、
戦闘姿は持越し専用、未裁定の恒久姿はエラーとして表現する。ROMには書かない。
"""
from __future__ import annotations

import copy
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Any

from tools.pr16_learnset_binding import encode, identity, require

CONSUMERS = ('egg', 'evolution', 'form_change', 'level_up', 'machine',
             'pre_evolution_carry', 'reminder', 'shared_egg', 'tutor')
INTERNAL = {'INTERNAL_EXCLUDED', 'INTERNAL_EXCLUDED_CROSS_ROM_SLOT', 'INTERNAL_EXCLUDED_RESERVED'}
SELECTED = {'OFFICIAL_SOURCE_SELECTED', 'VEGA_SOURCE_SELECTED'}
NONPERMANENT = {'INTERNAL_IDENTITY_ONLY', 'EXCLUDED_REMAKE_FORM_IDENTITY_ONLY',
                'NON_BATTLING_FORM_IDENTITY_ONLY', 'BATTLE_COPY_CARRY_ONLY',
                'BATTLE_FORM_CARRY_ONLY', 'P04_MEGA_CARRY_ONLY'}


class BindingRequired(ValueError):
    """空の習得表へ変換してはならない未接続状態。"""


@dataclass(frozen=True)
class NonLearningIdentity:
    """学習ゼロ件ではなく、この経路の恒久学習対象ではないことを表す。"""
    species_id: int
    species_key: str
    policy: str
    preserve_identity: bool = True
    preserve_current_moves: bool = True
    automatic_fallback: bool = False


def pair(rows: Mapping[int, Mapping[str, Any]], sid: int, key: str) -> Mapping[str, Any]:
    require(type(sid) is int and sid >= 0 and sid in rows, 'Species ID不明/型違反')
    require(rows[sid]['species_key'] == key, 'Species ID/key不一致')
    return rows[sid]


def unique(rows: Sequence[Mapping[str, Any]], id_key: str, key_key: str) -> dict[int, Mapping[str, Any]]:
    result = {}
    keys = set()
    for row in rows:
        sid, key = row[id_key], row[key_key]
        require(type(sid) is int and sid >= 0 and isinstance(key, str) and key,
                'identity型不正')
        require(sid not in result and key not in keys, 'identity重複')
        result[sid] = row
        keys.add(key)
    return result


def proof(name: str, value: Any) -> dict[str, Any]:
    return {'contract': name, 'record_sha256': identity(encode(value))['sha256']}


def build_bindings(coverage: list[dict], manifest: Mapping[int, Mapping], contracts: Mapping[str, dict]) -> list[dict]:
    """input全行を変更せず分類。未知区分・key不一致・曖昧なcloneは失敗させる。"""
    all_species = unique(coverage, 'species_id', 'species_key')
    targets = unique(contracts['identity']['target_normalization']['records'], 'canonical_id', 'species_key')
    mega = unique(contracts['p04_species']['records'], 'id', 'species_key')
    links = unique(contracts['p04_mega']['mappings'], 'target_species_id', 'target_species_key')
    require(set(mega) == set(links), 'P04正逆mappingとSpecies集合不一致')
    own = contracts['own_tempo']
    own_id = own['identity']['species_id']
    require(own['identity']['classification'] == 'INTERNAL_CONDITIONAL_FORM'
            and own['p03']['source_route_clone']['policy'] == 'EXACT_LEARNSET_CLONE_WITH_DISTINCT_INTERNAL_SPECIES_OWNER',
            'Own Tempo clone契約不一致')
    own_source = own['p03']['owner_clone']['donor_species']
    require(own_source == own['identity']['normal_species_id'] and own_id != own_source,
            'Own Tempo owner/source混同')
    pair(all_species, own_id, own['identity']['species_key'])
    require(own_source in all_species and all_species[own_source]['selection'] in SELECTED,
            'Own Tempo donorが受入後継表にない')

    # 既存P02の逆変身行だけを証拠として利用する。数字・名前から基底姿を推測しない。
    reverse = {}
    for row in contracts['p02']['current_table']['rows']:
        if row['method']['family'] != 'BATTLE_TRANSFORM' or row['condition']['parameter']['value'] != 0:
            continue
        src, dst = row['source'], row['target']
        pair(all_species, src['canonical_id'], src['species_key'])
        pair(all_species, dst['canonical_id'], dst['species_key'])
        previous = reverse.setdefault(src['canonical_id'], [])
        require(all(r['target']['canonical_id'] != dst['canonical_id'] for r in previous), '逆変身target重複')
        previous.append(row)

    result = []
    for row in coverage:
        if row['selection'] not in ('SOURCE_NOT_SELECTED', 'RUNTIME_EXTENSION_NOT_SELECTED'):
            require(row['selection'] in SELECTED, '未知の選択状態')
            continue
        sid, key = row['species_id'], row['species_key']
        require(row['active_routes'] == 0 and row['automatic_fallback'] is False, '未選択行の無断採用')
        record = {'species_id': sid, 'species_key': key, 'original_selection': row['selection'],
                  'coverage_sha256': identity(encode(row))['sha256'], 'automatic_fallback': False,
                  'preserve_identity': True, 'rewrite_existing_moves': False,
                  'direct_grant_on_transform': False, 'runtime_applied': False}
        if row['selection'] == 'SOURCE_NOT_SELECTED':
            target = pair(targets, sid, key)
            require(row['source_target'] == target, 'P01 target正本不一致')
            require(sid in manifest and manifest[sid]['species_key'] == key
                    and manifest[sid]['form_key'] == target['form_key'], 'manifest Species/Form不一致')
            record['source_target'] = copy.deepcopy(target)
            record['evidence'] = [proof('identity', target), proof('species_manifest', manifest[sid])]
            normalized = target['normalized']
            status, decision = normalized['target_status'], normalized['decision']
            if sid == 649:
                cfg = contracts['caterpie']['target']
                correction = contracts['p03']['correction']['caterpie']
                require(key == cfg['species_key'] == correction['species_key'] == 'SPECIES_KEY_CATERPIE'
                        and cfg['species_id'] == correction['canonical_id'] == 649
                        and target['override'] == 'FIX_LEGACY_TARGET_SWAP_KEEP_ID_649'
                        and normalized == {'apply': True, 'decision': 'REFERENCE', 'target_status': 'REQUIRED_BASE'}
                        and cfg['reference_id'] == correction['reference_id'] == target['reference_id'],
                        'Caterpie ID訂正契約不一致')
                routes = cfg['level_up_routes'] + [cfg['machine_route']]
                require(len(routes) == correction['route_count'] == 4
                        and [r['route_id'] for r in routes] == [r['route_id'] for r in correction['compiled_routes']],
                        'Caterpie旧P03の4経路不一致')
                for actual, original in zip(routes, correction['compiled_routes']):
                    require(all(actual[k] == original[k] for k in ('route_id','consumer','method','project_move_id')),
                            'Caterpie経路identity不一致')
                record.update(policy='EXPLICIT_CATERPIE_IDENTITY_REPAIR', reference_id=cfg['reference_id'],
                              source_species_id=649, routes=copy.deepcopy(routes), official_baseline_record_delta=0)
                record['evidence'] += [proof('caterpie', cfg), proof('p03', correction)]
            else:
                require(normalized['apply'] is False and (target['override'] == 'NONE' or
                        (sid == 412 and key == 'SPECIES_KEY_EGG' and status == 'INTERNAL_EXCLUDED'
                         and target['override'] == 'KEEP_INTERNAL_EGG_EXCLUDED_AT_ID_412')), '許可されない採用訂正')
                if status in INTERNAL:
                    require(decision == 'PRESERVE_VEGA_OR_INTERNAL', '内部枠の保全根拠不一致')
                    record.update(policy='INTERNAL_IDENTITY_ONLY', reason=status)
                elif status == 'BATTLE_ONLY_EXCLUDED_COPY':
                    require(decision == 'PRESERVE_VEGA_OR_INTERNAL', 'battle copy根拠不一致')
                    record.update(policy='BATTLE_COPY_CARRY_ONLY', reason=status)
                elif status == 'BATTLE_ONLY_EXCLUDED':
                    require(decision in ('REFERENCE_ONLY_STAGE61_EXCLUDED','NO_OFFICIAL_BATTLING_FORM'),
                            '戦闘姿の不明な採用区分')
                    record.update(policy='NON_BATTLING_FORM_IDENTITY_ONLY' if decision == 'NO_OFFICIAL_BATTLING_FORM'
                                  else 'BATTLE_FORM_CARRY_ONLY', reason=decision)
                    if sid in reverse:
                        record['reversion_targets'] = [
                            {'species_id': r['target']['canonical_id'], 'species_key': r['target']['species_key'],
                             'condition': copy.deepcopy(r['condition']), 'slot': r['slot']} for r in reverse[sid]]
                        record['reversion_requires_original_form'] = len(reverse[sid]) > 1
                        record['evidence'] += [proof('p02_reverse', r) for r in reverse[sid]]
                elif status == 'OPTIONAL_FORM':
                    require(decision == 'EXCLUDED_REMAKE_ONLY' and target['reference_id'] == '', '任意姿の除外根拠不一致')
                    record.update(policy='EXCLUDED_REMAKE_FORM_IDENTITY_ONLY', reason=decision)
                elif status == 'UNOBTAINABLE_EVENT_FORM_EXCLUDED':
                    gift = contracts['gift']['gift']
                    require(sid == gift['species_id'] == 1029 and key == gift['species_key'] == 'SPECIES_KEY_FLOETTE_ETERNAL'
                            and target['reference_id'] == 'legendsza:0670.05', '恒久gift姿のidentity不一致')
                    # Gift入手許可と公式learnset採用は別。旧gift ROM表を正本へ昇格させない。
                    record.update(policy='GIFT_LEARNSET_ADOPTION_REQUIRED', reference_id=target['reference_id'],
                                  blocking=True, reason='GIFT_EXISTS_BUT_P01_LEARNSET_APPLY_FALSE')
                    record['evidence'].append(proof('gift', gift))
                else:
                    raise ValueError('未知の未選択canonical区分: ' + status)
        else:
            require(row['source_target'] is None and sid not in manifest, 'runtime拡張とmanifestの衝突')
            if sid in mega:
                spec, link = mega[sid], links[sid]
                require(spec['species_key'] == link['target_species_key'] == key
                        and spec['classification'] == 'BATTLE_ONLY_MEGA'
                        and spec['source_species_id'] == link['source_species_id']
                        and spec['source_species_key'] == link['source_species_key']
                        and {'level_up_pointer','tmhm','tutor'} <= set(spec['clone_policy']['source_rows']),
                        'P04 source clone正本不一致')
                pair(all_species, spec['source_species_id'], spec['source_species_key'])
                record.update(policy='P04_MEGA_CARRY_ONLY', source_species_id=spec['source_species_id'],
                              source_species_key=spec['source_species_key'],
                              evidence=[proof('p04_species',spec),proof('p04_mega',link)])
            elif sid == own_id:
                record.update(policy='STAGE75_DISTINCT_OWNER_CLONE', source_species_id=own_source,
                              source_species_key=all_species[own_source]['species_key'],
                              reference_id=own['identity']['reference_id'],
                              source_reference_id=own['p03']['source_route_clone']['source_reference_id'],
                              expected_route_count=own['p03']['source_route_clone']['route_count'],
                              hatch_owner=sid, evolution_policy_changed=False,
                              evidence=[proof('own_tempo', own)])
            else:
                raise ValueError('未知のruntime拡張: ' + key)
        result.append(record)
    return result


def query_routes(block: dict, family: str, binding: dict | None = None, *, donor_block: dict | None = None):
    """通常consumerの入力を解決する。非学習identityを空listへ潰さない。"""
    require(family in CONSUMERS, '未知consumer')
    sid, key = block['species_id'], block['species_key']
    require(type(sid) is int and sid >= 0 and isinstance(key, str) and key, 'block identity不正')
    require(block.get('runtime_applied') is False, 'runtime済みblockは隔離表ではない')
    require(block['selection'] in SELECTED | {'SOURCE_NOT_SELECTED', 'RUNTIME_EXTENSION_NOT_SELECTED'}, '未知selection')
    if block['selection'] in SELECTED:
        require(binding is None, '受入選択種へのbinding上書き')
        result = copy.deepcopy(block['routes'])
    else:
        if binding is None:
            raise BindingRequired(f'{sid}: 明示bindingが必要')
        require(binding['species_id'] == sid and binding['species_key'] == key
                and binding['automatic_fallback'] is False and binding['runtime_applied'] is False
                and binding['original_selection'] == block['selection']
                and binding['rewrite_existing_moves'] is False
                and binding['direct_grant_on_transform'] is False
                and block['routes'] == [], 'binding identity/無断付与')
        policy = binding['policy']
        if policy in NONPERMANENT:
            return NonLearningIdentity(sid,key,policy)
        if policy == 'GIFT_LEARNSET_ADOPTION_REQUIRED':
            raise BindingRequired('1029: gift入手契約はlearnset採用契約ではない。旧表fallback禁止')
        if policy == 'EXPLICIT_CATERPIE_IDENTITY_REPAIR':
            result = []
            for ordinal, source in enumerate(binding['routes']):
                if source['consumer'] != family:
                    continue
                result.append({'species_id':sid,'species_key':key,'form_key':'','consumer':family,
                               'move_id':source['project_move_id'],'move_key':source['move_key'],
                               'source_order':ordinal,'source_id':'binding:caterpie:'+source['route_id'],
                               'layer':'explicit_identity_repair','disposition':'EXPLICIT_BINDING_SELECTED',
                               'conditional_egg':False,'provenance':{'binding':copy.deepcopy(binding['evidence']),
                               'source_route':copy.deepcopy(source)},'runtime_applied':False})
        elif policy == 'STAGE75_DISTINCT_OWNER_CLONE':
            require(donor_block is not None and donor_block['species_id'] == binding['source_species_id']
                    and donor_block['species_key'] == binding['source_species_key']
                    and donor_block['selection'] in SELECTED, 'Own Tempo donor未選択/不一致')
            result = copy.deepcopy(donor_block['routes'])
            for route in result:
                require(route['species_id'] == binding['source_species_id']
                        and route['species_key'] == binding['source_species_key'], 'donor経路のSpecies不一致')
                original_id = route['source_id']
                route['binding_origin'] = {'species_id': route['species_id'], 'species_key': route['species_key'],
                                          'source_id':original_id,'record_sha256':identity(encode(route))['sha256']}
                route.update(species_id=sid, species_key=key, form_key='FORM_KEY_ROCKRUFF_OWN_TEMPO',
                             source_id='binding:own-tempo:'+original_id, layer='explicit_distinct_owner_clone')
        else:
            raise BindingRequired('未知binding方針: ' + policy)
    for route in result:
        require(route['consumer'] == family and route['species_id'] == sid and route['species_key'] == key,
                'consumer/Species区画混入')
        require(type(route['move_id']) is int and 1 <= route['move_id'] <= 1062, '実装外Move/Side Change')
    return result


def summarize(bindings: list[dict]) -> dict:
    blockers = [dict(species_id=r['species_id'],species_key=r['species_key'],policy=r['policy'])
                for r in bindings if r.get('blocking')]
    return {'binding_rows':len(bindings),'policies':dict(sorted(Counter(r['policy'] for r in bindings).items())),
            'blocking':blockers,'automatic_fallback':False,'blanket_deletion':False,
            'official_baseline_records_changed':False,'existing_move_rewrite':False,
            'runtime_applied':False,'issue19_complete':False,'release_ready':False}
