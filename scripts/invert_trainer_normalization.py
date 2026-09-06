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
            if (archive or kind9) and task.endswith(('TASK02_TOHOKU_EARLY', 'TASK04_TOHOKU_LATE')) and len(ordinary_decisions) == 1:
                row['decision'] = next(iter(ordinary_decisions))
            # Task03: 34 UNKNOWN行のfail-closed注記と4 general行の設計注記。
            # 復元CSV 93981 bytesは歴史的SHA 1e20d1da...f7c576と完全一致する。
            # 元decisionの識別だけを戻し、現在の実装の成功条件は変更しない。
            if archive and task.endswith('TASK03_TOHOKU_MID'):
                if change.get('original_battle_type') == 'UNKNOWN' and row['notes'].endswith('exact-ROM audit pending, no inference made'):
                    row['decision'] = 'FAIL_CLOSED_SOURCE_PRESERVED'
                elif row['notes'].startswith('role=TOHOKU_GENERAL_') and row['notes'].endswith('physical ownership preserved'):
                    row['decision'] = 'INDIVIDUAL_MIDGAME_DESIGN'
            continue
        row['trainer_id'] = change['original_trainer_id']
        original = sources[name].get(key)
        if original is None:
            raise ValueError('Trainer inverse source owner is missing')
        if name == 'trainer_encounters.csv':
            row['battle_type'] = change['original_battle_type']
            row['notes'] = row['notes'].removesuffix(' | original ROM command non-destructive ARCHIVE_REMATCH normalization').removesuffix(' | exact ROM audit: kind 9 EARLY_RIVAL/SINGLE')
            if archive:
                normalized_unlock = row['unlock_expression']
                for field in ENCOUNTER_OWNER_FIELDS:
                    row[field] = original[field]
                # 台帳は最終Task設計を正規化する直前の値。authoring原型で上書きしない。
                for field in ('physical_map_key', 'script_key', 'defeat_state_key'):
                    if 'original_' + field in change:
                        row[field] = change['original_' + field]
                consumer = change['archive_consumer_key']
                number = consumer.removeprefix('ARCHIVE_REMATCH_')
                if not (consumer.startswith('ARCHIVE_REMATCH_')
                        and len(number) == 4 and number.isascii() and number.isdigit()):
                    raise ValueError('Trainer inverse archive consumer identity differs')
                prefix = f'ARCHIVE_REMATCH_AVAILABLE && ARCHIVE_ENTRY_{number}_UNLOCKED && ('
                if not normalized_unlock.startswith(prefix) or not normalized_unlock.endswith(')'):
                    raise ValueError('Trainer inverse archive unlock contract differs')
                preserved = normalized_unlock[len(prefix):-1]
                # strip/空文字変換の情報が原型に残る場合は元のbyte表現を保持する。
                # Taskで変更された式は生成器のwrapperだけを外して戻す。
                if preserved != (original['unlock_expression'].strip() or 'TRUE'):
                    row['unlock_expression'] = preserved
                row['evidence'] = row['evidence'].split('; original command preserved; archive_consumer=')[0]
        else:
            row['evidence'] = row['evidence'].split('; original binding preserved; archive_consumer=')[0].removesuffix('; exact ROM kind=9 TRAINER_BATTLE_EARLY_RIVAL')
            if archive:
                for field in BINDING_OWNER_FIELDS:
                    row[field] = original[field]
        if archive or kind9:
            row['status'] = original['status']
    return result
