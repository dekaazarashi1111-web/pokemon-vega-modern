import unittest
from tools.stage61_entry_reference_identity import reference_key


class EntryReferenceIdentityTests(unittest.TestCase):
    def test_vega_provenance_is_not_replaced_with_clean_map_name(self):
        references = {(0, 2): 'RecordCorner'}
        self.assertEqual(reference_key(group=0, number=2, physical_key='VEGA_STOCK:000/002',
            declared_reference='RecordCorner', legacy_coordinates=references), 'RecordCorner')
        with self.assertRaises(ValueError):
            reference_key(group=0, number=2, physical_key='RecordCorner',
                declared_reference='RecordCorner', legacy_coordinates=references)

    def test_swapped_vega_coordinate_is_rejected(self):
        with self.assertRaises(ValueError):
            reference_key(group=0, number=2, physical_key='VEGA_STOCK:000/003',
                declared_reference='RecordCorner', legacy_coordinates={(0, 2): 'RecordCorner'})

    def test_legacy_reference_drift_is_rejected(self):
        with self.assertRaises(ValueError):
            reference_key(group=0, number=2, physical_key='VEGA_STOCK:000/002',
                declared_reference='OtherMap', legacy_coordinates={(0, 2): 'RecordCorner'})

    def test_imported_canonical_name_remains_exact(self):
        name = 'KANTO_DUNGEON_POKEMON_LEAGUE_LORELEIS_ROOM'
        self.assertEqual(reference_key(group=97, number=75, physical_key=name,
            declared_reference=name, legacy_coordinates={(97, 75): name}), name)
        with self.assertRaises(ValueError):
            reference_key(group=97, number=75, physical_key='VEGA_STOCK:097/075',
                declared_reference=name, legacy_coordinates={(97, 75): name})
