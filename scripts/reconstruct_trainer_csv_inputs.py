"""正規化済みtracked CSVから元の入力CSVを再構成し、元manifestのhashで採否を決める。"""
from __future__ import annotations
import csv
import hashlib
import io
import json
from pathlib import Path

CONTENT = 'content/trainer_changekit_final'
EXTRA_FIELDS = {'original_trainer_id', 'runtime_trainer_id', 'trainer_id_allocation_reason'}
DIALOGUE_ORDER = ('INTRO', 'DEFEAT', 'POST_BATTLE', 'REMATCH_INTRO', 'NOT_ENOUGH_PARTY_FOR_DOUBLE')
PHASES = ('TOHOKU_PROLOGUE_PRE_GYM1', *(f'TOHOKU_BADGE{i}_TO_{i+1}' for i in range(1, 8)),
          'TOHOKU_LEAGUE_APPROACH', 'TOHOKU_INITIAL_LEAGUE', 'TOHOKU_POSTGAME')


def reconstruct(root: Path, rows: list[dict]) -> dict[str, bytes]:
    """値を推測・上書きせず、元SHAに一致した再構成だけを返す。"""
    content = root / CONTENT
    def read(name):
        with (content / name).open(encoding='utf-8', newline='') as stream:
            reader = csv.DictReader(stream)
            return list(reader.fieldnames or []), list(reader)
    if not (content / 'coverage.csv').is_file():
        return {}
    coverage = read('coverage.csv')[1]
    keys = {}
    for row in coverage:
        keys.setdefault('VEGA_TRAINER_CHANGEKIT_' + row['task_id'], set()).add(row['encounter_key'])
    parties = {row['party_key']: row['encounter_key'] for row in read('trainer_parties.csv')[1]}
    encounters = {row['encounter_key']: row for row in read('trainer_encounters.csv')[1]}
    ledger = {row['encounter_key']: row for row in read('normalization_ledger.csv')[1]}
    result = {}
    for expected in rows:
        relative = Path(expected['path'])
        if relative.suffix != '.csv' or not (content / relative.name).is_file():
            continue
        fields, records = read(relative.name)
        task = relative.parts[0]
        if task in keys and 'data' in relative.parts:
            records = [dict(row) for row in records
                       if row.get('encounter_key', parties.get(row.get('party_key'))) in keys[task]]
            fields = [field for field in fields if field not in EXTRA_FIELDS]
            if relative.name in {'trainer_encounters.csv', 'trainer_physical_bindings.csv'}:
                for row in records:
                    row['trainer_id'] = ledger[row['encounter_key']]['original_trainer_id']
            def order(row):
                key = row.get('encounter_key', parties.get(row.get('party_key')))
                phase = encounters[key]['story_phase']
                if task.endswith('TASK02_TOHOKU_EARLY'):
                    prefix = (phase, key)
                elif task.endswith(('TASK03_TOHOKU_MID', 'TASK04_TOHOKU_LATE')) \
                        and not (task.endswith('TASK04_TOHOKU_LATE') and relative.name == 'trainer_dialogue.csv'):
                    prefix = (PHASES.index(phase), key)
                else:
                    prefix = (key,)
                state = row.get('state_key', '')
                # Task06の入力はstate_key辞書順。他のkitは物語文の入力順。
                state_order = state if task.endswith('TASK06_KANTO') else (
                    DIALOGUE_ORDER.index(state) if state in DIALOGUE_ORDER else len(DIALOGUE_ORDER))
                return (*prefix, int(row.get('slot', '0')), state_order)
            records.sort(key=order)
        stream = io.StringIO(newline='')
        writer = csv.DictWriter(stream, fields, lineterminator='\n', extrasaction='ignore')
        writer.writeheader()
        writer.writerows(records)
        raw = stream.getvalue().encode('utf-8')
        if len(raw) == expected['size'] and hashlib.sha256(raw).hexdigest() == expected['sha256']:
            result[expected['path']] = raw
    return result
