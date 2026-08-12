from __future__ import annotations

import csv
import re
from pathlib import Path

from common import repo_root

EXPECTED = {
    'id_ranges.csv': ['domain','owner','start_id','end_id','status','notes'],
    'move_ids.csv': ['move_key','id','vega_id','cfru_symbol','classification','display_name','status','notes'],
    'species_ids.csv': ['species_key','id','vega_id','dpe_symbol','classification','display_name','form_key','status','notes'],
    'ability_ids.csv': ['ability_key','id','vega_id','cfru_symbol','classification','display_name','status','notes'],
    'item_ids.csv': ['item_key','id','vega_id','cfru_symbol','classification','display_name','pocket','status','notes'],
    'type_ids.csv': ['type_key','id','vega_id','cfru_symbol','classification','display_name','status','notes'],
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


def int_or_none(value: str) -> int | None:
    value = value.strip()
    if not value:
        return None
    return int(value, 0)


def main() -> int:
    root = repo_root()
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
            if reader.fieldnames != headers:
                errors.append(f'{name}: header mismatch {reader.fieldnames!r}')
                continue
            loaded_rows[name] = []
            for line_no, row in enumerate(reader, 2):
                loaded_rows[name].append(dict(row))
                key_col = next((h for h in headers if h.endswith('_key') and h not in {'move1_key','move2_key','move3_key','move4_key','item_key','species_key','map_key','flag_key'}), None)
                if name.startswith('kanto_'):
                    key_col = {'kanto_maps.csv':'map_key','kanto_encounters.csv':None,'kanto_trainers.csv':None,'kanto_items.csv':'placement_key'}[name]
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
    if errors:
        print('\n'.join(f'ERROR: {e}' for e in errors))
        return 1
    print('Manifest validation: OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
