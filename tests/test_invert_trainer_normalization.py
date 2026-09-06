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
