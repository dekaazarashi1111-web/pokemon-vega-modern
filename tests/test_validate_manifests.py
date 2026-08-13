#!/usr/bin/env python3
"""T05を含むmanifest validatorの焦点テスト。"""

from __future__ import annotations

import copy
import csv
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))

import validate_manifests as validator  # noqa: E402


def _write_csv(path: Path, header: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8', newline='') as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=header,
            lineterminator='\n',
            extrasaction='ignore',
        )
        writer.writeheader()
        writer.writerows(rows)


def _blank_row(filename: str) -> dict[str, str]:
    row = {field: 'NONE' for field in validator.EXPECTED[filename]}
    row['notes'] = ''
    return row


def _type_display_fields(canonical_id: int) -> dict[str, str]:
    if canonical_id == 23:
        icon = (32, 12, 224)
        color = (29, 17, 25, 26173)
    elif canonical_id == 24:
        icon = (32, 12, 228)
        color = (31, 31, 31, 32767)
    else:
        icon = (32, 12, canonical_id * 4)
        red = canonical_id % 32
        green = (canonical_id * 2) % 32
        blue = (canonical_id * 3) % 32
        color = (red, green, blue, red | (green << 5) | (blue << 10))
    return {
        'icon_width': str(icon[0]),
        'icon_height': str(icon[1]),
        'icon_tile_offset': str(icon[2]),
        'icon_source': 'CFRU_MOVE_MENU_INFO_ICONS',
        'color_r': str(color[0]),
        'color_g': str(color[1]),
        'color_b': str(color[2]),
        'color_bgr555': str(color[3]),
        'color_source': 'CFRU_TERA_TYPE_COLOR',
    }


def _complete_qol_row(key: str, line_no: int) -> dict[str, str]:
    row = _blank_row('item_ids.csv')
    row.update(
        {
            'item_key': key,
            'id': str(line_no),
            'vega_id': str(line_no),
            'cfru_id': str(line_no),
            'cfru_symbol': f'ITEM_TEST_{line_no}',
            'classification': 'VEGA_CFRU_CANONICAL',
            'display_name': key,
            'description_key': f'DESC_TEST_{line_no}',
            'icon_key': f'ICON_TEST_{line_no}',
            'palette_key': f'PALETTE_TEST_{line_no}',
            'pocket': 'POCKET_ITEMS',
            'price': '1000',
            'importance': '0',
            'role': 'QOL_ITEM',
            'item_type_key': 'ITEM_TYPE_TEST_0',
            'item_type_id': '0',
            'item_type_explicit': '0',
            'item_type_source': 'TEST_ITEM_TYPE_SOURCE',
            'source_mystery': '0',
            'is_evolution_stone': '0',
            'is_evolution_item': '0',
            'consume_policy': 'ON_EFFECT',
            'target_policy': 'PARTY_ONE',
            'supply_key': f'SUPPLY_TEST_{line_no}',
            'runtime_binding': 'CFRU_RUNTIME',
            'status': 'FROZEN',
            '__line__': str(line_no + 2),
        }
    )
    if key in validator.BREEDING_ITEMS:
        row['hold_effect_key'] = 'HOLD_EFFECT_TEST'
    if key in (
        validator.MINT_ITEMS
        | validator.ABILITY_ITEMS
        | validator.HYPER_TRAINING_ITEMS
    ):
        row.update(
            {
                'field_effect_key': 'FIELD_EFFECT_TEST',
                'field_effect_param': 'FIELD_PARAM_TEST',
                'field_use_callback_key': 'FIELD_USE_TEST',
            }
        )
    if key in validator.OVAL_CHARM_ITEMS:
        row['field_effect_key'] = 'BREEDING_CHECK_X2_CAP100'
    if key in validator.EXPERIENCE_CANDIES:
        row.update(
            {
                'vega_id': 'NONE',
                'cfru_id': 'NONE',
                'cfru_symbol': 'NONE',
                'classification': 'QOL_APPEND',
                'field_effect_key': 'EXP_ADD_FIXED',
                'field_effect_param': str(validator.EXPERIENCE_CANDIES[key]),
                'field_use_callback_key': 'FIELD_USE_EXP_CANDY',
                'runtime_binding': 'T06_RUNTIME_BIND_PENDING',
                'status': 'APPENDED',
            }
        )
    if key in validator.EV_RESET_ITEMS:
        row.update(
            {
                'vega_id': 'NONE',
                'cfru_id': 'NONE',
                'cfru_symbol': 'NONE',
                'classification': 'QOL_APPEND',
                'field_effect_key': 'EV_SET_ZERO',
                'field_effect_param': key.removeprefix('ITEM_KEY_EV_RESET_'),
                'field_use_callback_key': 'FIELD_USE_EV_RESET',
                'runtime_binding': 'T06_RUNTIME_BIND_PENDING',
                'status': 'APPENDED',
            }
        )
    if key in set(validator.EXPERIENCE_CANDIES) | validator.EV_RESET_ITEMS:
        row.update(
            {
                'item_type_key': 'ITEM_TYPE_QOL_FIELD_ITEM',
                'item_type_id': '0',
                'item_type_explicit': '0',
                'item_type_source': 'docs/QOL_POLICY.md',
                'source_mystery': '0',
                'is_evolution_stone': '0',
                'is_evolution_item': '0',
            }
        )
    row['field_effect_key'] = validator.QOL_FIELD_EFFECTS[key]
    if key in validator.QOL_FIELD_PARAMS:
        row['field_effect_param'] = validator.QOL_FIELD_PARAMS[key]
    if key in validator.HELD_BREEDING_ITEMS:
        row['consume_policy'] = 'NEVER'
        row['target_policy'] = 'HELD'
    if key in validator.PASSIVE_KEY_ITEMS:
        row['consume_policy'] = 'NEVER'
        row['target_policy'] = 'PASSIVE_KEY_ITEM'
    if key in validator.QOL_ASSET_BINDINGS:
        row['icon_key'], row['palette_key'] = validator.QOL_ASSET_BINDINGS[key]
    return row


def _qol_rows() -> list[dict[str, str]]:
    return [
        _complete_qol_row(key, index)
        for index, key in enumerate(sorted(validator.QOL_REQUIRED_ITEMS))
    ]


def _full_t05_fixture() -> tuple[
    dict[str, list[dict[str, str]]],
    list[dict[str, str]],
    dict[str, dict[str, int]],
]:
    ability_rows: list[dict[str, str]] = []
    ability_sources = {f'ABILITY_TEST_{index}': index for index in range(311)}
    for canonical_id in range(312):
        row = _blank_row('ability_ids.csv')
        row.update(
            {
                'ability_key': f'ABILITY_KEY_TEST_{canonical_id}',
                'id': str(canonical_id),
                'vega_id': str(canonical_id) if canonical_id < 78 else 'NONE',
                'classification': (
                    'VEGA_EXCLUSIVE'
                    if canonical_id == 77
                    else 'VEGA_CFRU_CANONICAL'
                    if canonical_id < 77
                    else 'CFRU_APPEND'
                ),
                'display_name': f'Ability {canonical_id}',
                'description_key': f'ABILITY_DESC_{canonical_id}',
                'effect_key': f'ABILITY_EFFECT_{canonical_id}',
                'runtime_binding': 'CFRU_RUNTIME',
                'status': 'FROZEN' if canonical_id < 78 else 'APPENDED',
            }
        )
        source_id = canonical_id if canonical_id < 77 else canonical_id - 1
        if canonical_id != 77:
            symbol = f'ABILITY_TEST_{source_id}'
            row.update(
                {
                    'cfru_id': str(source_id),
                    'cfru_symbol': symbol,
                    'dpe_symbol': symbol,
                }
            )
        ability_rows.append(row)

    existing_qol = sorted(
        validator.QOL_REQUIRED_ITEMS
        - set(validator.EXPERIENCE_CANDIES)
        - validator.EV_RESET_ITEMS
    )
    appended_qol = sorted(set(validator.EXPERIENCE_CANDIES) | validator.EV_RESET_ITEMS)
    source_symbols = {
        index: (
            'ITEM_DIRE_HIT'
            if index == 74
            else 'ITEM_POKE_DOLL'
            if index == 80
            else 'ITEM_CHESTO_BERRY'
            if index == 134
            else 'ITEM_CHOICE_BAND'
            if index == 186
            else 'ITEM_GOLD_TEETH'
            if index == 348
            else f'ITEM_TEST_{index}'
        )
        for index in range(774)
    }
    item_sources = {symbol: source_id for source_id, symbol in source_symbols.items()}
    item_aliases = {
        **item_sources,
        'ITEM_TEST_ENIGMA_ALIAS': 175,
        **{f'ITEM_TMHM_ALIAS_{index}': 289 + index for index in range(52)},
    }
    identity_source_ids = (set(range(161)) - {80, 134}) | {186, 348}
    item_rows: list[dict[str, str]] = []
    # Synthetic merged space: exactly 161 proven identities in Vega 0..374,
    # then the remaining 613 CFRU source IDs and 11 QOL-only rows.
    for canonical_id in range(375):
        source_id = (
            348
            if canonical_id == 353
            else canonical_id
            if canonical_id in identity_source_ids and canonical_id != 348
            else None
        )
        row = _blank_row('item_ids.csv')
        row.update(
            {
                'item_key': f'ITEM_KEY_TEST_{canonical_id}',
                'id': str(canonical_id),
                'vega_id': str(canonical_id),
                'cfru_id': str(source_id) if source_id is not None else 'NONE',
                'cfru_symbol': source_symbols[source_id] if source_id is not None else 'NONE',
                'classification': 'VEGA_CFRU_CANONICAL' if source_id is not None else 'VEGA_EXCLUSIVE',
                'display_name': f'Item {canonical_id}',
                'description_key': f'ITEM_DESC_{canonical_id}',
                'icon_key': f'ITEM_ICON_{canonical_id}',
                'palette_key': f'ITEM_PALETTE_{canonical_id}',
                'pocket': 'POCKET_ITEMS',
                'price': '1000',
                'importance': '0',
                'role': 'ITEM',
                'item_type_key': 'ITEM_TYPE_TEST_0',
                'item_type_id': '0',
                'item_type_explicit': '0',
                'item_type_source': 'TEST_ITEM_TYPE_SOURCE',
                'source_mystery': '0',
                'is_evolution_stone': '0',
                'is_evolution_item': '0',
                'consume_policy': 'ON_EFFECT',
                'target_policy': 'PARTY_ONE',
                'supply_key': f'SUPPLY_TEST_{canonical_id}',
                'runtime_binding': 'CFRU_RUNTIME',
                'status': 'FROZEN',
            }
        )
        item_rows.append(row)
    item_rows[74]['item_key'] = 'ITEM_KEY_DIRE_HIT'
    item_rows[186]['item_key'] = 'ITEM_KEY_CHOICE_BAND'
    item_rows[353]['item_key'] = 'ITEM_KEY_GOLD_TEETH'
    next_canonical_id = 375
    for source_id in sorted(set(range(774)) - identity_source_ids):
        row = _blank_row('item_ids.csv')
        row.update(
            {
                'item_key': f'ITEM_KEY_APPEND_{source_id}',
                'id': str(next_canonical_id),
                'vega_id': 'NONE',
                'cfru_id': str(source_id),
                'cfru_symbol': source_symbols[source_id],
                'classification': 'CFRU_APPEND',
                'display_name': f'Item {source_id}',
                'description_key': f'ITEM_DESC_{source_id}',
                'icon_key': f'ITEM_ICON_{source_id}',
                'palette_key': f'ITEM_PALETTE_{source_id}',
                'pocket': 'POCKET_ITEMS',
                'price': '1000',
                'importance': '0',
                'role': 'ITEM',
                'item_type_key': 'ITEM_TYPE_TEST_0',
                'item_type_id': '0',
                'item_type_explicit': '0',
                'item_type_source': 'TEST_ITEM_TYPE_SOURCE',
                'source_mystery': '0',
                'is_evolution_stone': '0',
                'is_evolution_item': '0',
                'consume_policy': 'ON_EFFECT',
                'target_policy': 'PARTY_ONE',
                'supply_key': f'SUPPLY_TEST_{source_id}',
                'runtime_binding': 'CFRU_RUNTIME',
                'status': 'APPENDED',
            }
        )
        item_rows.append(row)
        next_canonical_id += 1
    for index, key in enumerate(existing_qol):
        replacement = _complete_qol_row(key, index)
        original = item_rows[index]
        replacement.update(
            {
                'id': str(index),
                'vega_id': str(index),
                'cfru_id': original['cfru_id'],
                'cfru_symbol': original['cfru_symbol'],
                'classification': original['classification'],
                'status': 'FROZEN',
            }
        )
        replacement.pop('__line__')
        item_rows[index] = replacement
    for offset, key in enumerate(appended_qol, 988):
        row = _complete_qol_row(key, offset)
        row['id'] = str(offset)
        row.pop('__line__')
        item_rows.append(row)

    # Exercise all 63 type IDs, with exactly 465 explicit rows.
    for canonical_id, row in enumerate(item_rows):
        item_type_id = canonical_id % 63
        if row['classification'] != 'QOL_APPEND':
            row.update(
                {
                    'item_type_key': f'ITEM_TYPE_TEST_{item_type_id}',
                    'item_type_id': str(item_type_id),
                    'item_type_explicit': '1' if canonical_id < 465 else '0',
                    'item_type_source': 'TEST_ITEM_TYPE_SOURCE',
                    'is_evolution_stone': '0',
                    'is_evolution_item': '0',
                }
            )
    for canonical_id in range(200, 212):
        item_rows[canonical_id].update(
            {
                'item_type_key': 'ITEM_TYPE_EVOLUTION_STONE',
                'item_type_id': '53',
                'item_type_explicit': '1',
                'is_evolution_stone': '1',
            }
        )
    for canonical_id in range(212, 252):
        item_rows[canonical_id].update(
            {
                'item_type_key': 'ITEM_TYPE_EVOLUTION_ITEM',
                'item_type_id': '54',
                'item_type_explicit': '1',
                'is_evolution_item': '1',
                'hold_effect_key': (
                    'HOLD_EFFECT_EVOLUTION' if canonical_id < 221 else 'NONE'
                ),
            }
        )
    for ball_index, canonical_id in enumerate(range(300, 327)):
        item_rows[canonical_id].update(
            {
                'pocket': 'POCKET_POKE_BALLS',
                'role': 'BALL',
                'ball_kind': f'BALL_KIND_TEST_{ball_index}',
            }
        )
    item_rows[327]['pocket'] = 'POCKET_KEY_ITEMS'
    item_rows[328]['pocket'] = 'POCKET_TM_CASE'
    item_rows[329]['pocket'] = 'POCKET_BERRIES'
    for canonical_id, key, source_mystery in (
        (330, 'ITEM_KEY_TM01', '1'),
        (331, 'ITEM_KEY_HM01_CUT', '121'),
        (332, 'ITEM_KEY_CHERI_BERRY', '1'),
    ):
        item_rows[canonical_id]['item_key'] = key
        item_rows[canonical_id]['source_mystery'] = source_mystery
    next(
        row for row in item_rows if row['item_key'] == 'ITEM_KEY_LONELY_MINT'
    )['source_mystery'] = '1'

    real_type_ids = set(range(18)) | {19, 20, 23, 24}
    type_sources = {f'TYPE_TEST_{index}': index for index in sorted(real_type_ids)}
    type_rows: list[dict[str, str]] = []
    for canonical_id in range(25):
        row = _blank_row('type_ids.csv')
        classification = 'VEGA_CFRU_CANONICAL'
        status = 'FROZEN'
        if canonical_id >= 18:
            classification = (
                'CFRU_APPEND'
                if canonical_id in {23, 24}
                else 'CFRU_SENTINEL'
                if canonical_id in {19, 20}
                else 'CFRU_RESERVED'
            )
            status = 'APPENDED' if classification == 'CFRU_APPEND' else 'RESERVED'
        key = f'TYPE_KEY_TEST_{canonical_id}'
        if canonical_id == 23:
            key = 'TYPE_KEY_FAIRY'
        elif canonical_id == 24:
            key = 'TYPE_KEY_STELLAR'
        row.update(
            {
                'type_key': key,
                'id': str(canonical_id),
                'vega_id': str(canonical_id) if canonical_id < 18 else 'NONE',
                'cfru_id': str(canonical_id),
                'classification': classification,
                'display_name': f'Type {canonical_id}',
                'icon_key': f'TYPE_ICON_{canonical_id}',
                'color_key': f'TYPE_COLOR_{canonical_id}',
                'effectiveness_key': f'TYPE_EFFECTIVENESS_{canonical_id}',
                **_type_display_fields(canonical_id),
                'special_rule': (
                    'FAIRY_CFRU_MATRIX'
                    if canonical_id == 23
                    else 'STELLAR_CFRU_SPECIAL'
                    if canonical_id == 24
                    else 'NONE'
                ),
                'status': status,
            }
        )
        if canonical_id in real_type_ids:
            symbol = f'TYPE_TEST_{canonical_id}'
            if canonical_id == 23:
                symbol = 'TYPE_FAIRY'
            elif canonical_id == 24:
                symbol = 'TYPE_STELLAR'
            row['cfru_symbol'] = symbol
            row['dpe_symbol'] = symbol
        if canonical_id in {23, 24}:
            row['tera_input_code'] = str(canonical_id + 1)
        type_rows.append(row)
    type_sources = {
        row['cfru_symbol']: int(row['cfru_id'])
        for row in type_rows
        if row['cfru_symbol'] != 'NONE'
    }

    range_rows = [
        {'domain': 'ability', 'owner': 'Vega', 'start_id': '0', 'end_id': '77', 'status': 'FROZEN', 'notes': ''},
        {'domain': 'ability', 'owner': 'CFRU-JP', 'start_id': '78', 'end_id': '311', 'status': 'ALLOCATED', 'notes': ''},
        {'domain': 'item', 'owner': 'Vega', 'start_id': '0', 'end_id': '374', 'status': 'FROZEN', 'notes': ''},
        {'domain': 'item', 'owner': 'CFRU-JP', 'start_id': '375', 'end_id': '987', 'status': 'ALLOCATED', 'notes': ''},
        {'domain': 'item', 'owner': 'QOL', 'start_id': '988', 'end_id': '998', 'status': 'ALLOCATED', 'notes': ''},
        {'domain': 'type', 'owner': 'Vega', 'start_id': '0', 'end_id': '17', 'status': 'FROZEN', 'notes': ''},
        {'domain': 'type', 'owner': 'CFRU-JP', 'start_id': '18', 'end_id': '24', 'status': 'ALLOCATED', 'notes': ''},
    ]
    sources = {
        'cfru_ability': ability_sources,
        'dpe_ability': ability_sources,
        'cfru_item': item_sources,
        'cfru_item_aliases': item_aliases,
        'cfru_type': type_sources,
        'dpe_type': type_sources,
    }
    return (
        {
            'ability_ids.csv': ability_rows,
            'item_ids.csv': item_rows,
            'type_ids.csv': type_rows,
        },
        range_rows,
        sources,
    )


def _write_complete_manifest_fixture(root: Path) -> None:
    shutil.copytree(ROOT / 'manifests', root / 'manifests')
    loaded, t05_ranges, _ = _full_t05_fixture()
    for filename, rows in loaded.items():
        _write_csv(root / 'manifests' / filename, validator.EXPECTED[filename], rows)
    with (ROOT / 'manifests/id_ranges.csv').open(encoding='utf-8', newline='') as handle:
        non_t05_ranges = [
            row
            for row in csv.DictReader(handle)
            if row['domain'] not in {'ability', 'item', 'type'}
        ]
    _write_csv(
        root / 'manifests/id_ranges.csv',
        validator.EXPECTED['id_ranges.csv'],
        non_t05_ranges + t05_ranges,
    )


class ValidateManifestsTests(unittest.TestCase):
    def test_pinned_sources_include_enum_items_and_match_dpe(self) -> None:
        errors: list[str] = []
        sources = validator._validate_pinned_source_shapes(ROOT, errors)
        self.assertEqual(errors, [])
        self.assertEqual(len(sources['cfru_ability']), 311)
        self.assertEqual(len(sources['cfru_item']), 774)
        self.assertEqual(sources['cfru_item']['ITEM_NORMALIUM_Z'], 0x244)
        self.assertEqual(sources['cfru_item']['ITEM_TAPUNIUM_Z'], 0x265)
        self.assertEqual(sources['cfru_item'], sources['dpe_item'])
        self.assertEqual(len(validator.PINNED_SOURCE_HEADERS), 7)
        self.assertEqual(len(sources['cfru_item_aliases']), 827)
        self.assertEqual(sources['cfru_item_aliases']['ITEM_ENIGMA_BERRY'], 175)
        self.assertEqual(sources['cfru_item_aliases']['ITEM_TM02_DRAGON_CLAW'], 290)
        self.assertEqual(sources['cfru_item_aliases']['ITEM_HM05_FLASH'], 343)
        self.assertEqual(len(sources['cfru_type']), 22)

    def test_header_only_legacy_t05_placeholders_remain_valid(self) -> None:
        with tempfile.TemporaryDirectory(prefix='manifest-empty-') as raw:
            root = Path(raw)
            for filename, header in validator.EXPECTED.items():
                selected = validator.T05_LEGACY_HEADERS.get(filename, header)
                _write_csv(root / 'manifests' / filename, selected, [])
            self.assertEqual(validator.collect_errors(root), [])

    def test_generated_manifests_pass_when_all_pinned_sources_are_absent(self) -> None:
        with tempfile.TemporaryDirectory(prefix='manifest-source-only-') as raw:
            root = Path(raw)
            _write_complete_manifest_fixture(root)
            self.assertFalse((root / 'vendor/upstream').exists())
            self.assertEqual(validator.collect_errors(root), [])

    def test_generated_manifests_fail_when_only_some_pinned_sources_exist(self) -> None:
        with tempfile.TemporaryDirectory(prefix='manifest-partial-source-') as raw:
            root = Path(raw)
            _write_complete_manifest_fixture(root)
            relative = Path(validator.PINNED_SOURCE_HEADERS[0])
            destination = root / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, destination)
            errors = validator.collect_errors(root)
            self.assertTrue(
                any(
                    'pinned source headers must be all present or all absent' in error
                    for error in errors
                ),
                errors,
            )

    def test_legacy_t05_header_is_rejected_after_first_data_row(self) -> None:
        with tempfile.TemporaryDirectory(prefix='manifest-legacy-data-') as raw:
            root = Path(raw)
            for filename, header in validator.EXPECTED.items():
                selected = validator.T05_LEGACY_HEADERS.get(filename, header)
                rows: list[dict[str, str]] = []
                if filename == 'ability_ids.csv':
                    rows = [{field: 'X' for field in selected}]
                _write_csv(root / 'manifests' / filename, selected, rows)
            errors = validator.collect_errors(root)
            self.assertTrue(any('ability_ids.csv: header mismatch' in error for error in errors))

    def test_qol_contract_accepts_all_45_stable_keys(self) -> None:
        rows = _qol_rows()
        errors: list[str] = []
        validator._validate_qol_items(rows, errors)
        self.assertEqual(len(rows), 45)
        self.assertEqual(errors, [])

    def test_qol_contract_rejects_wrong_exp_and_ev_berry_alias(self) -> None:
        rows = _qol_rows()
        by_key = {row['item_key']: row for row in rows}
        by_key['ITEM_KEY_EXP_CANDY_XL']['field_effect_param'] = '29999'
        by_key['ITEM_KEY_EV_RESET_HP']['cfru_symbol'] = 'ITEM_POMEG_BERRY'
        by_key['ITEM_KEY_EV_RESET_HP']['cfru_id'] = '153'
        errors: list[str] = []
        validator._validate_qol_items(rows, errors)
        self.assertTrue(any('must grant exactly 30000 EXP' in error for error in errors))
        self.assertTrue(any('must not alias an EV berry' in error for error in errors))

    def test_fairy_and_stellar_require_complete_display_and_tera_mapping(self) -> None:
        rows = []
        for key, canonical_id in (('TYPE_KEY_FAIRY', 23), ('TYPE_KEY_STELLAR', 24)):
            row = _blank_row('type_ids.csv')
            row.update(
                {
                    'type_key': key,
                    'id': str(canonical_id),
                    'cfru_id': str(canonical_id),
                    'cfru_symbol': key.replace('_KEY', ''),
                    'dpe_symbol': key.replace('_KEY', ''),
                    'classification': 'CFRU_APPEND',
                    'display_name': key,
                    'icon_key': f'{key}_ICON',
                    'color_key': f'{key}_COLOR',
                    'effectiveness_key': f'{key}_EFFECTIVENESS',
                    **_type_display_fields(canonical_id),
                    'special_rule': (
                        'FAIRY_CFRU_MATRIX'
                        if key == 'TYPE_KEY_FAIRY'
                        else 'STELLAR_CFRU_SPECIAL'
                    ),
                    'tera_input_code': str(canonical_id + 1),
                    'status': 'APPENDED',
                    '__line__': str(canonical_id),
                }
            )
            rows.append(row)
        errors: list[str] = []
        validator._validate_types(rows, errors)
        self.assertEqual(errors, [])
        rows[1]['icon_key'] = 'NONE'
        rows[0]['tera_input_code'] = '23'
        validator._validate_types(rows, errors := [])
        self.assertTrue(any('requires icon_key' in error for error in errors))
        self.assertTrue(any('tera input code 24' in error for error in errors))

    def test_stellar_reserved_or_incomplete_contract_is_rejected(self) -> None:
        rows = []
        for key, canonical_id, special_rule in (
            ('TYPE_KEY_FAIRY', 23, 'FAIRY_CFRU_MATRIX'),
            ('TYPE_KEY_STELLAR', 24, 'STELLAR_CFRU_SPECIAL'),
        ):
            row = _blank_row('type_ids.csv')
            row.update(
                {
                    'type_key': key,
                    'id': str(canonical_id),
                    'cfru_id': str(canonical_id),
                    'cfru_symbol': key.replace('_KEY', ''),
                    'dpe_symbol': key.replace('_KEY', ''),
                    'classification': 'CFRU_APPEND',
                    'display_name': key,
                    'icon_key': f'{key}_ICON',
                    'color_key': f'{key}_COLOR',
                    'effectiveness_key': f'{key}_EFFECTIVENESS',
                    **_type_display_fields(canonical_id),
                    'special_rule': special_rule,
                    'tera_input_code': str(canonical_id + 1),
                    'status': 'APPENDED',
                    '__line__': str(canonical_id),
                }
            )
            rows.append(row)
        stellar = rows[1]
        stellar['classification'] = 'CFRU_RESERVED'
        stellar['status'] = 'RESERVED'
        stellar['special_rule'] = 'STELLAR_RESERVED_DEFERRED_T09'
        stellar['effectiveness_key'] = 'NONE'
        errors: list[str] = []
        validator._validate_types(rows, errors)
        self.assertTrue(any('classification=CFRU_APPEND' in error for error in errors))
        self.assertTrue(any('STELLAR_CFRU_SPECIAL' in error for error in errors))
        self.assertTrue(any('requires complete effectiveness_key' in error for error in errors))

    def test_active_type_display_ranges_and_added_type_values_are_rejected(self) -> None:
        loaded, ranges, sources = _full_t05_fixture()
        broken = copy.deepcopy(loaded)
        broken['type_ids.csv'][0]['color_r'] = '32'
        broken['type_ids.csv'][23]['icon_tile_offset'] = '225'
        broken['type_ids.csv'][24]['color_bgr555'] = '0'
        with mock.patch.object(
            validator, '_validate_pinned_source_shapes', return_value=sources
        ):
            validator._validate_t05_manifests(ROOT, broken, ranges, errors := [])
        self.assertTrue(any('color_r outside 0..31' in error for error in errors))
        self.assertTrue(any('TYPE_KEY_FAIRY icon geometry' in error for error in errors))
        self.assertTrue(any('TYPE_KEY_STELLAR color must be' in error for error in errors))

    def test_dire_hit_identity_and_new_item_ranges_are_fail_closed(self) -> None:
        loaded, ranges, sources = _full_t05_fixture()
        self.assertEqual(len(loaded['item_ids.csv']), 999)
        dire_hit = loaded['item_ids.csv'][74]
        self.assertEqual(
            (
                dire_hit['item_key'],
                dire_hit['vega_id'],
                dire_hit['cfru_id'],
                dire_hit['cfru_symbol'],
            ),
            ('ITEM_KEY_DIRE_HIT', '74', '74', 'ITEM_DIRE_HIT'),
        )
        broken = copy.deepcopy(loaded)
        broken['item_ids.csv'][74]['item_key'] = 'ITEM_KEY_VEGA_074'
        old_ranges = copy.deepcopy(ranges)
        cfru_range = next(
            row for row in old_ranges if row['domain'] == 'item' and row['owner'] == 'CFRU-JP'
        )
        qol_range = next(
            row for row in old_ranges if row['domain'] == 'item' and row['owner'] == 'QOL'
        )
        cfru_range['end_id'] = '988'
        qol_range['start_id'] = '989'
        qol_range['end_id'] = '999'
        with mock.patch.object(
            validator, '_validate_pinned_source_shapes', return_value=sources
        ):
            validator._validate_t05_manifests(ROOT, broken, old_ranges, errors := [])
        self.assertTrue(
            any('missing ITEM_KEY_DIRE_HIT explicit identity mapping' in error for error in errors)
        )
        self.assertTrue(any('item contract must freeze 0..374' in error for error in errors))

    def test_held_and_passive_qol_policy_mismatch_is_rejected(self) -> None:
        rows = _qol_rows()
        by_key = {row['item_key']: row for row in rows}
        by_key['ITEM_KEY_EVERSTONE']['consume_policy'] = 'ON_EFFECT'
        by_key['ITEM_KEY_POWER_BAND']['target_policy'] = 'PARTY_ONE'
        by_key['ITEM_KEY_OVAL_CHARM']['target_policy'] = 'NONE'
        errors: list[str] = []
        validator._validate_qol_items(rows, errors)
        self.assertTrue(any('ITEM_KEY_EVERSTONE must use' in error for error in errors))
        self.assertTrue(any('ITEM_KEY_POWER_BAND must use' in error for error in errors))
        self.assertTrue(any('ITEM_KEY_OVAL_CHARM must use' in error for error in errors))

    def test_new_qol_asset_symbol_mismatch_is_rejected(self) -> None:
        rows = _qol_rows()
        by_key = {row['item_key']: row for row in rows}
        by_key['ITEM_KEY_EXP_CANDY_XS']['icon_key'] = 'ITEM_ICON_RARE_CANDY'
        by_key['ITEM_KEY_EV_RESET_SPEED']['palette_key'] = 'gItemIcon_HondewBerryPal'
        errors: list[str] = []
        validator._validate_qol_items(rows, errors)
        self.assertTrue(any('ITEM_KEY_EXP_CANDY_XS asset binding' in error for error in errors))
        self.assertTrue(any('ITEM_KEY_EV_RESET_SPEED asset binding' in error for error in errors))

    def test_item_taxonomy_ball_evolution_and_source_mystery_are_fail_closed(self) -> None:
        loaded, _, _ = _full_t05_fixture()
        rows = loaded['item_ids.csv']
        validator._validate_item_metadata(rows, errors := [])
        self.assertEqual(errors, [])

        broken = copy.deepcopy(rows)
        by_key = {row['item_key']: row for row in broken}
        by_key['ITEM_KEY_TM01']['source_mystery'] = '-1'
        by_key['ITEM_KEY_CHERI_BERRY']['source_mystery'] = '2'
        broken[0]['source_mystery'] = '256'
        broken[0]['item_type_explicit'] = '0'
        broken[200]['is_evolution_stone'] = '0'
        broken[212]['hold_effect_key'] = 'NONE'
        broken[300]['ball_kind'] = broken[301]['ball_kind']
        broken[328]['pocket'] = 'POCKET_ITEMS'
        validator._validate_item_metadata(broken, errors := [])
        self.assertTrue(any('invalid non-negative source_mystery' in error for error in errors))
        self.assertTrue(
            any("invalid non-negative source_mystery '256'" in error for error in errors)
        )
        self.assertTrue(any('ITEM_KEY_CHERI_BERRY source_mystery must be 1' in error for error in errors))
        self.assertTrue(any('expected 465 explicit item-type rows' in error for error in errors))
        self.assertTrue(any('expected 12 evolution stones' in error for error in errors))
        self.assertTrue(any('expected 9 held+evolution' in error for error in errors))
        self.assertTrue(any('exactly 27 unique BALL rows' in error for error in errors))
        self.assertTrue(any('stable pocket set must be exactly' in error for error in errors))

    def test_identity_and_distinct_append_contracts_are_fail_closed(self) -> None:
        loaded, ranges, sources = _full_t05_fixture()
        broken = copy.deepcopy(loaded)
        choice_band = broken['item_ids.csv'][186]
        choice_band['classification'] = 'VEGA_EXCLUSIVE'
        source_80 = next(
            row for row in broken['item_ids.csv'] if row['cfru_id'] == '80'
        )
        source_80['classification'] = 'CFRU_RESERVED'
        source_80['status'] = 'RESERVED'
        broken['item_ids.csv'][134]['status'] = 'APPENDED'
        with mock.patch.object(
            validator, '_validate_pinned_source_shapes', return_value=sources
        ):
            validator._validate_t05_manifests(ROOT, broken, ranges, errors := [])
        self.assertTrue(any('exactly 161 proven Vega/CFRU identities' in error for error in errors))
        self.assertTrue(any('ITEM_KEY_CHOICE_BAND must identity-map' in error for error in errors))
        self.assertTrue(any('CFRU 80 ITEM_POKE_DOLL must remain' in error for error in errors))
        self.assertTrue(any('Vega 134 must remain' in error for error in errors))

    def test_complete_t05_contract_and_targeted_failures(self) -> None:
        loaded, ranges, sources = _full_t05_fixture()
        with mock.patch.object(
            validator, '_validate_pinned_source_shapes', return_value=sources
        ):
            errors: list[str] = []
            validator._validate_t05_manifests(ROOT, loaded, ranges, errors)
        self.assertEqual(errors, [])

        broken = copy.deepcopy(loaded)
        broken['ability_ids.csv'][100]['id'] = '999'
        broken['ability_ids.csv'][101]['cfru_symbol'] = broken['ability_ids.csv'][100][
            'cfru_symbol'
        ]
        broken['item_ids.csv'][-1]['vega_id'] = broken['item_ids.csv'][-1]['id']
        with mock.patch.object(
            validator, '_validate_pinned_source_shapes', return_value=sources
        ):
            validator._validate_t05_manifests(ROOT, broken, ranges, errors := [])
        self.assertTrue(any('canonical IDs must be exact contiguous' in error for error in errors))
        self.assertTrue(any('duplicate CFRU ability symbol' in error for error in errors))
        self.assertTrue(any('QOL range contract mismatch' in error for error in errors))


if __name__ == '__main__':
    unittest.main()
