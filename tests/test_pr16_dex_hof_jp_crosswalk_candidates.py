"""候補addressをJP extent/実ROM型へ誤昇格しない拒否試験。"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('crosswalk', ROOT/'scripts/pr16_dex_hof_jp_crosswalk_candidates.py')
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)


class CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = (ROOT/m.CONTRACT).read_bytes(); cls.fixed = m.contract(cls.raw)
        cls.sources = m.sources_from_cache(cls.fixed, ROOT/'.local/jp-crosswalk-sources')

    def setUp(self):
        self.value = copy.deepcopy(self.fixed)

    def invalid(self):
        with self.assertRaises((ValueError, KeyError, IndexError)):
            m.validate(self.value, self.sources)

    def test_real_complete_fixed_sources(self):
        result = m.validate(self.value, self.sources)
        self.assertEqual((result['candidate_pairs'], result['rejected_conflicted_pairs'], result['newly_classified']), (2, 1, 0))

    def test_contract_any_byte_change(self):
        with self.assertRaises(ValueError):m.contract(self.raw+b'\n')

    def test_each_source_change_rejected(self):
        for key in self.sources:
            changed = dict(self.sources); changed[key] += b'\n'
            with self.subTest(key=key), self.assertRaises(ValueError):m.validate(self.value, changed)

    def test_source_set_missing(self):
        changed=dict(self.sources);changed.pop(next(iter(changed)))
        with self.assertRaises(ValueError):m.validate(self.value,changed)

    def test_audit_address_changed(self):
        self.value['mapped_symbols'][0]['jp_address']='0x08008B4A';self.invalid()

    def test_audit_method_changed(self):
        self.value['mapped_symbols'][0]['method']='bounded_translated_string_sequence';self.invalid()

    def test_reference_size_not_jp_extent(self):
        self.value['mapped_symbols'][0]['jp_extent_verified']=True;self.invalid()

    def test_rank_not_probability(self):
        self.value['mapped_symbols'][0]['score_is_probability']=True;self.invalid()

    def test_duplicate_mapping_rejected(self):
        self.value['mapped_symbols'][-1]=copy.deepcopy(self.value['mapped_symbols'][0]);self.invalid()

    def test_neighbor_distance_not_extent(self):
        self.value['candidates'][0]['jp_extent']=30;self.invalid()

    def test_unmeasured_eos_not_filled(self):
        self.value['candidates'][0]['eos_address']='0x083DDEE3';self.invalid()

    def test_third_candidate_cannot_be_added(self):
        self.value['candidates'].append(copy.deepcopy(self.value['candidates'][0]));self.invalid()

    def test_competing_boundary_cannot_be_promoted(self):
        self.value['rejected_third']['status']='accepted';self.invalid()

    def test_source_proof_cannot_increment_classification(self):
        self.value['formal_classification_added']=1;self.invalid()

    def test_candidate_status_cannot_be_accepted(self):
        self.value['candidates'][0]['status']='accepted';self.invalid()

    def test_current_cell_verified_cannot_be_true(self):
        self.value['candidates'][0]['registration']['cells'][0]['actual_cell_verified']=True;self.invalid()

    def test_current_registration_verified_cannot_be_true(self):
        self.value['candidates'][1]['registration_candidates'][0]['actual_registration_verified']=True;self.invalid()

    def test_caller_address_joins_mapping(self):
        self.value['candidates'][0]['callers'][0]['jp']='0x08000000';self.invalid()

    def test_api_address_joins_mapping(self):
        self.value['shared_api_source'][0]['jp']='0x08000000';self.invalid()

    def test_cell_offset_joins_geometry(self):
        self.value['candidates'][0]['registration']['cells'][0]['predicted_cell']='0x08419E08';self.invalid()

    def test_callback_thumb_bit_required(self):
        self.value['candidates'][1]['registration_candidates'][0]['registered_callback']='0x0812410C';self.invalid()

    def test_conflict_origin_joins_parsed_row(self):
        self.value['rejected_third']['origin_reference_address']='0x08000000';self.invalid()

    def test_top_status_stays_unaccepted(self):
        self.value['status']='accepted';self.invalid()


if __name__ == '__main__':
    unittest.main()
