"""Pinned owner-original and adversarial classification checks; no emulator."""
import copy
import io
from pathlib import Path
import sys
import unittest
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pr16_p05_supply_owner_evidence as e


class SupplyOwnerEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw=(ROOT/e.BASE/'original.zip').read_bytes()
        with zipfile.ZipFile(io.BytesIO(cls.raw)) as z:
            cls.report=e.load(z.read('supply-owner.json'))

    def test_exact_original_and_classification(self):
        findings,binding=e.validate_archive(self.raw)
        self.assertEqual(binding['source_count'],66)
        self.assertEqual(findings['formal_physical_gaps_closed'],0)
        self.assertEqual(findings['circus']['unknown_f0']['classification'],'NON_SCRIPT_BACK_SPRITE_TABLE_DATA')
        self.assertFalse(findings['circus']['unknown_f0']['native_opcode_length_required'])
        self.assertTrue(findings['ring']['only_match_is_removal'])
        self.assertEqual(findings['new_emulator_runs'],0)

    def test_outer_identity_not_just_plausible_json(self):
        with self.assertRaises(ValueError):e.validate_archive(self.raw+b'x')

    def test_no_native_claims_promoted(self):
        for field in ('physical_ring_accepted','physical_bp_accepted','physical_policy_accepted','physical_circus_admission_accepted','release_ready','decoder_changed','no_match_proves_absence'):
            report=copy.deepcopy(self.report);report[field]=True
            with self.subTest(field=field),self.assertRaises(ValueError):e.classify(report)

    def test_false_opcode_requires_exact_lineage(self):
        for field,value in [('address',0x0954ECC8),('roots',['map:12:7:object:0']),('stopped_at',0x0954ECD8)]:
            report=copy.deepcopy(self.report)
            node=next(n for n in report['selected_script_nodes'] if n['end_reason']=='unknown_opcode')
            node[field]=value
            with self.subTest(field=field),self.assertRaises(ValueError):e.classify(report)

    def test_sprite_tag_and_data_byte_are_not_guessed(self):
        report=copy.deepcopy(self.report)
        node=next(n for n in report['selected_script_nodes'] if n['end_reason']=='unknown_opcode')
        node['stop_window']='f1'+node['stop_window'][2:]
        with self.assertRaises(ValueError):e.classify(report)

    def test_header_shape_not_inferred_from_only_var403a(self):
        report=copy.deepcopy(self.report)
        m=next(m for m in report['map_headers'] if (m['group'],m['map'])==(12,7))
        m['pointers'][2]=0
        with self.assertRaises(ValueError):e.classify(report)

    def test_ring_remove_cannot_be_promoted_to_give(self):
        report=copy.deepcopy(self.report);report['ring_operand_candidates'][0]['opcode']=0x44
        with self.assertRaises(ValueError):e.classify(report)

    def test_p08_preserves_all_completion_and_candidate_fields(self):
        data=e.load((ROOT/e.P08).read_bytes());before=copy.deepcopy(data)
        after=e.update_p08(data)
        a=next(r for r in after['remaining_conditions'] if r['id']=='PHYSICAL_CIRCUS_ADMISSION')
        self.assertIsNone(a['success_evidence'])
        self.assertNotIn('complete', a)
        original=next(r for r in before['remaining_conditions'] if r['id']==a['id'])
        self.assertEqual({k:v for k,v in a.items() if k not in ('resume','supply_owner_evidence')},
                         {k:v for k,v in original.items() if k not in ('resume','supply_owner_evidence')})
        for key in before:
            if key not in ('remaining_conditions','p05_supply_owner_checkpoint'):
                self.assertEqual(after[key],before[key])
        for left,right in zip(before['remaining_conditions'],after['remaining_conditions']):
            if left['id']!='PHYSICAL_CIRCUS_ADMISSION':self.assertEqual(left,right)
        self.assertEqual(e.update_p08(copy.deepcopy(after)),after)


if __name__=='__main__':unittest.main()
