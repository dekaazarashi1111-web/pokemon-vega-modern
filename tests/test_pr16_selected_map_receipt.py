"""受領・停止点の人工境界試験。受入済み実ROM測定は呼ばない。"""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_selected_map_receipt as r
p = r.parent


def fixture():
    return dict(candidate=p.CANDIDATE, origin=dict(address=p.HIT, **p.HIT_ID),
        corrected_arm_layout=dict(p.LAYOUT), prior_descriptor_decoder_abi_mismatch=True,
        prior_measurement_rewritten=False, prior_zero_lz_search_replayed=False,
        descriptor_candidates=[dict(symbol='test_'+str(i), invalid_data_fields=[], bounded_distances=[]) for i in range(68)],
        valid_descriptor_candidates=68, actual_asset_reader_proven=False,
        formal_classification_changes=0, donor_safe_bytes=0, selected_lookup_profiles=[],
        actual_root=dict(literal_address=p.BASE+16, root=p.BASE+64, first_bank=p.BASE+128, first_header=p.BASE+256),
        actual_lookup=dict(group=0, number=0, conditional_actual_thumb_interpretation=True,
            natural_map_validity_proven=False, code=dict(start=p.BASE, end_exclusive=p.BASE+20), result=p.BASE+256,
            data_reads=[dict(address=p.BASE+n,size=4) for n in (16,64,128)]),
        map_probe=dict(root=dict(address=p.BASE+64,size=512), input_bounds=dict(groups=128,maps_per_group=128,total_probes=16384),
            matches=[], whole_map_inventory_claimed=False, all_rom_scan=False, actual_asset_reader_proven=False,
            donor_safe_bytes=0, unique_headers=1, layouts=[{}], descriptors=[{}]))


class ReceiptTests(unittest.TestCase):
    def setUp(self):self.proof=fixture()
    def reject(self):
        with self.assertRaises(ValueError):r.summarize(self.proof)
    def test_complete_zero_result_has_no_selected_owner(self):
        value=r.summarize(self.proof)
        self.assertFalse(value['owner_identified']);self.assertEqual(value['matching_candidates'],0)
        self.assertEqual(value['next_action_id'],r.NEXT)
    def test_not_global_map_absence(self):
        self.assertFalse(r.summarize(self.proof)['global_map_absence_proven'])
    def test_boolean_count_rejected(self):
        self.proof['valid_descriptor_candidates']=True;self.reject()
    def test_candidate_hash_rejected(self):
        self.proof['candidate']={};self.reject()
    def test_target_identity_rejected(self):
        self.proof['origin']={};self.reject()
    def test_swapped_abi_rejected(self):
        self.proof['corrected_arm_layout'].update(callback=20,attributes=16);self.reject()
    def test_old_rewrite_rejected(self):
        self.proof['prior_measurement_rewritten']=True;self.reject()
    def test_old_lz_replay_rejected(self):
        self.proof['prior_zero_lz_search_replayed']=True;self.reject()
    def test_duplicate_symbols_rejected(self):
        self.proof['descriptor_candidates'][1]['symbol']='test_0';self.reject()
    def test_count_mismatch_rejected(self):
        self.proof['descriptor_candidates'][0]['invalid_data_fields']=['tiles'];self.reject()
    def test_positive_old_candidate_needs_different_next(self):
        self.proof['descriptor_candidates'][0]['bounded_distances']=[{}];self.reject()
    def test_natural_map_claim_rejected(self):
        self.proof['actual_lookup']['natural_map_validity_proven']=True;self.reject()
    def test_missing_actual_root_read_rejected(self):
        self.proof['actual_lookup']['data_reads'].pop();self.reject()
    def test_code_extent_rejected(self):
        self.proof['actual_lookup']['code']['end_exclusive']=p.BASE+258;self.reject()
    def test_root_mismatch_rejected(self):
        self.proof['map_probe']['root']['address']+=4;self.reject()
    def test_probe_bounds_rejected(self):
        self.proof['map_probe']['input_bounds']['groups']=129;self.reject()
    def test_positive_map_match_needs_different_next(self):
        self.proof['map_probe']['matches']=[{}];self.reject()
    def test_selected_profile_contradicts_zero(self):
        self.proof['selected_lookup_profiles']=[{}];self.reject()
    def test_formal_count_not_promoted(self):
        self.proof['formal_classification_changes']=1;self.reject()
    def test_boolean_zero_rejected(self):
        self.proof['donor_safe_bytes']=False;self.reject()
    def test_reader_claim_rejected(self):
        self.proof['actual_asset_reader_proven']=True;self.reject()
    def test_full_map_claim_rejected(self):
        self.proof['map_probe']['whole_map_inventory_claimed']=True;self.reject()
    def test_safe_capacity_rejected(self):
        self.proof['map_probe']['donor_safe_bytes']=4;self.reject()
    def test_deterministic_read_only(self):
        before=copy.deepcopy(self.proof)
        self.assertEqual(r.summarize(self.proof),r.summarize(self.proof));self.assertEqual(self.proof,before)


if __name__=='__main__':unittest.main()
