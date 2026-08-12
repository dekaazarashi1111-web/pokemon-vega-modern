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
            for line_no, row in enumerate(reader, 2):
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
    if errors:
        print('\n'.join(f'ERROR: {e}' for e in errors))
        return 1
    print('Manifest validation: OK')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
