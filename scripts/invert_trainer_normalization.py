"""元の正規化処理を逆適用する。採用条件は別段の歴史的size+SHA完全一致。"""
from __future__ import annotations
import csv
import hashlib
import io
from collections.abc import Mapping

# Private Releaseのauthoring source/v5/data。本文はGitへ追加しない。
# 読取専用監査34023077870の内側manifestと各member SHAで独立照合した。
SOURCE_INPUTS = {
    'trainer_encounters.csv': (1040651, '87a3e58893a5f7f47e05427ff8b9b5042ef9972f10f90f698c85fdacb386767b'),
    'trainer_physical_bindings.csv': (577737, '52304087d5d883fa5c5109128ce063ea614adb0cf5450a9f7f17eac10a6101f0'),
}
ENCOUNTER_OWNER_FIELDS = tuple('physical_map_key group_id map_id root_kind root_index local_id x y elevation graphics_id movement_type sight_range script_key initial_or_rematch rematch_tier mandatory avoidable_path_evidence unlock_expression defeat_state_key'.split())
BINDING_OWNER_FIELDS = tuple('map_event_owner object_or_script_address rematch_state_key defeat_flag_key serializer_owner'.split())


def read_pinned_sources(raw_tables: Mapping[str, bytes]) -> dict[str, dict[str, dict[str, str]]]:
    result = {}
    for name, raw in raw_tables.items():
        if name not in SOURCE_INPUTS or (len(raw), hashlib.sha256(raw).hexdigest()) != SOURCE_INPUTS[name]:
            raise ValueError('Trainer inverse source is not the pinned authoring member')
        rows = list(csv.DictReader(io.StringIO(raw.decode('utf-8-sig'), newline='')))
        indexed = {row['encounter_key']: row for row in rows}
        if len(indexed) != len(rows) or '' in indexed:
            raise ValueError('Trainer inverse source has duplicate or empty keys')
        result[name] = indexed
    return result


def inverse_rows(name: str, task: str, records: list[dict[str, str]],
                 ledger: Mapping[str, Mapping[str, str]],
                 sources: Mapping[str, Mapping[str, Mapping[str, str]]]) -> list[dict[str, str]]:
    """_normalizeのowner退避/注記だけを戻す。party/AI/難易度/台詞の設計変更は保持。"""
    result = [dict(row) for row in records]
    if name not in {'coverage.csv', *SOURCE_INPUTS}:
        return result
    if name in SOURCE_INPUTS and name not in sources:
        return result
    ordinary_decisions = {
        row['decision'] for row in result
        if name == 'coverage.csv' and not ledger[row['encounter_key']]['archive_consumer_key']
        and 'KIND9' not in ledger[row['encounter_key']]['normalization_action']
    }
    for row in result:
        key = row['encounter_key']
        change = ledger[key]
        archive = bool(change['archive_consumer_key'])
        kind9 = 'KIND9' in change['normalization_action']
        if name == 'coverage.csv':
            if archive:
                row['notes'] = row['notes'].split('; archive_consumer=')[0]
            # Task02/04は無加工の同task全行が同一decision。最終hashも別途要求する。
            # 個別decisionのTask03は復元根拠不足なのでここでは変更しない。
            if (archive or kind9) and task.endswith(('TASK02_TOHOKU_EARLY', 'TASK04_TOHOKU_LATE')) and len(ordinary_decisions) == 1:
                row['decision'] = next(iter(ordinary_decisions))
            continue
        row['trainer_id'] = change['original_trainer_id']
        original = sources[name].get(key)
        if original is None:
            raise ValueError('Trainer inverse source owner is missing')
        if name == 'trainer_encounters.csv':
            row['battle_type'] = change['original_battle_type']
            row['notes'] = row['notes'].removesuffix(' | original ROM command non-destructive ARCHIVE_REMATCH normalization').removesuffix(' | exact ROM audit: kind 9 EARLY_RIVAL/SINGLE')
            if archive:
                for field in ENCOUNTER_OWNER_FIELDS:
                    row[field] = original[field]
                row['evidence'] = row['evidence'].split('; original command preserved; archive_consumer=')[0]
        else:
            row['evidence'] = row['evidence'].split('; original binding preserved; archive_consumer=')[0].removesuffix('; exact ROM kind=9 TRAINER_BATTLE_EARLY_RIVAL')
            if archive:
                for field in BINDING_OWNER_FIELDS:
                    row[field] = original[field]
        if archive or kind9:
            row['status'] = original['status']
    return result
