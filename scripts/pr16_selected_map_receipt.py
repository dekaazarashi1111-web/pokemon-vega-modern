#!/usr/bin/env python3
"""保存済みmap測定の意味を検査する。ROM再構成・lookup再実行はしない。"""
from __future__ import annotations
import pr16_selected_map_asset as parent

BASE_HEAD = '290c2d16c45d6cea2617e91216966a2329a5d566'
SOURCE_HEAD = '164eb78e03fd4a01a8cfc236da836ee525a95650'
RUN = 38177623055
ARTIFACT = dict(id=11717235226, name='pr16-selected-map-asset-public-text',
                size=438487, sha256='c0729cab350b4619d8336b717bcff30b0cf34e6c6c8b703f29159ab2ccc04977')
NEXT = 'SAVE_CAPACITY_SELECTED_ASSET_OWNER_AFTER_MAP_PROBE'
GOAL = ('0x0880FA64の実asset所有元と全4byteの実readerを特定する。'
        '訂正後の旧68 descriptorと実lookup由来128×128有限入力では一致0件。'
        '一致したmap候補は保存されていないので、候補がある前提では再開しない。'
        '未調査の入力・他asset経路を具体的な参照元から絞る。0件は全map不存在証明ではない。'
        '受入済みmap32試験/ARM配置/lookup/probe、旧LZ探索/30試験、Wikiは無変更再走しない。'
        '正式789/85・選定残6・安全容量0。窓外跨り/間接参照/退役移管/heap/controller/局所Saveは未完。')


def integer(value, minimum, maximum):
    parent.need(type(value) is int and minimum <= value <= maximum, '厳密な有限整数')
    return value


def zero(value):
    return integer(value, 0, 0)


def summarize(proof):
    """hashで束縛された保存証拠だけを要約し、負結果の範囲外への昇格を拒否。"""
    parent.need(proof['candidate'] == parent.CANDIDATE and
                proof['origin'] == dict(address=parent.HIT, **parent.HIT_ID), '候補/対象identity')
    parent.checked_layout(proof['corrected_arm_layout'])
    parent.need(proof['prior_descriptor_decoder_abi_mismatch'] is True and
                proof['prior_measurement_rewritten'] is False and
                proof['prior_zero_lz_search_replayed'] is False, '旧原本/別scope保全')
    rows = proof['descriptor_candidates']
    parent.need(type(rows) is list and len(rows) == 68 and
                len({r['symbol'] for r in rows}) == 68, '旧68候補の一意性')
    valid = sum(not r['invalid_data_fields'] for r in rows)
    parent.need(valid == integer(proof['valid_descriptor_candidates'], 0, 68), 'descriptor件数一致')
    parent.need(all(not r['bounded_distances'] for r in rows), '別の旧候補一致がある場合は要再判断')
    lookup, root, maps = proof['actual_lookup'], proof['actual_root'], proof['map_probe']
    parent.need(lookup['group'] == lookup['number'] == 0 and
                lookup['conditional_actual_thumb_interpretation'] is True and
                lookup['natural_map_validity_proven'] is False, 'lookup条件付き根')
    start, end = lookup['code']['start'], lookup['code']['end_exclusive']
    integer(start, parent.BASE, 0x0A000000-2);integer(end-start, 2, 256)
    parent.need(start <= root['literal_address'] < end and
                root['first_header'] == lookup['result'], '保存lookupのliteral/戻り値')
    reads = {r['address'] for r in lookup['data_reads'] if r['size'] == 4}
    parent.need({root['literal_address'], root['root'], root['first_bank']} <= reads, '実read連鎖')
    parent.need(maps['root']['address'] == root['root'] and maps['root']['size'] == 512, '同じ有限root')
    bounds = maps['input_bounds']
    parent.need(set(bounds) == {'groups','maps_per_group','total_probes'} and
                all(type(v) is int for v in bounds.values()) and
                bounds == dict(groups=128, maps_per_group=128, total_probes=16384), '受入入力矩形')
    parent.need(type(maps['matches']) is list and not maps['matches'] and
                type(proof['selected_lookup_profiles']) is list and not proof['selected_lookup_profiles'],
                '一致0を選定mapありとして扱わない')
    parent.need(maps['whole_map_inventory_claimed'] is False and maps['all_rom_scan'] is False and
                maps['actual_asset_reader_proven'] is False and proof['actual_asset_reader_proven'] is False,
                '不成立/限定性の保持')
    zero(proof['formal_classification_changes']);zero(proof['donor_safe_bytes']);zero(maps['donor_safe_bytes'])
    return dict(corrected_descriptor_candidates=len(rows), valid_descriptor_candidates=valid,
                bounded_map_inputs=16384, unique_headers=integer(maps['unique_headers'], 0, 16384),
                unique_layouts=len(maps['layouts']), unique_descriptors=len(maps['descriptors']),
                matching_candidates=0, selected_lookup_profiles=0,
                owner_identified=False, actual_asset_reader_proven=False,
                global_map_absence_proven=False, formal_classified=789, formal_unclassified=85,
                selected_unknown_origins=6, donor_safe_bytes=0, next_action_id=NEXT)
