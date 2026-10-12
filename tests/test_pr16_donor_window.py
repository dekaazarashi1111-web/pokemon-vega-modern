"""新しい窓順位だけを検証。Forest/Bubble/ROM/旧受入は実行しない。"""
from __future__ import annotations
import copy
from pathlib import Path
import random
import sys
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import pr16_donor_window as m

L = m.BASE+0x1000

def hit(target=L, address=m.BASE, accepted=False, kind='ALL_BYTE_START_U32_ALL_ROM_MIRRORS'):
    return dict(target=target,address=address,size=4,sha256='a'*64,kind=kind,
        accepted=accepted,classification='FALSE_POSITIVE_TYPED_TEST' if accepted else 'UNCLASSIFIED')

class WindowTests(unittest.TestCase):
    def run_plan(self, rows=None, **kw):
        return m.analyze([] if rows is None else rows,kw.get('lo',L),kw.get('hi',L+32),
                         kw.get('required',8),kw.get('alignment',4))
    def bad(self, **kw):
        with self.assertRaises(ValueError): self.run_plan(**kw)
    def test_empty_has_no_safety_claim(self):
        r=self.run_plan();self.assertEqual(r['examined_windows'],7)
        self.assertEqual(r['claims'],m.CLAIMS);self.assertEqual(r['claims']['donor_safe_bytes'],0)
    def test_lower_target_included(self):
        r=self.run_plan([hit()],required=32)
        self.assertEqual(r['selected']['unclassified_target_entries'],1)
    def test_upper_target_excluded_half_open(self):
        r=self.run_plan([hit(L+8)])
        self.assertEqual(r['selected']['start'],L);self.assertEqual(r['selected']['unclassified_target_entries'],0)
    def test_last_byte_included(self):
        r=self.run_plan([hit(L+31)],required=32)
        self.assertEqual(r['selected']['unclassified_target_entries'],1)
    def test_lowest_start_tiebreak(self):
        self.assertEqual(self.run_plan()['selected']['start'],L)
    def test_first_target_changes_best_window(self):
        self.assertEqual(self.run_plan([hit()])['selected']['start'],L+4)
    def test_contiguous_optimal_band(self):
        self.assertEqual(self.run_plan()['optimal_start_bands'],[dict(first_start=L,last_start=L+24,windows=7)])
    def test_disjoint_optimal_bands(self):
        r=self.run_plan([hit(L+12)])
        self.assertEqual(len(r['optimal_start_bands']),2)
    def test_same_target_multiple_origins_count_separately(self):
        r=self.run_plan([hit(),hit(address=m.BASE+4)],required=32)
        self.assertEqual(r['selected']['unclassified_target_entries'],2)
        self.assertEqual(r['selected']['distinct_unclassified_targets'],1)
    def test_same_origin_distinct_inventory_kinds_retained(self):
        r=self.run_plan([hit(),hit(kind='THUMB_BL_SHAPE')],required=32)
        self.assertEqual(r['inherited']['total'],2)
    def test_accepted_false_positive_not_unknown(self):
        r=self.run_plan([hit(accepted=True)],required=32)
        self.assertEqual(r['selected']['accepted_false_positive_entries'],1)
        self.assertEqual(r['minimum_unclassified_target_entries'],0)
    def test_accepted_conditions_never_promote_capacity(self):
        r=self.run_plan([hit(accepted=True)],required=32)
        self.assertFalse(r['claims']['indirect_reference_completeness_claimed'])
        self.assertEqual(r['claims']['donor_safe_bytes'],0)
    def test_outside_points_are_still_unresolved(self):
        r=self.run_plan([hit(L+8)])
        self.assertEqual(r['outside_point_count'],1);self.assertTrue(r['outside_point_rows_still_unresolved'])
        self.assertFalse(r['claims']['outside_target_excludes_access'])
    def test_intra_owner_origin_omission_explicit(self):
        self.assertFalse(self.run_plan()['claims']['intra_donor_origins_covered'])
    def test_crossing_origin_is_retained(self):
        r=self.run_plan([hit(address=L-2)],required=32)
        self.assertEqual(r['selected']['unclassified_target_rows'][0]['address'],L-2)
    def test_non_aligned_donor_start_ceil(self):
        self.assertEqual(self.run_plan(lo=L+1)['first_start'],L+4)
    def test_non_aligned_end_floor(self):
        self.assertEqual(self.run_plan(hi=L+31)['last_start'],L+20)
    def test_size_not_multiple_of_alignment(self):
        self.assertEqual(self.run_plan(required=7)['selected']['size'],7)
    def test_one_fitting_window(self):
        self.assertEqual(self.run_plan(required=32)['examined_windows'],1)
    def test_bool_geometry_rejected(self): self.bad(required=True)
    def test_float_geometry_rejected(self): self.bad(required=8.0)
    def test_zero_requirement_rejected(self): self.bad(required=0)
    def test_negative_requirement_rejected(self): self.bad(required=-1)
    def test_too_large_requirement_rejected(self): self.bad(required=33)
    def test_non_power_two_alignment_rejected(self): self.bad(alignment=3)
    def test_zero_alignment_rejected(self): self.bad(alignment=0)
    def test_alignment_over_limit_rejected(self): self.bad(alignment=8192)
    def test_no_aligned_window_rejected(self): self.bad(lo=L+1,hi=L+3,required=2)
    def test_before_rom_rejected(self): self.bad(lo=m.BASE-1)
    def test_after_rom_rejected(self): self.bad(hi=m.ROM_END+1)
    def test_window_count_limit(self): self.bad(hi=L+100002,required=1,alignment=1)
    def test_rows_tuple_rejected(self): self.bad(rows=())
    def test_rows_count_limit(self): self.bad(rows=[hit()]*10001)
    def test_duplicate_rejected(self): self.bad(rows=[hit(),hit()])
    def test_missing_target_rejected(self):
        h=hit();del h['target'];self.bad(rows=[h])
    def test_target_outside_rejected(self): self.bad(rows=[hit(L+32)])
    def test_origin_outside_rejected(self): self.bad(rows=[hit(address=m.ROM_END-3)])
    def test_bool_target_rejected(self): self.bad(rows=[hit(True)])
    def test_wrong_size_rejected(self):
        h=hit();h['size']=3;self.bad(rows=[h])
    def test_unknown_kind_rejected(self): self.bad(rows=[hit(kind='GUESSED_POINTER')])
    def test_bool_int_accepted_rejected(self):
        h=hit();h['accepted']=0;self.bad(rows=[h])
    def test_inconsistent_classification_rejected(self):
        h=hit();h['classification']='FALSE_POSITIVE_TYPED_TEST';self.bad(rows=[h])
    def test_missing_hash_rejected(self):
        h=hit();del h['sha256'];self.bad(rows=[h])
    def test_nonhex_hash_rejected(self):
        h=hit();h['sha256']='z'*64;self.bad(rows=[h])
    def test_deterministic_input_order(self):
        rows=[hit(L+20,m.BASE+8),hit(L+12,m.BASE+4),hit()]
        self.assertEqual(m.encode(self.run_plan(rows)),m.encode(self.run_plan(rows[::-1])))
    def test_input_and_global_claims_unchanged(self):
        rows=[hit()];before=copy.deepcopy(rows);r=self.run_plan(rows);r['claims']['donor_safe_bytes']=1
        self.assertEqual(rows,before);self.assertEqual(m.CLAIMS['donor_safe_bytes'],0)
    def test_full_parent_identity_rejects_forged_input(self):
        with self.assertRaises(ValueError):m.bind_parent({},m.encode)
    def test_integer_identity_rejected(self):
        with self.assertRaises(ValueError):m.identity(1)
    def test_bisect_vs_exhaustive_oracle(self):
        rng=random.Random(20261011)
        for _ in range(150):
            rows=[hit(L+rng.randrange(32),m.BASE+i*4,rng.randrange(4)==0) for i in range(rng.randrange(30))]
            size=rng.randrange(1,33);alignment=rng.choice([1,2,4,8])
            r=self.run_plan(rows,required=size,alignment=alignment)
            oracle=[(sum(not h['accepted'] and s<=h['target']<s+size for h in rows),s)
                    for s in range(L,L+32-size+1,alignment)]
            best,start=min(oracle)
            self.assertEqual((r['minimum_unclassified_target_entries'],r['selected']['start']),(best,start))
            self.assertEqual(sum(b['windows'] for b in r['optimal_start_bands']),sum(score==best for score,_ in oracle))
            self.assertEqual(sum(x['windows'] for x in r['score_histogram']),len(oracle))

if __name__=='__main__':unittest.main()
