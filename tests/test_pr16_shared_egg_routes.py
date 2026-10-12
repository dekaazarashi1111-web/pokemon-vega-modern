"""Oracle/validator negatives only. Native successes are separate exact runs."""
from copy import deepcopy
from pathlib import Path
import struct
import sys
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_shared_egg_routes as shared
import pr16_integrated_native as parent


def row(sid, legacy=None, moves=None, form='', carry=1):
    return {'species': sid, 'form_key': form, 'pre_evolution_carry': carry,
            'legacy': [33] if legacy is None else legacy,
            'shared': [69, 215] if moves is None else moves}


class SharedEggOracleTests(unittest.TestCase):
    def test_reverse_table_keeps_first_matching_parent(self):
        raw = bytearray(0x21615C + 412*40)
        for sid in (17, 22):
            struct.pack_into('<H', raw, 0x21615C + sid*40 + 4, 400)
        self.assertEqual(shared.reverse_table(raw), {400: 17})

    def test_legacy_reverse_chain_stops_after_five(self):
        self.assertEqual(shared.egg_species(10, {i: i-1 for i in range(1, 11)}), 5)
        self.assertEqual(shared.egg_species(10, {}), 10)

    def test_own_tempo_override_is_not_normal_rockruff(self):
        self.assertEqual(shared.egg_species(1263, {}), 1670)
        self.assertEqual(shared.egg_species(1670, {1670: 1142}), 1670)
        self.assertEqual(shared.egg_species(1142, {}), 1142)

    def test_national_override_and_incense_union_are_independent(self):
        pool, witness = shared.legacy_pool(25, {}, {25: 25}, {24: [344]}, {})
        self.assertEqual(pool, [344]); self.assertEqual(witness['primary_species'], 24)
        pool, witness = shared.legacy_pool(517, {517: 608}, {}, {608: [47, 727], 517: [727, 33]}, {})
        self.assertEqual(pool, [47, 727, 33]); self.assertEqual(witness['secondary_species'], 517)

    def test_exact_incense_collision_bypasses_ancestral_union(self):
        pool, witness = shared.legacy_pool(608, {608: 1}, {}, {1: [999], 517: [998]}, {608: [47, 727]})
        self.assertEqual(pool, [47, 727]); self.assertEqual(witness['kind'], 'exact-conflict')

    def test_happiny_additions_remain_preserved_not_new_shared_rows(self):
        pool, _ = shared.legacy_pool(364, {}, {}, {}, {364: [69, 461]})
        self.assertEqual(pool, [69, 461, 464, 357])

    def test_receiver_selection_is_deterministic_not_result_driven(self):
        rows = [row(20), row(15), row(10, moves=[69])]
        first, eligible = shared.select_receivers(rows)
        second, _ = shared.select_receivers(list(reversed(rows)))
        self.assertEqual([r['species'] for r in first], [15, 20])
        self.assertEqual(first, second); self.assertEqual(eligible, 3)

    def test_inherited_known_base_and_alternate_form_are_not_append_witnesses(self):
        bad = [row(1, legacy=[69, 215]), row(2, moves=[33, 81]), row(3, carry=0), row(4, form='battle')]
        with self.assertRaises(ValueError):
            shared.select_receivers(bad + [row(5)])

    def test_native_candidate_overflow_is_rejected_not_truncated(self):
        with self.assertRaises(ValueError):
            shared.select_receivers([row(1, legacy=list(range(1, 42)), moves=[100]), row(2)])

    def test_duplicate_receivers_cannot_inflate_native_coverage(self):
        with self.assertRaises(ValueError):
            shared.select_receivers([row(1), row(1)])

    def audit(self):
        selected, _ = shared.select_receivers([row(500), row(600)])
        return {'selected_receivers': selected, 'canonical_pp': {69: 20, 215: 5}}

    def test_all_slots_empty_and_cancels_have_exact_pp_transactions(self):
        cases = shared.build_cases(self.audit(), parent.make_case)
        self.assertEqual(len(cases), 16)
        for species in (500, 600):
            group = [c for c in cases if c['species'] == species]
            self.assertEqual([c['slot'] for c in group if c['action'] == 0], [0, 1, 2, 3])
            for c in group:
                self.assertEqual(c['herb'], 0)
                self.assertEqual((c['dh'], c['hof'], c['family']), (1, 1, 2))
                if c['action'] < 2:
                    self.assertEqual(c['after'][c['slot']], c['expected'])
                    self.assertEqual((c['pp_bonuses_after'] >> (2*c['slot'])) & 3, 0)
                else:
                    self.assertEqual((c['after'], c['pp_after'], c['pp_bonuses_after']),
                                     (c['known'], c['pp_before'], c['pp_bonuses_before']))
                    self.assertEqual(c['canonical_pp'], 0)

    def test_shared_target_relabelled_as_legacy_is_rejected(self):
        audit = deepcopy(self.audit())
        audit['selected_receivers'][0]['legacy'].extend([69, 215])
        with self.assertRaises(ValueError):
            shared.build_cases(audit, parent.make_case)

if __name__ == '__main__':
    unittest.main()
