import copy
import unittest
from scripts.invert_trainer_normalization import inverse_rows, read_pinned_sources, BINDING_OWNER_FIELDS


class TrainerNormalizationInverseTests(unittest.TestCase):
    def test_unpinned_original_bytes_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'pinned'):
            read_pinned_sources({'trainer_encounters.csv': b'encounter_key\nwrong\n'})

    def test_binding_owner_is_restored_without_changing_authored_content(self):
        original = {key: 'source_' + key for key in BINDING_OWNER_FIELDS}
        original.update(status='PENDING_EXACT_AUDIT')
        row = {key: 'normalized_' + key for key in BINDING_OWNER_FIELDS}
        row.update(encounter_key='E1', trainer_id='1000', status='READY',
                   authored='individual-design', evidence='original evidence; original binding preserved; archive_consumer=A1')
        before = copy.deepcopy(row)
        ledger = {'E1': {'archive_consumer_key': 'A1', 'normalization_action': 'ARCHIVE', 'original_trainer_id': '12'}}
        got = inverse_rows('trainer_physical_bindings.csv', 'TASK02_TOHOKU_EARLY', [row], ledger, {'trainer_physical_bindings.csv': {'E1': original}})[0]
        self.assertEqual(row, before)
        for key, value in original.items():
            self.assertEqual(got[key], value)
        self.assertEqual(got['authored'], 'individual-design')
        self.assertEqual(got['trainer_id'], '12')
        self.assertEqual(got['evidence'], 'original evidence')

    def test_missing_original_owner_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'owner is missing'):
            inverse_rows('trainer_encounters.csv', 'TASK02_TOHOKU_EARLY', [{'encounter_key': 'E1'}],
                         {'E1': {'archive_consumer_key': 'A1', 'normalization_action': 'ARCHIVE', 'original_trainer_id': '12'}},
                         {'trainer_encounters.csv': {}})

    def test_ambiguous_coverage_decisions_are_not_inferred(self):
        rows = [{'encounter_key': 'E1', 'decision': 'ARCHIVE', 'notes': 'designed; archive_consumer=A1'},
                {'encounter_key': 'E2', 'decision': 'BOSS', 'notes': 'boss'},
                {'encounter_key': 'E3', 'decision': 'DOUBLE', 'notes': 'double'}]
        ledger = {key: {'archive_consumer_key': 'A1' if key == 'E1' else '', 'normalization_action': ''} for key in ('E1', 'E2', 'E3')}
        got = inverse_rows('coverage.csv', 'TASK03_TOHOKU_MID', rows, ledger, {})
        self.assertEqual(got[0]['decision'], 'ARCHIVE')
        self.assertEqual(got[0]['notes'], 'designed')
        self.assertEqual(rows[0]['notes'], 'designed; archive_consumer=A1')


    def test_archive_encounter_preserves_task_ledger_and_unlock(self):
        from scripts.invert_trainer_normalization import ENCOUNTER_OWNER_FIELDS
        original = {field: 'authoring_' + field for field in ENCOUNTER_OWNER_FIELDS}
        original.update(status='PENDING_EXACT_AUDIT', unlock_expression='OLD_UNLOCK')
        row = dict(original)
        row.update(encounter_key='E1', trainer_id='1000', battle_type='NORMALIZED',
                   notes='Task design | original ROM command non-destructive ARCHIVE_REMATCH normalization',
                   evidence='Task evidence; original command preserved; archive_consumer=ARCHIVE_REMATCH_0001',
                   unlock_expression='ARCHIVE_REMATCH_AVAILABLE && ARCHIVE_ENTRY_0001_UNLOCKED && (TASK_UNLOCK && (BADGE_2 || BADGE_3))')
        change = {'archive_consumer_key': 'ARCHIVE_REMATCH_0001',
                  'normalization_action': 'MOVE_TO_ARCHIVE_REMATCH:OWNER',
                  'original_trainer_id': '12', 'original_battle_type': 'UNKNOWN',
                  'original_physical_map_key': 'TASK_MAP',
                  'original_script_key': 'TASK_SCRIPT',
                  'original_defeat_state_key': 'TASK_DEFEATED'}
        before = copy.deepcopy(row)
        got = inverse_rows('trainer_encounters.csv', 'TASK03_TOHOKU_MID', [row],
                           {'E1': change}, {'trainer_encounters.csv': {'E1': original}})[0]
        self.assertEqual(row, before)
        self.assertEqual(got['physical_map_key'], 'TASK_MAP')
        self.assertEqual(got['script_key'], 'TASK_SCRIPT')
        self.assertEqual(got['defeat_state_key'], 'TASK_DEFEATED')
        self.assertEqual(got['unlock_expression'], 'TASK_UNLOCK && (BADGE_2 || BADGE_3)')
        self.assertEqual(got['notes'], 'Task design')
        self.assertEqual(got['evidence'], 'Task evidence')
        self.assertEqual(got['battle_type'], 'UNKNOWN')
        self.assertEqual(got['trainer_id'], '12')
        self.assertEqual(got['status'], 'PENDING_EXACT_AUDIT')
        for bad in ('ARCHIVE_REMATCH_AVAILABLE && ARCHIVE_ENTRY_0002_UNLOCKED && (TASK_UNLOCK)',
                    'TASK_UNLOCK', 'ARCHIVE_REMATCH_AVAILABLE && ARCHIVE_ENTRY_0001_UNLOCKED && (TASK_UNLOCK'):
            with self.subTest(kind='invalid-wrapper'):
                changed = dict(row, unlock_expression=bad)
                with self.assertRaisesRegex(ValueError, 'unlock contract'):
                    inverse_rows('trainer_encounters.csv', 'TASK03_TOHOKU_MID', [changed],
                                 {'E1': change}, {'trainer_encounters.csv': {'E1': original}})

    def test_archive_inverse_preserves_original_unlock_spelling_when_provable(self):
        from scripts.invert_trainer_normalization import ENCOUNTER_OWNER_FIELDS
        for original_unlock in ('', '  FLAG_BASE  ', 'TRUE'):
            original = {field: 'authoring_' + field for field in ENCOUNTER_OWNER_FIELDS}
            original.update(status='PENDING', unlock_expression=original_unlock)
            row = dict(original, encounter_key='E1', notes='design', evidence='source',
                       unlock_expression='ARCHIVE_REMATCH_AVAILABLE && ARCHIVE_ENTRY_0007_UNLOCKED && (' + (original_unlock.strip() or 'TRUE') + ')')
            change = {'archive_consumer_key': 'ARCHIVE_REMATCH_0007',
                      'normalization_action': 'ARCHIVE', 'original_trainer_id': '12',
                      'original_battle_type': 'UNKNOWN'}
            got = inverse_rows('trainer_encounters.csv', 'TASK03_TOHOKU_MID', [row],
                               {'E1': change}, {'trainer_encounters.csv': {'E1': original}})[0]
            self.assertEqual(got['unlock_expression'], original_unlock)
