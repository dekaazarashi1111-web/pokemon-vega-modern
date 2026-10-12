"""legacy seen三mirrorの物理境界を回帰検査。破損を許可しない。"""
import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from copy import deepcopy
import pr16_story_dex_guard as d
from pr16_story_milestones import DiagnosticStop
class DexGuardTests(unittest.TestCase):
    def test_first_bit(self):self.assertEqual(d.addresses(1)['writes'][0],dict(mirror='save2',offset=0x5C,mask=1))
    def test_stock_last_species(self):self.assertTrue(d.addresses(386)['physical_in_bounds']);self.assertTrue(d.addresses(386)['legacy_species_number'])
    def test_padding_is_not_species_acceptance(self):self.assertTrue(d.addresses(416)['physical_in_bounds']);self.assertFalse(d.addresses(416)['legacy_species_number'])
    def test_first_out_of_bounds(self):self.assertFalse(d.addresses(417)['physical_in_bounds']);self.assertEqual(d.addresses(417)['writes'][0]['offset'],0x90)
    def test_national749_rematch27(self):r=d.addresses(749);self.assertFalse(r['physical_in_bounds']);self.assertEqual(r['bit'],16);self.assertEqual(r['writes'][1]['offset']-0x63A,27)
    def test_national963_rematch54(self):r=d.addresses(963);self.assertFalse(r['physical_in_bounds']);self.assertEqual(r['bit'],4);self.assertEqual(r['writes'][1]['offset']-0x63A,54)
    def test_national963_other_aliases(self):r=d.addresses(963);self.assertEqual([x['offset']for x in r['writes']],[0xD4,0x670,0x3A90])
    def test_national749_other_aliases(self):r=d.addresses(749);self.assertEqual([x['offset']for x in r['writes']],[0xB9,0x655,0x3A75])
    def test_last_unwrapped_index(self):self.assertEqual(d.addresses(2048)['byte_index'],255)
    def test_wrapping_index_rejected(self):
        with self.assertRaises(DiagnosticStop):d.addresses(2049)
    def test_invalid_zero(self):
        with self.assertRaises(DiagnosticStop):d.addresses(0)
    def test_invalid_type(self):
        with self.assertRaises(DiagnosticStop):d.addresses(True)
    def test_mismatched_actual_party(self):
        live=dict(route=dict(trainer_id=131),enemy_mons=[dict(species=481,level=13)])
        audit=dict(trainers=[dict(trainer_id=131,party=[dict(species=1537,level=15,**d.addresses(963))])])
        with self.assertRaises(DiagnosticStop):d.require_safe_party(live,audit)
    def test_unsafe_actual_party_stops_before_buttons(self):
        live=dict(route=dict(trainer_id=131),enemy_mons=[dict(species=1537,level=15)])
        audit=dict(trainers=[dict(trainer_id=131,party=[dict(species=1537,level=15,**d.addresses(963))])])
        with self.assertRaises(DiagnosticStop)as e:d.require_safe_party(live,audit)
        self.assertEqual(e.exception.report['reason'],'unsafe_legacy_dex_seen_target');self.assertTrue(e.exception.report['detail']['no_battle_input_sent'])
if __name__=='__main__':unittest.main()
