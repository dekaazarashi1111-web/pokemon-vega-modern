from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from common import repo_root

EXPECTED = {
    'id_ranges.csv': ['domain','owner','start_id','end_id','status','notes'],
    'move_ids.csv': ['move_key','id','vega_id','cfru_symbol','classification','display_name','status','notes'],
    'species_ids.csv': ['species_key','id','vega_id','dpe_symbol','classification','display_name','form_key','status','notes'],
    'ability_ids.csv': ['ability_key','id','vega_id','cfru_id','cfru_symbol','dpe_symbol','classification','display_name','description_key','effect_key','runtime_binding','status','notes'],
    'item_ids.csv': ['item_key','id','vega_id','cfru_id','cfru_symbol','classification','display_name','description_key','icon_key','palette_key','pocket','price','importance','role','item_type_key','item_type_id','item_type_explicit','item_type_source','source_mystery','is_evolution_stone','is_evolution_item','hold_effect_key','hold_effect_param','field_effect_key','field_effect_param','field_use_callback_key','battle_usage','battle_effect_key','battle_effect_param','battle_use_callback_key','secondary_id','ball_kind','consume_policy','target_policy','supply_key','runtime_binding','status','notes'],
    'type_ids.csv': ['type_key','id','vega_id','cfru_id','cfru_symbol','dpe_symbol','classification','display_name','icon_key','icon_width','icon_height','icon_tile_offset','icon_source','color_key','color_r','color_g','color_b','color_bgr555','color_source','effectiveness_key','special_rule','tera_input_code','status','notes'],
    'map_ids.csv': ['map_key','group_id','map_id','source_map','classification','status','notes'],
    'trainer_ids.csv': ['trainer_key','id','source_trainer','classification','status','notes'],
    'flags.csv': ['flag_key','id','owner','scope','status','notes'],
    'vars.csv': ['var_key','id','owner','scope','status','notes'],
    'kanto_maps.csv': ['map_key','source_map','scope','import_mode','preserve_npcs','preserve_local_events','status','notes'],
    'kanto_encounters.csv': ['map_key','method','condition','slot','species_key','level_min','level_max','weight','status','notes'],
    'kanto_trainers.csv': ['trainer_key','class_key','party_slot','species_key','level','move1_key','move2_key','move3_key','move4_key','item_key','ability_policy','nature','ai_profile','status','notes'],
    'kanto_items.csv': ['placement_key','map_key','placement_type','item_key','quantity','condition','flag_key','status','notes'],
}
KEY_RE = re.compile(r'^[A-Z][A-Z0-9_]*$')

T05_LEGACY_HEADERS = {
    'ability_ids.csv': ['ability_key','id','vega_id','cfru_symbol','classification','display_name','status','notes'],
    'item_ids.csv': ['item_key','id','vega_id','cfru_symbol','classification','display_name','pocket','status','notes'],
    'type_ids.csv': ['type_key','id','vega_id','cfru_symbol','classification','display_name','status','notes'],
}

PRIMARY_KEYS = {
    'move_ids.csv': 'move_key',
    'species_ids.csv': 'species_key',
    'ability_ids.csv': 'ability_key',
    'item_ids.csv': 'item_key',
    'type_ids.csv': 'type_key',
    'map_ids.csv': 'map_key',
    'trainer_ids.csv': 'trainer_key',
    'flags.csv': 'flag_key',
    'vars.csv': 'var_key',
    'kanto_maps.csv': 'map_key',
    'kanto_items.csv': 'placement_key',
}

T05_FILES = ('ability_ids.csv', 'item_ids.csv', 'type_ids.csv')
NONE = {'', 'NONE'}

T05_ALLOWED_CLASSIFICATIONS = {
    'ability_ids.csv': {'VEGA_CFRU_CANONICAL', 'VEGA_EXCLUSIVE', 'CFRU_APPEND'},
    'item_ids.csv': {
        'VEGA_CFRU_CANONICAL',
        'VEGA_EXCLUSIVE',
        'CFRU_APPEND',
        'CFRU_RESERVED',
        'QOL_APPEND',
    },
    'type_ids.csv': {
        'VEGA_CFRU_CANONICAL',
        'CFRU_APPEND',
        'CFRU_RESERVED',
        'CFRU_SENTINEL',
    },
}

EXPERIENCE_CANDIES = {
    'ITEM_KEY_EXP_CANDY_XS': 100,
    'ITEM_KEY_EXP_CANDY_S': 800,
    'ITEM_KEY_EXP_CANDY_M': 3000,
    'ITEM_KEY_EXP_CANDY_L': 10000,
    'ITEM_KEY_EXP_CANDY_XL': 30000,
}

BREEDING_ITEMS = {
    'ITEM_KEY_EVERSTONE',
    'ITEM_KEY_DESTINY_KNOT',
    'ITEM_KEY_POWER_WEIGHT',
    'ITEM_KEY_POWER_BRACER',
    'ITEM_KEY_POWER_BELT',
    'ITEM_KEY_POWER_ANKLET',
    'ITEM_KEY_POWER_LENS',
    'ITEM_KEY_POWER_BAND',
}

MINT_ITEMS = {
    f'ITEM_KEY_{name}_MINT'
    for name in (
        'LONELY', 'ADAMANT', 'NAUGHTY', 'BRAVE', 'BOLD', 'IMPISH', 'LAX',
        'RELAXED', 'MODEST', 'MILD', 'RASH', 'QUIET', 'CALM', 'GENTLE',
        'CAREFUL', 'SASSY', 'TIMID', 'HASTY', 'JOLLY', 'NAIVE', 'SERIOUS',
    )
}

ABILITY_ITEMS = {'ITEM_KEY_ABILITY_CAPSULE', 'ITEM_KEY_ABILITY_PATCH'}
HYPER_TRAINING_ITEMS = {'ITEM_KEY_BOTTLE_CAP', 'ITEM_KEY_GOLD_BOTTLE_CAP'}
OVAL_CHARM_ITEMS = {'ITEM_KEY_OVAL_CHARM'}
EV_RESET_ITEMS = {
    'ITEM_KEY_EV_RESET_HP',
    'ITEM_KEY_EV_RESET_ATK',
    'ITEM_KEY_EV_RESET_DEF',
    'ITEM_KEY_EV_RESET_SPEED',
    'ITEM_KEY_EV_RESET_SPATK',
    'ITEM_KEY_EV_RESET_SPDEF',
}
QOL_REQUIRED_ITEMS = (
    set(EXPERIENCE_CANDIES)
    | BREEDING_ITEMS
    | MINT_ITEMS
    | ABILITY_ITEMS
    | HYPER_TRAINING_ITEMS
    | OVAL_CHARM_ITEMS
    | EV_RESET_ITEMS
)

QOL_FIELD_EFFECTS = {
    **{key: 'EXP_ADD_FIXED' for key in EXPERIENCE_CANDIES},
    'ITEM_KEY_EVERSTONE': 'BREEDING_NATURE_AND_FORM_INHERIT',
    'ITEM_KEY_DESTINY_KNOT': 'BREEDING_INHERIT_FIVE_IVS',
    **{key: 'BREEDING_FORCE_IV' for key in BREEDING_ITEMS if key.startswith('ITEM_KEY_POWER_')},
    **{key: 'NATURE_MODIFIER_SET_KEEP_PERSONALITY' for key in MINT_ITEMS},
    'ITEM_KEY_ABILITY_CAPSULE': 'ABILITY_NORMAL_SWAP',
    'ITEM_KEY_ABILITY_PATCH': 'ABILITY_HIDDEN_SET',
    'ITEM_KEY_BOTTLE_CAP': 'HYPER_TRAIN_ONE',
    'ITEM_KEY_GOLD_BOTTLE_CAP': 'HYPER_TRAIN_ALL',
    'ITEM_KEY_OVAL_CHARM': 'BREEDING_CHECK_MULTIPLIER_X2_CAP100',
    **{key: 'EV_SET_ZERO' for key in EV_RESET_ITEMS},
}

QOL_FIELD_PARAMS = {
    **{key: str(value) for key, value in EXPERIENCE_CANDIES.items()},
    'ITEM_KEY_POWER_WEIGHT': 'STAT_HP',
    'ITEM_KEY_POWER_BRACER': 'STAT_ATK',
    'ITEM_KEY_POWER_BELT': 'STAT_DEF',
    'ITEM_KEY_POWER_ANKLET': 'STAT_SPEED',
    'ITEM_KEY_POWER_LENS': 'STAT_SPATK',
    'ITEM_KEY_POWER_BAND': 'STAT_SPDEF',
    **{
        f'ITEM_KEY_{name}_MINT': f'NATURE_{name}'
        for name in (
            'LONELY', 'ADAMANT', 'NAUGHTY', 'BRAVE', 'BOLD', 'IMPISH', 'LAX',
            'RELAXED', 'MODEST', 'MILD', 'RASH', 'QUIET', 'CALM', 'GENTLE',
            'CAREFUL', 'SASSY', 'TIMID', 'HASTY', 'JOLLY', 'NAIVE', 'SERIOUS',
        )
    },
    **{
        key: f'STAT_{key.removeprefix("ITEM_KEY_EV_RESET_")}'
        for key in EV_RESET_ITEMS
    },
}

HELD_BREEDING_ITEMS = BREEDING_ITEMS
PASSIVE_KEY_ITEMS = OVAL_CHARM_ITEMS

QOL_ASSET_BINDINGS = {
    **{
        key: ('gItemIcon_RareCandyTiles', 'gItemIcon_RareCandyPal')
        for key in EXPERIENCE_CANDIES
    },
    'ITEM_KEY_EV_RESET_HP': ('gItemIcon_PomegBerryTiles', 'gItemIcon_PomegBerryPal'),
    'ITEM_KEY_EV_RESET_ATK': ('gItemIcon_KelpsyBerryTiles', 'gItemIcon_KelpsyBerryPal'),
    'ITEM_KEY_EV_RESET_DEF': ('gItemIcon_QualotBerryTiles', 'gItemIcon_QualotBerryPal'),
    'ITEM_KEY_EV_RESET_SPEED': ('gItemIcon_TamatoBerryTiles', 'gItemIcon_TamatoBerryPal'),
    'ITEM_KEY_EV_RESET_SPATK': ('gItemIcon_HondewBerryTiles', 'gItemIcon_HondewBerryPal'),
    'ITEM_KEY_EV_RESET_SPDEF': ('gItemIcon_GrepaBerryTiles', 'gItemIcon_GrepaBerryPal'),
}

PINNED_SOURCE_HEADERS = (
    'vendor/upstream/CFRU-JP/include/constants/abilities.h',
    'vendor/upstream/DPE-JP/include/abilities.h',
    'vendor/upstream/CFRU-JP/include/constants/items.h',
    'vendor/upstream/CFRU-JP/include/constants/tmshms.h',
    'vendor/upstream/DPE-JP/include/items.h',
    'vendor/upstream/CFRU-JP/include/constants/pokemon.h',
    'vendor/upstream/DPE-JP/include/base_stats.h',
)

STABLE_ITEM_POCKETS = {
    'POCKET_ITEMS',
    'POCKET_KEY_ITEMS',
    'POCKET_POKE_BALLS',
    'POCKET_TM_CASE',
    'POCKET_BERRIES',
}


def int_or_none(value: str) -> int | None:
    value = value.strip()
    if value in NONE:
        return None
    return int(value, 0)


def _is_none(value: str | None) -> bool:
    return value is None or value.strip() in NONE


def _row_line(row: dict[str, str]) -> int:
    return int(row.get('__line__', '0'))


def _read_numeric_defines(
    root: Path,
    relative: str,
    prefix: str,
    stop_symbol: str | None,
    errors: list[str],
    label: str,
    *,
    parse_enums: bool = False,
) -> dict[str, int]:
    path = root / relative
    if not path.is_file():
        errors.append(f'{label}: pinned source missing: {relative}')
        return {}
    definitions: dict[str, int] = {}
    values: dict[int, str] = {}
    pattern = re.compile(
        rf'^\s*#define\s+({re.escape(prefix)}[A-Z0-9_]+)\s+'
        r'(0[xX][0-9A-Fa-f]+|[0-9]+)\b'
    )
    stop_pattern = (
        re.compile(rf'^\s*#define\s+{re.escape(stop_symbol)}\b')
        if stop_symbol
        else None
    )
    selected_lines: list[str] = []
    for line_no, line in enumerate(path.read_text(encoding='utf-8').splitlines(), 1):
        if stop_pattern and stop_pattern.match(line):
            break
        selected_lines.append(line)
        match = pattern.match(line)
        if not match:
            continue
        symbol, raw_value = match.groups()
        value = int(raw_value, 0)
        if symbol in definitions:
            errors.append(f'{label}:{line_no}: duplicate source symbol {symbol}')
            continue
        if value in values:
            errors.append(
                f'{label}:{line_no}: source ID {value} is shared by '
                f'{values[value]} and {symbol}'
            )
            continue
        definitions[symbol] = value
        values[value] = symbol
    if parse_enums:
        source = '\n'.join(selected_lines)
        clean = re.sub(r'/\*.*?\*/|//[^\n]*', '', source, flags=re.DOTALL)
        for enum_match in re.finditer(r'\benum\s*\{(.*?)\}\s*;', clean, re.DOTALL):
            current_value = -1
            for raw_entry in enum_match.group(1).split(','):
                entry = raw_entry.strip()
                if not entry:
                    continue
                match = re.fullmatch(
                    rf'({re.escape(prefix)}[A-Z0-9_]+)'
                    r'(?:\s*=\s*(0[xX][0-9A-Fa-f]+|[0-9]+))?',
                    entry,
                )
                if not match:
                    continue
                symbol, explicit = match.groups()
                current_value = int(explicit, 0) if explicit is not None else current_value + 1
                line_no = clean.count('\n', 0, enum_match.start()) + 1
                if symbol in definitions:
                    errors.append(f'{label}:{line_no}: duplicate source symbol {symbol}')
                    continue
                if current_value in values:
                    errors.append(
                        f'{label}:{line_no}: source ID {current_value} is shared by '
                        f'{values[current_value]} and {symbol}'
                    )
                    continue
                definitions[symbol] = current_value
                values[current_value] = symbol
    if not definitions:
        errors.append(f'{label}: no numeric {prefix} definitions found')
    return definitions


def _read_cfru_item_aliases(
    root: Path,
    canonical: dict[str, int],
    errors: list[str],
) -> dict[str, int]:
    """固定CFRU item namespace（canonical + source alias）を復元する。"""

    item_path = root / 'vendor/upstream/CFRU-JP/include/constants/items.h'
    tmhm_path = root / 'vendor/upstream/CFRU-JP/include/constants/tmshms.h'
    aliases = dict(canonical)

    # ITEMS_COUNTより前のsymbol-to-symbol alias（現固定sourceではEnigma Berry）も
    # public source symbolなのでcanonical IDへ解決する。
    symbolic_pattern = re.compile(
        r'^\s*#define\s+(ITEM_[A-Z0-9_]+)\s+(ITEM_[A-Z0-9_]+)\s*$'
    )
    for line_no, line in enumerate(
        item_path.read_text(encoding='utf-8').splitlines(), 1
    ):
        if re.match(r'^\s*#define\s+ITEMS_COUNT\b', line):
            break
        match = symbolic_pattern.match(line)
        if not match:
            continue
        symbol, target = match.groups()
        if target not in aliases:
            errors.append(
                f'CFRU item source:{line_no}: unresolved item alias {symbol} -> {target}'
            )
            continue
        if symbol in aliases and aliases[symbol] != aliases[target]:
            errors.append(f'CFRU item source:{line_no}: conflicting item alias {symbol}')
            continue
        aliases[symbol] = aliases[target]

    tmhm_pattern = re.compile(
        r'^\s*#define\s+(ITEM_[A-Z0-9_]+)\s+'
        r'(0[xX][0-9A-Fa-f]+|[0-9]+)\b'
    )
    tmhm: dict[str, int] = {}
    for line_no, line in enumerate(
        tmhm_path.read_text(encoding='utf-8').splitlines(), 1
    ):
        match = tmhm_pattern.match(line)
        if not match:
            continue
        symbol, raw_value = match.groups()
        if symbol in tmhm:
            errors.append(f'CFRU TM/HM source:{line_no}: duplicate source symbol {symbol}')
            continue
        tmhm[symbol] = int(raw_value, 0)
    if len(tmhm) != 58 or set(tmhm.values()) != set(range(289, 347)):
        errors.append(
            'cfru_tmhm_item: pinned source shape changed; expected 58 symbols '
            'covering IDs 289..346'
        )
    new_tmhm_symbols = set(tmhm) - set(aliases)
    if len(new_tmhm_symbols) != 52:
        errors.append(
            'cfru_tmhm_item: expected exactly 52 unique aliases outside '
            f'constants/items.h, got {len(new_tmhm_symbols)}'
        )
    for symbol, source_id in tmhm.items():
        if source_id not in canonical.values():
            errors.append(
                f'CFRU TM/HM source: {symbol} targets unknown item ID {source_id}'
            )
        if symbol in aliases and aliases[symbol] != source_id:
            errors.append(f'CFRU TM/HM source: conflicting item alias {symbol}')
            continue
        aliases[symbol] = source_id
    if len(aliases) != 827:
        errors.append(
            'cfru_item_aliases: pinned source shape changed; expected 827 '
            f'unique symbols, got {len(aliases)}'
        )
    return aliases


def _validate_pinned_source_shapes(
    root: Path, errors: list[str]
) -> dict[str, dict[str, int]]:
    present = [relative for relative in PINNED_SOURCE_HEADERS if (root / relative).is_file()]
    if not present:
        # Source-only CI clones intentionally omit vendor/upstream.  The generated
        # manifests remain independently verifiable below; only the exact lookup
        # against pinned headers is unavailable in this mode.
        return {}
    if len(present) != len(PINNED_SOURCE_HEADERS):
        missing = [relative for relative in PINNED_SOURCE_HEADERS if relative not in present]
        errors.append(
            'pinned source headers must be all present or all absent; missing '
            + ', '.join(missing)
        )
        return {}
    sources = {
        'cfru_ability': _read_numeric_defines(
            root,
            'vendor/upstream/CFRU-JP/include/constants/abilities.h',
            'ABILITY_',
            'ABILITIES_COUNT',
            errors,
            'CFRU ability source',
        ),
        'dpe_ability': _read_numeric_defines(
            root,
            'vendor/upstream/DPE-JP/include/abilities.h',
            'ABILITY_',
            None,
            errors,
            'DPE ability source',
        ),
        'cfru_item': _read_numeric_defines(
            root,
            'vendor/upstream/CFRU-JP/include/constants/items.h',
            'ITEM_',
            'ITEMS_COUNT',
            errors,
            'CFRU item source',
            parse_enums=True,
        ),
        'dpe_item': _read_numeric_defines(
            root,
            'vendor/upstream/DPE-JP/include/items.h',
            'ITEM_',
            'ITEMS_COUNT',
            errors,
            'DPE item source',
            parse_enums=True,
        ),
        'cfru_type': _read_numeric_defines(
            root,
            'vendor/upstream/CFRU-JP/include/constants/pokemon.h',
            'TYPE_',
            'NUMBER_OF_MON_TYPES',
            errors,
            'CFRU type source',
        ),
        'dpe_type': _read_numeric_defines(
            root,
            'vendor/upstream/DPE-JP/include/base_stats.h',
            'TYPE_',
            None,
            errors,
            'DPE type source',
        ),
    }
    sources['cfru_item_aliases'] = _read_cfru_item_aliases(
        root, sources['cfru_item'], errors
    )
    expected_shapes = {
        'cfru_ability': (311, set(range(311))),
        'dpe_ability': (311, set(range(311))),
        'cfru_item': (774, set(range(774))),
        'dpe_item': (774, set(range(774))),
        'cfru_type': (22, set(range(18)) | {19, 20, 23, 24}),
        'dpe_type': (22, set(range(18)) | {19, 20, 23, 24}),
    }
    for name, (expected_count, expected_values) in expected_shapes.items():
        definitions = sources[name]
        if definitions and len(definitions) != expected_count:
            errors.append(
                f'{name}: pinned source shape changed; expected {expected_count} symbols, '
                f'got {len(definitions)}'
            )
        if definitions and expected_values is not None and set(definitions.values()) != expected_values:
            errors.append(f'{name}: pinned source ID set changed')
    if sources['cfru_item'] and sources['dpe_item']:
        if sources['cfru_item'] != sources['dpe_item']:
            errors.append('CFRU/DPE item symbol-to-ID tables differ')
    return sources


def _validate_item_source_alias_resolution(
    rows: list[dict[str, str]], aliases: dict[str, int], errors: list[str]
) -> None:
    by_source_id: dict[int, dict[str, str]] = {}
    for row in rows:
        try:
            source_id = int_or_none(row['cfru_id'])
        except ValueError:
            continue
        if source_id is not None:
            by_source_id[source_id] = row
    unresolved = sorted(
        symbol for symbol, source_id in aliases.items() if source_id not in by_source_id
    )
    if unresolved:
        preview = ', '.join(unresolved[:5])
        suffix = '' if len(unresolved) <= 5 else f' (+{len(unresolved) - 5} more)'
        errors.append(
            'item_ids.csv: every CFRU item source symbol/alias must resolve '
            f'exactly once; unresolved {preview}{suffix}'
        )


def _validate_source_binding(
    filename: str,
    rows: list[dict[str, str]],
    symbol_column: str,
    id_column: str,
    expected: dict[str, int],
    errors: list[str],
    label: str,
) -> None:
    seen: dict[str, int] = {}
    for row in rows:
        line_no = _row_line(row)
        symbol = row[symbol_column].strip()
        if symbol in NONE:
            continue
        if symbol not in expected:
            errors.append(f'{filename}:{line_no}: unknown {label} symbol {symbol}')
            continue
        if symbol in seen:
            errors.append(
                f'{filename}:{line_no}: duplicate {label} symbol {symbol} '
                f'(first at line {seen[symbol]})'
            )
        else:
            seen[symbol] = line_no
        try:
            source_id = int_or_none(row[id_column])
        except ValueError:
            errors.append(
                f'{filename}:{line_no}: invalid {id_column} {row[id_column]!r}'
            )
            continue
        if source_id is None:
            errors.append(f'{filename}:{line_no}: {symbol} has no {id_column}')
        elif source_id != expected[symbol]:
            errors.append(
                f'{filename}:{line_no}: {symbol} source ID mismatch; '
                f'expected {expected[symbol]}, got {source_id}'
            )
    missing = sorted(set(expected) - set(seen))
    if missing:
        preview = ', '.join(missing[:5])
        suffix = '' if len(missing) <= 5 else f' (+{len(missing) - 5} more)'
        errors.append(
            f'{filename}: {label} symbols must resolve exactly once; missing {preview}{suffix}'
        )


def _require_bound_fields(
    filename: str,
    row: dict[str, str],
    fields: tuple[str, ...],
    errors: list[str],
) -> None:
    for field in fields:
        if _is_none(row.get(field)):
            errors.append(
                f'{filename}:{_row_line(row)}: {row.get("item_key", "row")} '
                f'requires {field}'
            )


def _validate_qol_items(rows: list[dict[str, str]], errors: list[str]) -> None:
    filename = 'item_ids.csv'
    by_key = {row['item_key']: row for row in rows}
    missing = sorted(QOL_REQUIRED_ITEMS - set(by_key))
    if missing:
        errors.append(
            f'{filename}: missing required QOL item keys: {", ".join(missing)}'
        )
        return

    metadata_fields = (
        'display_name',
        'description_key',
        'icon_key',
        'palette_key',
        'pocket',
        'price',
        'importance',
        'role',
        'supply_key',
        'runtime_binding',
    )
    for key in sorted(QOL_REQUIRED_ITEMS):
        row = by_key[key]
        _require_bound_fields(filename, row, metadata_fields, errors)
        if not _is_none(row.get('pocket')) and not row['pocket'].startswith('POCKET_'):
            errors.append(f'{filename}:{_row_line(row)}: invalid pocket {row["pocket"]}')
        for field in ('price', 'importance'):
            try:
                value = int(row[field], 0)
                if value < 0:
                    raise ValueError
            except ValueError:
                errors.append(
                    f'{filename}:{_row_line(row)}: invalid non-negative {field} '
                    f'{row[field]!r}'
                )
        expected_effect = QOL_FIELD_EFFECTS[key]
        if row['field_effect_key'] != expected_effect:
            errors.append(
                f'{filename}:{_row_line(row)}: {key} field effect must be '
                f'{expected_effect}'
            )
        expected_param = QOL_FIELD_PARAMS.get(key)
        if expected_param is not None and row['field_effect_param'] != expected_param:
            errors.append(
                f'{filename}:{_row_line(row)}: {key} field effect parameter must be '
                f'{expected_param}'
            )

    for key in sorted(set(EXPERIENCE_CANDIES) | EV_RESET_ITEMS):
        row = by_key[key]
        actual_type_contract = (
            row['item_type_key'],
            row['item_type_id'],
            row['item_type_explicit'],
            row['item_type_source'],
            row['source_mystery'],
            row['is_evolution_stone'],
            row['is_evolution_item'],
        )
        expected_type_contract = (
            'ITEM_TYPE_QOL_FIELD_ITEM', '0', '0', 'docs/QOL_POLICY.md', '0', '0', '0'
        )
        if actual_type_contract != expected_type_contract:
            errors.append(
                f'{filename}:{_row_line(row)}: {key} QOL item-type contract mismatch'
            )

    for key in sorted(HELD_BREEDING_ITEMS):
        row = by_key[key]
        if (row['consume_policy'], row['target_policy']) != ('NEVER', 'HELD'):
            errors.append(
                f'{filename}:{_row_line(row)}: {key} must use '
                'consume_policy=NEVER and target_policy=HELD'
            )
    for key in sorted(PASSIVE_KEY_ITEMS):
        row = by_key[key]
        if (row['consume_policy'], row['target_policy']) != (
            'NEVER',
            'PASSIVE_KEY_ITEM',
        ):
            errors.append(
                f'{filename}:{_row_line(row)}: {key} must use '
                'consume_policy=NEVER and target_policy=PASSIVE_KEY_ITEM'
            )
    for key, expected_assets in QOL_ASSET_BINDINGS.items():
        row = by_key[key]
        actual_assets = (row['icon_key'], row['palette_key'])
        if actual_assets != expected_assets:
            errors.append(
                f'{filename}:{_row_line(row)}: {key} asset binding must be '
                f'{expected_assets[0]}/{expected_assets[1]}'
            )

    for key, experience in EXPERIENCE_CANDIES.items():
        row = by_key[key]
        _require_bound_fields(
            filename,
            row,
            ('field_effect_key', 'field_effect_param', 'field_use_callback_key'),
            errors,
        )
        if row['classification'] != 'QOL_APPEND' or row['status'] != 'APPENDED':
            errors.append(f'{filename}:{_row_line(row)}: {key} must be a QOL append')
        if not _is_none(row['cfru_id']) or not _is_none(row['cfru_symbol']):
            errors.append(f'{filename}:{_row_line(row)}: {key} must not alias a CFRU item')
        try:
            actual_experience = int(row['field_effect_param'], 0)
        except ValueError:
            actual_experience = None
        if actual_experience != experience:
            errors.append(
                f'{filename}:{_row_line(row)}: {key} must grant exactly {experience} EXP'
            )
        if row['consume_policy'] != 'ON_EFFECT':
            errors.append(f'{filename}:{_row_line(row)}: {key} must use ON_EFFECT')
        if row['target_policy'] != 'PARTY_ONE':
            errors.append(f'{filename}:{_row_line(row)}: {key} must target PARTY_ONE')
        if row['runtime_binding'] != 'T06_RUNTIME_BIND_PENDING':
            errors.append(
                f'{filename}:{_row_line(row)}: {key} runtime binding must remain explicit'
            )

    for key in sorted(EV_RESET_ITEMS):
        row = by_key[key]
        _require_bound_fields(
            filename,
            row,
            ('field_effect_key', 'field_effect_param', 'field_use_callback_key'),
            errors,
        )
        if row['classification'] != 'QOL_APPEND' or row['status'] != 'APPENDED':
            errors.append(f'{filename}:{_row_line(row)}: {key} must be a QOL append')
        if not _is_none(row['cfru_id']) or not _is_none(row['cfru_symbol']):
            errors.append(f'{filename}:{_row_line(row)}: {key} must not alias an EV berry')
        if row['consume_policy'] != 'ON_EFFECT':
            errors.append(f'{filename}:{_row_line(row)}: {key} must use ON_EFFECT')
        if row['target_policy'] != 'PARTY_ONE':
            errors.append(f'{filename}:{_row_line(row)}: {key} must target PARTY_ONE')
        if row['runtime_binding'] != 'T06_RUNTIME_BIND_PENDING':
            errors.append(
                f'{filename}:{_row_line(row)}: {key} runtime binding must remain explicit'
            )

    for key in sorted(BREEDING_ITEMS):
        _require_bound_fields(filename, by_key[key], ('hold_effect_key',), errors)
    for key in sorted(MINT_ITEMS):
        _require_bound_fields(
            filename,
            by_key[key],
            ('field_effect_key', 'field_effect_param', 'field_use_callback_key'),
            errors,
        )
    for key in sorted(ABILITY_ITEMS):
        _require_bound_fields(
            filename,
            by_key[key],
            ('field_effect_key', 'field_use_callback_key'),
            errors,
        )
    # The pinned CFRU has Hyper Training script services but no bottle-cap item
    # callback.  T05 records the semantic effect and an explicit T06 service
    # adapter; requiring a fabricated callback here would hide that boundary.
    for key in sorted(HYPER_TRAINING_ITEMS):
        _require_bound_fields(filename, by_key[key], ('field_effect_key',), errors)
    for key in sorted(OVAL_CHARM_ITEMS):
        _require_bound_fields(filename, by_key[key], ('field_effect_key',), errors)


def _validate_types(rows: list[dict[str, str]], errors: list[str]) -> None:
    filename = 'type_ids.csv'
    by_key = {row['type_key']: row for row in rows}
    complete_fields = (
        'display_name',
        'icon_key',
        'icon_width',
        'icon_height',
        'icon_tile_offset',
        'icon_source',
        'color_key',
        'color_r',
        'color_g',
        'color_b',
        'color_bgr555',
        'color_source',
        'effectiveness_key',
    )
    added_type_contracts = (
        (
            'TYPE_KEY_FAIRY', 23, 24, 'FAIRY_CFRU_MATRIX',
            (32, 12, 224), (29, 17, 25, 26173),
        ),
        (
            'TYPE_KEY_STELLAR', 24, 25, 'STELLAR_CFRU_SPECIAL',
            (32, 12, 228), (31, 31, 31, 32767),
        ),
    )
    for (
        key,
        expected_id,
        expected_tera,
        expected_special_rule,
        expected_icon,
        expected_color,
    ) in added_type_contracts:
        row = by_key.get(key)
        if row is None:
            errors.append(f'{filename}: missing required added type {key}')
            continue
        try:
            canonical_id = int(row['id'], 0)
            tera_code = int(row['tera_input_code'], 0)
        except ValueError:
            canonical_id = tera_code = -1
        if (canonical_id, tera_code) != (expected_id, expected_tera):
            errors.append(
                f'{filename}:{_row_line(row)}: {key} must use ID {expected_id} '
                f'and tera input code {expected_tera}'
            )
        expected_symbol = key.removeprefix('TYPE_KEY_')
        expected_symbol = f'TYPE_{expected_symbol}'
        if row['cfru_symbol'] != expected_symbol or row['dpe_symbol'] != expected_symbol:
            errors.append(
                f'{filename}:{_row_line(row)}: {key} source symbol mismatch'
            )
        if row['classification'] != 'CFRU_APPEND' or row['status'] != 'APPENDED':
            errors.append(
                f'{filename}:{_row_line(row)}: {key} must use '
                'classification=CFRU_APPEND and status=APPENDED'
            )
        if row['special_rule'] != expected_special_rule:
            errors.append(
                f'{filename}:{_row_line(row)}: {key} special_rule must be '
                f'{expected_special_rule}'
            )
        for field in complete_fields:
            if _is_none(row[field]):
                errors.append(
                    f'{filename}:{_row_line(row)}: {key} requires complete {field}'
                )
        try:
            actual_icon = tuple(
                int(row[field], 0)
                for field in ('icon_width', 'icon_height', 'icon_tile_offset')
            )
            actual_color = tuple(
                int(row[field], 0)
                for field in ('color_r', 'color_g', 'color_b', 'color_bgr555')
            )
        except ValueError:
            actual_icon = ()
            actual_color = ()
        if actual_icon != expected_icon:
            errors.append(
                f'{filename}:{_row_line(row)}: {key} icon geometry must be '
                f'{expected_icon}'
            )
        if actual_color != expected_color:
            errors.append(
                f'{filename}:{_row_line(row)}: {key} color must be {expected_color}'
            )

    for row in rows:
        if row['classification'] in {'VEGA_CFRU_CANONICAL', 'CFRU_APPEND'}:
            for field in complete_fields:
                if _is_none(row[field]):
                    errors.append(
                        f'{filename}:{_row_line(row)}: public type {row["type_key"]} '
                        f'requires {field}'
                    )
            numeric_ranges = {
                'icon_width': (1, 255),
                'icon_height': (1, 255),
                'icon_tile_offset': (0, 0xFFFF),
                'color_r': (0, 31),
                'color_g': (0, 31),
                'color_b': (0, 31),
                'color_bgr555': (0, 0x7FFF),
            }
            for field, (minimum, maximum) in numeric_ranges.items():
                try:
                    value = int(row[field], 0)
                except ValueError:
                    errors.append(
                        f'{filename}:{_row_line(row)}: active type '
                        f'{row["type_key"]} has invalid {field}'
                    )
                    continue
                if not minimum <= value <= maximum:
                    errors.append(
                        f'{filename}:{_row_line(row)}: active type '
                        f'{row["type_key"]} {field} outside {minimum}..{maximum}'
                    )
            try:
                red = int(row['color_r'], 0)
                green = int(row['color_g'], 0)
                blue = int(row['color_b'], 0)
                packed = int(row['color_bgr555'], 0)
            except ValueError:
                continue
            expected_packed = red | (green << 5) | (blue << 10)
            if packed != expected_packed:
                errors.append(
                    f'{filename}:{_row_line(row)}: active type {row["type_key"]} '
                    'color_bgr555 does not match RGB components'
                )


def _validate_item_metadata(rows: list[dict[str, str]], errors: list[str]) -> None:
    filename = 'item_ids.csv'
    required_active_fields = (
        'display_name',
        'description_key',
        'icon_key',
        'palette_key',
        'pocket',
        'price',
        'importance',
        'role',
        'item_type_key',
        'item_type_id',
        'item_type_explicit',
        'item_type_source',
        'source_mystery',
        'is_evolution_stone',
        'is_evolution_item',
        'hold_effect_key',
        'hold_effect_param',
        'field_effect_key',
        'field_effect_param',
        'field_use_callback_key',
        'battle_usage',
        'battle_effect_key',
        'battle_effect_param',
        'battle_use_callback_key',
        'secondary_id',
        'ball_kind',
        'consume_policy',
        'target_policy',
        'supply_key',
        'runtime_binding',
    )
    pockets: set[str] = set()
    explicit_count = 0
    evolution_stone_count = 0
    evolution_item_count = 0
    held_evolution_count = 0
    item_type_ids: set[int] = set()
    balls: list[dict[str, str]] = []
    for row in rows:
        line_no = _row_line(row)
        if row['classification'] != 'CFRU_RESERVED':
            for field in required_active_fields:
                if _is_none(row[field]) and field in {
                    'display_name',
                    'description_key',
                    'icon_key',
                    'palette_key',
                    'pocket',
                    'price',
                    'importance',
                    'role',
                    'consume_policy',
                    'supply_key',
                    'runtime_binding',
                }:
                    errors.append(
                        f'{filename}:{line_no}: active item {row["item_key"]} '
                        f'requires {field}'
                    )
        for field in ('item_type_key', 'item_type_source'):
            if _is_none(row[field]):
                errors.append(
                    f'{filename}:{line_no}: item {row["item_key"]} requires {field}'
                )
        if not _is_none(row['item_type_key']) and not row['item_type_key'].startswith(
            'ITEM_TYPE_'
        ):
            errors.append(f'{filename}:{line_no}: invalid item_type_key {row["item_type_key"]}')
        if not _is_none(row['pocket']):
            pockets.add(row['pocket'])
            if row['pocket'] not in STABLE_ITEM_POCKETS:
                errors.append(f'{filename}:{line_no}: invalid stable pocket {row["pocket"]}')
        if row['classification'] != 'CFRU_RESERVED' and not row['supply_key'].startswith('SUPPLY_'):
            errors.append(
                f'{filename}:{line_no}: active item supply_key must start with SUPPLY_'
            )
        for field in (
            'price', 'importance', 'source_mystery', 'hold_effect_param',
            'battle_usage', 'secondary_id',
        ):
            if _is_none(row[field]):
                continue
            try:
                value = int(row[field], 0)
                if value < 0 or (field == 'source_mystery' and value > 0xFF):
                    raise ValueError
            except ValueError:
                errors.append(
                    f'{filename}:{line_no}: invalid non-negative {field} {row[field]!r}'
                )
        for field in ('item_type_explicit', 'is_evolution_stone', 'is_evolution_item'):
            if row[field] not in {'0', '1'}:
                errors.append(
                    f'{filename}:{line_no}: {field} must be the explicit boolean 0 or 1'
                )
        try:
            item_type_id = int(row['item_type_id'], 0)
        except ValueError:
            errors.append(
                f'{filename}:{line_no}: invalid item_type_id {row["item_type_id"]!r}'
            )
        else:
            item_type_ids.add(item_type_id)
            if not 0 <= item_type_id <= 62:
                errors.append(
                    f'{filename}:{line_no}: item_type_id outside pinned 0..62'
                )
        explicit = row['item_type_explicit'] == '1'
        is_stone = row['is_evolution_stone'] == '1'
        is_evolution_item = row['is_evolution_item'] == '1'
        explicit_count += explicit
        evolution_stone_count += is_stone
        evolution_item_count += is_evolution_item
        held_evolution_count += is_evolution_item and not _is_none(row['hold_effect_key'])
        if is_stone and (
            row['item_type_key'], row['item_type_id'], row['item_type_explicit']
        ) != ('ITEM_TYPE_EVOLUTION_STONE', '53', '1'):
            errors.append(f'{filename}:{line_no}: evolution-stone item-type contract mismatch')
        if is_evolution_item and (
            row['item_type_key'], row['item_type_id'], row['item_type_explicit']
        ) != ('ITEM_TYPE_EVOLUTION_ITEM', '54', '1'):
            errors.append(f'{filename}:{line_no}: evolution-item item-type contract mismatch')
        if is_stone and is_evolution_item:
            errors.append(f'{filename}:{line_no}: evolution flags must be disjoint')
        if not _is_none(row['ball_kind']):
            balls.append(row)
        if row['role'] == 'BALL' and _is_none(row['ball_kind']):
            errors.append(f'{filename}:{line_no}: ball item requires ball_kind')

    if pockets != STABLE_ITEM_POCKETS:
        errors.append(
            'item_ids.csv: stable pocket set must be exactly '
            + ', '.join(sorted(STABLE_ITEM_POCKETS))
        )
    if item_type_ids != set(range(63)):
        errors.append('item_ids.csv: item_type_id coverage must be exact 0..62')
    if explicit_count != 465:
        errors.append(
            f'item_ids.csv: expected 465 explicit item-type rows, got {explicit_count}'
        )
    if evolution_stone_count != 12:
        errors.append(
            f'item_ids.csv: expected 12 evolution stones, got {evolution_stone_count}'
        )
    if evolution_item_count != 40:
        errors.append(
            f'item_ids.csv: expected 40 evolution items, got {evolution_item_count}'
        )
    if held_evolution_count != 9:
        errors.append(
            f'item_ids.csv: expected 9 held+evolution multi-role items, '
            f'got {held_evolution_count}'
        )
    ball_kinds = [row['ball_kind'] for row in balls]
    if (
        len(balls) != 27
        or len(set(ball_kinds)) != 27
        or any(
            row['pocket'] != 'POCKET_POKE_BALLS' or row['role'] != 'BALL'
            for row in balls
        )
    ):
        errors.append(
            'item_ids.csv: ball_kind must resolve exactly 27 unique BALL rows '
            'in POCKET_POKE_BALLS'
        )

    by_key = {row['item_key']: row for row in rows}
    source_mystery_contract = {
        'ITEM_KEY_TM01': '1',
        'ITEM_KEY_HM01_CUT': '121',
        'ITEM_KEY_CHERI_BERRY': '1',
        'ITEM_KEY_LONELY_MINT': '1',
    }
    for key, expected in source_mystery_contract.items():
        row = by_key.get(key)
        if row is None:
            errors.append(f'item_ids.csv: missing source_mystery representative {key}')
        elif row['source_mystery'] != expected:
            errors.append(
                f'item_ids.csv:{_row_line(row)}: {key} source_mystery must be {expected}'
            )


def _validate_t05_manifests(
    root: Path,
    loaded_rows: dict[str, list[dict[str, str]]],
    range_rows: list[dict[str, str]],
    errors: list[str],
) -> None:
    if not any(loaded_rows.get(name) for name in T05_FILES):
        return
    if not all(loaded_rows.get(name) for name in T05_FILES):
        errors.append('T05 manifests must be generated as one complete ability/item/type set')
        return

    sources = _validate_pinned_source_shapes(root, errors)
    domain_ranges: dict[str, list[dict[str, Any]]] = {}
    for line_no, row in enumerate(range_rows, 2):
        if row['domain'] not in {'ability', 'item', 'type'}:
            continue
        try:
            start = int(row['start_id'], 0)
            end = int(row['end_id'], 0)
        except ValueError:
            continue
        domain_ranges.setdefault(row['domain'], []).append(
            {
                'start': start,
                'end': end,
                'owner': row['owner'],
                'status': row['status'],
                'line': line_no,
            }
        )

    exact_sizes = {'ability_ids.csv': 312, 'item_ids.csv': 999, 'type_ids.csv': 25}
    source_id_limits = {'ability_ids.csv': 310, 'item_ids.csv': 773, 'type_ids.csv': 24}
    domains = {
        'ability_ids.csv': 'ability',
        'item_ids.csv': 'item',
        'type_ids.csv': 'type',
    }
    key_prefixes = {
        'ability_ids.csv': 'ABILITY_KEY_',
        'item_ids.csv': 'ITEM_KEY_',
        'type_ids.csv': 'TYPE_KEY_',
    }
    source_symbol_fields = {
        'ability_ids.csv': {'cfru_symbol': 'ABILITY_', 'dpe_symbol': 'ABILITY_'},
        'item_ids.csv': {'cfru_symbol': 'ITEM_'},
        'type_ids.csv': {'cfru_symbol': 'TYPE_', 'dpe_symbol': 'TYPE_'},
    }
    for filename, domain in domains.items():
        rows = loaded_rows[filename]
        headers = EXPECTED[filename]
        source_symbols_seen: dict[str, dict[str, int]] = {
            field: {} for field in source_symbol_fields[filename]
        }
        for line_no, row in enumerate(rows, 2):
            row['__line__'] = str(line_no)
            for field in headers:
                if field != 'notes' and not row.get(field, '').strip():
                    errors.append(
                        f'{filename}:{line_no}: use explicit NONE for unbound {field}'
                    )
            if row['classification'] not in T05_ALLOWED_CLASSIFICATIONS[filename]:
                errors.append(
                    f'{filename}:{line_no}: invalid classification {row["classification"]}'
                )
            if row['status'] not in {'FROZEN', 'APPENDED', 'RESERVED'}:
                errors.append(f'{filename}:{line_no}: invalid status {row["status"]}')
            primary_key = row[PRIMARY_KEYS[filename]]
            if not primary_key.startswith(key_prefixes[filename]):
                errors.append(
                    f'{filename}:{line_no}: stable key must start with '
                    f'{key_prefixes[filename]}'
                )
            for field, prefix in source_symbol_fields[filename].items():
                symbol = row[field].strip()
                if symbol in NONE:
                    continue
                if not symbol.startswith(prefix):
                    errors.append(
                        f'{filename}:{line_no}: {field} must start with {prefix}'
                    )
                previous = source_symbols_seen[field].get(symbol)
                if previous is not None:
                    errors.append(
                        f'{filename}:{line_no}: duplicate {field} {symbol} '
                        f'(first at line {previous})'
                    )
                else:
                    source_symbols_seen[field][symbol] = line_no

        canonical_ids: list[int] = []
        for row in rows:
            try:
                canonical_ids.append(int(row['id'], 0))
            except ValueError:
                continue
        if canonical_ids != list(range(len(rows))):
            errors.append(
                f'{filename}: canonical IDs must be exact contiguous 0..{len(rows) - 1}'
            )
        expected_size = exact_sizes.get(filename)
        if expected_size is not None and len(rows) != expected_size:
            errors.append(f'{filename}: expected {expected_size} rows, got {len(rows)}')

        ranges = sorted(domain_ranges.get(domain, []), key=lambda entry: entry['start'])
        if not ranges:
            errors.append(f'id_ranges.csv: missing {domain} ranges')
        else:
            for entry in ranges:
                expected_range_status = 'FROZEN' if entry['owner'] == 'Vega' else 'ALLOCATED'
                if entry['status'] != expected_range_status:
                    errors.append(
                        f'id_ranges.csv:{entry["line"]}: {entry["owner"]} {domain} range '
                        f'must use {expected_range_status}'
                    )
            if ranges[0]['start'] != 0:
                errors.append(f'id_ranges.csv: {domain} ranges must start at 0')
            for left, right in zip(ranges, ranges[1:]):
                if right['start'] != left['end'] + 1:
                    errors.append(
                        f'id_ranges.csv:{right["line"]}: {domain} ranges must be contiguous'
                    )
            if ranges[-1]['end'] != len(rows) - 1:
                errors.append(
                    f'id_ranges.csv: {domain} ranges must end at canonical ID {len(rows) - 1}'
                )

        cfru_ids: dict[int, int] = {}
        for row in rows:
            line_no = _row_line(row)
            try:
                canonical_id = int(row['id'], 0)
            except ValueError:
                continue
            matching = [
                entry
                for entry in ranges
                if entry['start'] <= canonical_id <= entry['end']
            ]
            if len(matching) != 1:
                errors.append(
                    f'{filename}:{line_no}: canonical ID {canonical_id} must belong to one range'
                )
                continue
            owner = matching[0]['owner']
            try:
                vega_id = int_or_none(row['vega_id'])
            except ValueError:
                errors.append(f'{filename}:{line_no}: invalid vega_id {row["vega_id"]!r}')
                vega_id = None
            if owner == 'Vega':
                if vega_id != canonical_id or row['status'] != 'FROZEN':
                    errors.append(
                        f'{filename}:{line_no}: Vega range must preserve canonical/vega ID '
                        f'{canonical_id} as FROZEN'
                    )
                if not row['classification'].startswith('VEGA_'):
                    errors.append(f'{filename}:{line_no}: Vega range has non-Vega classification')
            elif owner == 'CFRU-JP':
                if vega_id is not None or row['status'] not in {'APPENDED', 'RESERVED'}:
                    errors.append(
                        f'{filename}:{line_no}: CFRU-JP range must be append/reserved without vega_id'
                    )
                if not row['classification'].startswith('CFRU_'):
                    errors.append(f'{filename}:{line_no}: CFRU-JP range has wrong classification')
            elif owner == 'QOL' and filename == 'item_ids.csv':
                if (
                    vega_id is not None
                    or row['classification'] != 'QOL_APPEND'
                    or row['status'] != 'APPENDED'
                ):
                    errors.append(f'{filename}:{line_no}: QOL range contract mismatch')
            else:
                errors.append(
                    f'{filename}:{line_no}: unsupported {domain} range owner {owner!r}'
                )

            classification = row['classification']
            if classification in {'CFRU_RESERVED', 'CFRU_SENTINEL'}:
                if row['status'] != 'RESERVED':
                    errors.append(
                        f'{filename}:{line_no}: {classification} must use RESERVED status'
                    )
            elif classification.endswith('_APPEND') and row['status'] != 'APPENDED':
                errors.append(f'{filename}:{line_no}: append classification/status mismatch')

            cfru_symbol_bound = not _is_none(row.get('cfru_symbol'))
            if classification in {'VEGA_CFRU_CANONICAL', 'CFRU_APPEND', 'CFRU_SENTINEL'}:
                if not cfru_symbol_bound:
                    errors.append(
                        f'{filename}:{line_no}: {classification} requires a CFRU symbol'
                    )
            elif classification in {'VEGA_EXCLUSIVE', 'QOL_APPEND'} and cfru_symbol_bound:
                errors.append(
                    f'{filename}:{line_no}: {classification} must not bind a CFRU symbol'
                )
            if filename in {'ability_ids.csv', 'type_ids.csv'}:
                dpe_symbol_bound = not _is_none(row.get('dpe_symbol'))
                if classification in {
                    'VEGA_CFRU_CANONICAL',
                    'CFRU_APPEND',
                    'CFRU_SENTINEL',
                } and not dpe_symbol_bound:
                    errors.append(
                        f'{filename}:{line_no}: {classification} requires a DPE symbol'
                    )
                if classification == 'VEGA_EXCLUSIVE' and dpe_symbol_bound:
                    errors.append(
                        f'{filename}:{line_no}: VEGA_EXCLUSIVE must not bind a DPE symbol'
                    )

            try:
                cfru_id = int_or_none(row['cfru_id'])
            except ValueError:
                errors.append(f'{filename}:{line_no}: invalid cfru_id {row["cfru_id"]!r}')
                continue
            if cfru_id is not None:
                if cfru_id in cfru_ids:
                    errors.append(
                        f'{filename}:{line_no}: duplicate cfru_id {cfru_id} '
                        f'(first at line {cfru_ids[cfru_id]})'
                    )
                cfru_ids[cfru_id] = line_no

        expected_cfru_ids = set(range(source_id_limits[filename] + 1))
        if set(cfru_ids) != expected_cfru_ids:
            errors.append(
                f'{filename}: cfru_id coverage must be exact 0..{source_id_limits[filename]}'
            )

    ability_rows = loaded_rows['ability_ids.csv']
    item_rows = loaded_rows['item_ids.csv']
    type_rows = loaded_rows['type_ids.csv']
    if sources:
        _validate_source_binding(
            'ability_ids.csv', ability_rows, 'cfru_symbol', 'cfru_id',
            sources['cfru_ability'], errors, 'CFRU ability',
        )
        _validate_source_binding(
            'ability_ids.csv', ability_rows, 'dpe_symbol', 'cfru_id',
            sources['dpe_ability'], errors, 'DPE ability',
        )
        _validate_source_binding(
            'item_ids.csv', item_rows, 'cfru_symbol', 'cfru_id',
            sources['cfru_item'], errors, 'CFRU item',
        )
        _validate_item_source_alias_resolution(
            item_rows, sources['cfru_item_aliases'], errors
        )
        _validate_source_binding(
            'type_ids.csv', type_rows, 'cfru_symbol', 'cfru_id',
            sources['cfru_type'], errors, 'CFRU type',
        )
        _validate_source_binding(
            'type_ids.csv', type_rows, 'dpe_symbol', 'cfru_id',
            sources['dpe_type'], errors, 'DPE type',
        )

    ability_ranges = sorted(
        (entry['owner'], entry['start'], entry['end'])
        for entry in domain_ranges.get('ability', [])
    )
    if ability_ranges != [('CFRU-JP', 78, 311), ('Vega', 0, 77)]:
        errors.append('id_ranges.csv: ability contract must freeze 0..77 and append 78..311')
    type_ranges = sorted(
        (entry['owner'], entry['start'], entry['end'])
        for entry in domain_ranges.get('type', [])
    )
    if type_ranges != [('CFRU-JP', 18, 24), ('Vega', 0, 17)]:
        errors.append('id_ranges.csv: type contract must freeze 0..17 and allocate 18..24')
    item_ranges = sorted(
        (entry['owner'], entry['start'], entry['end'])
        for entry in domain_ranges.get('item', [])
    )
    if item_ranges != [
        ('CFRU-JP', 375, 987),
        ('QOL', 988, 998),
        ('Vega', 0, 374),
    ]:
        errors.append(
            'id_ranges.csv: item contract must freeze 0..374, append CFRU '
            '375..987, and reserve QOL 988..998'
        )

    identity_rows = [
        row
        for row in item_rows[:375]
        if row['classification'] == 'VEGA_CFRU_CANONICAL'
    ]
    if len(identity_rows) != 161:
        errors.append(
            f'item_ids.csv: expected exactly 161 proven Vega/CFRU identities, '
            f'got {len(identity_rows)}'
        )

    by_item_key = {row['item_key']: row for row in item_rows}
    explicit_identities = (
        ('ITEM_KEY_DIRE_HIT', 74, 74, 'ITEM_DIRE_HIT'),
        ('ITEM_KEY_CHOICE_BAND', 186, 186, 'ITEM_CHOICE_BAND'),
        ('ITEM_KEY_GOLD_TEETH', 353, 348, 'ITEM_GOLD_TEETH'),
    )
    for key, canonical_id, source_id, source_symbol in explicit_identities:
        row = by_item_key.get(key)
        if row is None:
            errors.append(f'item_ids.csv: missing {key} explicit identity mapping')
            continue
        actual = (
            row['id'], row['vega_id'], row['cfru_id'], row['cfru_symbol'],
            row['classification'], row['status'],
        )
        expected = (
            str(canonical_id), str(canonical_id), str(source_id), source_symbol,
            'VEGA_CFRU_CANONICAL', 'FROZEN',
        )
        if actual != expected:
            errors.append(
                f'item_ids.csv:{_row_line(row)}: {key} must identity-map CFRU '
                f'{source_id} to frozen Vega {canonical_id}'
            )

    by_cfru_id = {
        int(row['cfru_id'], 0): row
        for row in item_rows
        if not _is_none(row['cfru_id'])
    }
    distinct_contracts = (
        (80, 'ITEM_POKE_DOLL'),
        (134, 'ITEM_CHESTO_BERRY'),
    )
    for source_id, source_symbol in distinct_contracts:
        vega_row = item_rows[source_id]
        source_row = by_cfru_id.get(source_id)
        if (
            vega_row['id'], vega_row['vega_id'], vega_row['cfru_id'],
            vega_row['cfru_symbol'], vega_row['classification'], vega_row['status'],
        ) != (
            str(source_id), str(source_id), 'NONE', 'NONE',
            'VEGA_EXCLUSIVE', 'FROZEN',
        ):
            errors.append(
                f'item_ids.csv:{_row_line(vega_row)}: Vega {source_id} must remain '
                'a frozen semantic-mismatch/distinct entity'
            )
        if source_row is None or (
            source_row['cfru_symbol'], source_row['classification'], source_row['status']
        ) != (source_symbol, 'CFRU_APPEND', 'APPENDED') or int(source_row['id'], 0) < 375:
            errors.append(
                f'item_ids.csv: CFRU {source_id} {source_symbol} must remain a '
                'distinct appended row'
            )

    _validate_qol_items(item_rows, errors)
    _validate_item_metadata(item_rows, errors)
    _validate_types(type_rows, errors)


def collect_errors(root: Path) -> list[str]:
    errors: list[str] = []
    id_seen: dict[str, dict[int, int]] = {}
    key_seen: dict[str, dict[str, int]] = {}
    loaded_rows: dict[str, list[dict[str, str]]] = {}
    for name, headers in EXPECTED.items():
        path = root / 'manifests' / name
        if not path.exists():
            errors.append(f'{name}: missing')
            continue
        with path.open(encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            rows = [dict(row) for row in reader]
            if reader.fieldnames != headers:
                # T05 used header-only placeholders before its generator existed.  Keep
                # those repositories valid, but never accept legacy columns once data
                # has been emitted because doing so would silently drop the new
                # semantic bindings.
                if (
                    name in T05_LEGACY_HEADERS
                    and reader.fieldnames == T05_LEGACY_HEADERS[name]
                    and not rows
                ):
                    loaded_rows[name] = []
                    continue
                errors.append(f'{name}: header mismatch {reader.fieldnames!r}')
                continue
            loaded_rows[name] = rows
            for line_no, row in enumerate(rows, 2):
                key_col = PRIMARY_KEYS.get(name)
                if key_col and row.get(key_col):
                    key = row[key_col].strip()
                    if not KEY_RE.match(key):
                        errors.append(f'{name}:{line_no}: invalid key {key}')
                    if key in key_seen.setdefault(name, {}):
                        errors.append(f'{name}:{line_no}: duplicate key {key}')
                    key_seen[name][key] = line_no
                if 'id' in headers and row.get('id','').strip():
                    try:
                        value = int_or_none(row['id'])
                    except ValueError:
                        errors.append(f'{name}:{line_no}: invalid id {row["id"]}')
                        continue
                    if value is not None:
                        if value in id_seen.setdefault(name, {}):
                            errors.append(f'{name}:{line_no}: duplicate id {value}')
                        id_seen[name][value] = line_no
                if name == 'kanto_encounters.csv' and row.get('level_min') and row.get('level_max'):
                    try:
                        if int(row['level_min']) > int(row['level_max']):
                            errors.append(f'{name}:{line_no}: min level > max level')
                    except ValueError:
                        errors.append(f'{name}:{line_no}: invalid level')
                if name == 'kanto_trainers.csv' and row.get('party_slot'):
                    try:
                        if not 1 <= int(row['party_slot']) <= 6:
                            errors.append(f'{name}:{line_no}: party_slot outside 1..6')
                    except ValueError:
                        errors.append(f'{name}:{line_no}: invalid party_slot')

    move_rows = loaded_rows.get('move_ids.csv', [])
    if move_rows:
        if len(move_rows) != 1063:
            errors.append(f'move_ids.csv: expected 1063 rows, got {len(move_rows)}')
        parsed_ids: list[int] = []
        cfru_symbols: list[str] = []
        allowed_classifications = {
            'VEGA_CFRU_CANONICAL',
            'VEGA_EXCLUSIVE_V3',
            'VEGA_COMPAT_DUPLICATE',
            'CFRU_APPEND',
        }
        for index, row in enumerate(move_rows):
            try:
                move_id = int(row['id'], 0)
            except ValueError:
                continue
            parsed_ids.append(move_id)
            frozen = index < 512
            expected_vega = str(index) if frozen else ''
            if row['vega_id'] != expected_vega:
                errors.append(
                    f'move_ids.csv:{index + 2}: Vega ID freeze/append contract mismatch'
                )
            expected_status = 'FROZEN' if frozen else 'APPENDED'
            if row['status'] != expected_status:
                errors.append(
                    f'move_ids.csv:{index + 2}: expected status {expected_status}'
                )
            if row['classification'] not in allowed_classifications:
                errors.append(
                    f'move_ids.csv:{index + 2}: invalid classification {row["classification"]}'
                )
            if frozen and row['classification'] == 'CFRU_APPEND':
                errors.append(f'move_ids.csv:{index + 2}: frozen row classified as append')
            if not frozen and row['classification'] != 'CFRU_APPEND':
                errors.append(f'move_ids.csv:{index + 2}: appended row has frozen classification')
            if row['cfru_symbol']:
                cfru_symbols.append(row['cfru_symbol'])
        if parsed_ids != list(range(1063)):
            errors.append('move_ids.csv: canonical IDs must be exact contiguous 0..1062')
        if len(cfru_symbols) != 992 or len(cfru_symbols) != len(set(cfru_symbols)):
            errors.append('move_ids.csv: CFRU symbols must resolve exactly once for all 992 moves')
        if len(move_rows) > 509:
            if (
                move_rows[470]['move_key'] != 'MOVE_KEY_SOUL_BITE'
                or move_rows[470]['display_name'] != 'ソウルバイト'
            ):
                errors.append('move_ids.csv: Vega ID 470 rename contract mismatch')
            if (
                move_rows[509]['move_key'] != 'MOVE_KEY_DARK_SNIPE'
                or move_rows[509]['display_name'] != 'ダークスナイプ'
            ):
                errors.append('move_ids.csv: Vega ID 509 rename contract mismatch')
        symbol_rows = {row['cfru_symbol']: row for row in move_rows if row['cfru_symbol']}
        for symbol in ('MOVE_JAWLOCK', 'MOVE_SNIPESHOT'):
            row = symbol_rows.get(symbol)
            if row is None or int(row['id'], 0) < 512:
                errors.append(f'move_ids.csv: {symbol} must remain a distinct appended move')

    range_rows = loaded_rows.get('id_ranges.csv', [])
    ranges_by_domain: dict[str, list[tuple[int, int, int]]] = {}
    for line_no, row in enumerate(range_rows, 2):
        try:
            start = int(row['start_id'], 0)
            end = int(row['end_id'], 0)
        except ValueError:
            errors.append(f'id_ranges.csv:{line_no}: invalid range endpoint')
            continue
        if start < 0 or end < start:
            errors.append(f'id_ranges.csv:{line_no}: invalid inclusive range')
            continue
        ranges_by_domain.setdefault(row['domain'], []).append((start, end, line_no))
    for domain, ranges in ranges_by_domain.items():
        ordered = sorted(ranges)
        for left, right in zip(ordered, ordered[1:]):
            if right[0] <= left[1]:
                errors.append(
                    f'id_ranges.csv:{right[2]}: {domain} range overlaps line {left[2]}'
                )
    _validate_t05_manifests(root, loaded_rows, range_rows, errors)
    return errors


def main() -> int:
    errors = collect_errors(repo_root())
    if errors:
        print('\n'.join(f'ERROR: {e}' for e in errors))
        return 1
    print('Manifest validation: OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
