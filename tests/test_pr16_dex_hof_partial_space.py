"""新scopeの区間モデルだけを検査。旧受入test/ROM/nativeを呼ばない。"""
import itertools
import copy
import unittest

from pr16_dex_hof_space_intervals import Access, Span, aligned, complement, merge_clip, plan_geometry, plan_materialized_successor
from pr16_dex_hof_partial_space import report


class IntervalTests(unittest.TestCase):
    def setUp(self):
        self.domain = Span(100, 200)

    def plan(self, owners=(), accesses=(), obligations=(), size=40, alignment=4):
        return plan_geometry(self.domain, owners, accesses, obligations, size, alignment)

    def test_empty_protection_is_geometry_only(self):
        p = self.plan()
        self.assertTrue(p["geometry_fits_contiguously"])
        self.assertFalse(p["lease_authorized"])
        self.assertFalse(p["rom_mutation_performed"])

    def test_actual_owner_blocks_entire_domain(self):
        p = self.plan(owners=(self.domain,))
        self.assertEqual(p["total_unprotected_bytes"], 0)

    def test_one_unknown_blocks_entire_domain(self):
        p = self.plan(accesses=(Access(10, 150),))
        self.assertEqual(p["unbounded_access_count"], 1)
        self.assertEqual(p["total_unprotected_bytes"], 0)

    def test_unknown_among_finite_bounds_still_blocks(self):
        p = self.plan(accesses=(Access(10, 120, (Span(120, 124),)), Access(20, 150)))
        self.assertEqual(p["total_unprotected_bytes"], 0)

    def test_indirect_obligation_independently_blocks(self):
        self.assertEqual(self.plan(obligations=("indirect-reference",))["total_unprotected_bytes"], 0)

    def test_retirement_obligation_independently_blocks(self):
        self.assertEqual(self.plan(obligations=("retirement",))["total_unprotected_bytes"], 0)

    def test_finite_extent_includes_backward_and_forward_access(self):
        p = self.plan(accesses=(Access(10, 150, (Span(120, 180),)),))
        self.assertEqual(p["gaps"], [{"address": 100, "size": 20}, {"address": 180, "size": 20}])
        self.assertFalse(p["geometry_fits_contiguously"])

    def test_disjoint_finite_envelopes_preserved(self):
        p = self.plan(accesses=(Access(10, 110, (Span(110, 115), Span(130, 160))),))
        self.assertEqual(p["total_unprotected_bytes"], 65)

    def test_extent_crossing_donor_edges_is_clipped(self):
        p = self.plan(accesses=(Access(10, 120, (Span(50, 140),)),))
        self.assertEqual(p["total_unprotected_bytes"], 60)

    def test_origin_may_be_outside_donor(self):
        p = self.plan(accesses=(Access(300, 120, (Span(120, 124),)),))
        self.assertEqual(p["total_unprotected_bytes"], 96)

    def test_target_outside_donor_rejected(self):
        with self.assertRaises(ValueError):
            self.plan(accesses=(Access(10, 200),))

    def test_empty_finite_extent_rejected(self):
        with self.assertRaises(ValueError):
            Access(10, 120, ())

    def test_extent_excluding_target_rejected(self):
        with self.assertRaises(ValueError):
            Access(10, 120, (Span(130, 140),))

    def test_duplicate_origins_rejected(self):
        with self.assertRaises(ValueError):
            self.plan(accesses=(Access(10, 120), Access(10, 140)))

    def test_overlap_and_adjacency_count_once(self):
        self.assertEqual(merge_clip(self.domain, (Span(90, 120), Span(110, 140), Span(140, 150))), (Span(100, 150),))

    def test_outside_owner_does_not_consume_domain(self):
        self.assertEqual(complement(self.domain, (Span(50, 100), Span(200, 250))), (self.domain,))

    def test_alignment_loss_is_counted(self):
        self.assertEqual(aligned((Span(101, 110),), 4), (Span(104, 110),))

    def test_alignment_can_remove_tiny_gap(self):
        self.assertEqual(aligned((Span(101, 104),), 4), ())

    def test_sum_of_fragments_does_not_mean_contiguous_fit(self):
        p = self.plan(owners=(Span(130, 170),), size=60)
        self.assertEqual(p["total_unprotected_bytes"], 60)
        self.assertFalse(p["geometry_fits_contiguously"])

    def test_exact_fit_is_permitted_only_as_geometry(self):
        p = self.plan(owners=(Span(140, 200),))
        self.assertTrue(p["geometry_fits_contiguously"])
        self.assertFalse(p["lease_authorized"])

    def test_invalid_span_types_and_overflow_rejected(self):
        for start, end in ((True, 20), (0, False), (2, 2), (2, 1), (-1, 2), (0, 2 ** 32 + 1), (0.0, 2)):
            with self.subTest(start=start, end=end), self.assertRaises(ValueError):
                Span(start, end)

    def test_invalid_alignment_rejected(self):
        for value in (0, -1, 3, True, 4.0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.plan(alignment=value)

    def test_invalid_request_rejected(self):
        for value in (0, -1, True, 4.0):
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.plan(size=value)

    def test_asserted_boolean_is_not_an_obligation_proof(self):
        with self.assertRaises(ValueError):
            self.plan(obligations=(True,))

    def test_no_lease_approval_argument_exists(self):
        with self.assertRaises(TypeError):
            plan_geometry(self.domain, (), (), (), 40, owner_released=True)

    def test_exhaustive_small_domain_against_set_oracle(self):
        domain = Span(3, 12)
        spans = [Span(a, b) for a in range(1, 14) for b in range(a + 1, 15)]
        for a, b in itertools.product(spans, repeat=2):
            expected = set(range(3, 12)) - set(range(a.start, a.end)) - set(range(b.start, b.end))
            actual = {v for s in complement(domain, (a, b)) for v in range(s.start, s.end)}
            self.assertEqual(actual, expected)

    def test_saved_current_scope_is_blocked_and_old_acceptance_not_rerun(self):
        r = report()
        self.assertEqual(r["current_plan"]["owner_count"], 115)
        self.assertEqual(r["current_plan"]["unbounded_access_count"], 148)
        self.assertEqual(r["current_plan"]["total_unprotected_bytes"], 0)
        self.assertEqual(r["unknown_frontier"]["unique_targets"], 109)
        self.assertEqual(r["unsafe_point_only_upper_bound"]["largest_gap_bytes"], 1269)
        self.assertEqual(r["unsafe_point_only_upper_bound"]["largest_aligned_gap"]["size"], 1266)
        self.assertEqual(r["other_known_capacity"]["global_free_bytes"], 511)
        self.assertEqual(r["other_known_capacity"]["save_subowner_free_bytes"], 804)
        self.assertEqual(r["other_known_capacity"]["deficit_vs_6528_bytes"], 5213)
        self.assertFalse(r["current_plan"]["lease_authorized"])
        self.assertTrue(all(v == 0 for k, v in r["execution"].items() if k != "lease_created"))


class SuccessorTests(unittest.TestCase):
    def setUp(self):
        self.domain = Span(100, 200)
        self.parent = {"candidate": {"size": 33554432, "sha256": "a" * 64},
                       "classified": 726, "unclassified": 148,
                       "hits": [{"address": 10000 + i * 4, "target": 100 + i % 100,
                                 "kind": "SYNTHETIC_ONLY", "size": 4, "sha256": "b" * 64,
                                 "accepted": i < 726, "classification": "TYPED" if i < 726 else "UNCLASSIFIED"}
                                for i in range(874)]}
        self.current = copy.deepcopy(self.parent)
        self.current["hits"][726].update(accepted=True, classification="TYPED")
        self.current.update(classified=727, unclassified=147)
        self.owners = {"candidate": self.parent["candidate"], "placement": {"owner_byte_audit": [
            {"name": str(i), "address": 100 if i == 0 else 1000 + i * 10, "size": 100 if i == 0 else 8}
            for i in range(115)]}}

    def plan(self):
        return plan_materialized_successor(self.parent, self.current, self.owners, self.domain)

    def test_new_unknown_147_remains_fully_protected(self):
        p = self.plan()
        self.assertEqual((p["parent_unknown_count"], p["current_unknown_count"], p["newly_classified_count"]), (148, 147, 1))
        self.assertEqual(p["unbounded_access_count"], 147)
        self.assertEqual(p["total_unprotected_bytes"], 0)
        self.assertFalse(p["lease_authorized"])

    def test_one_unknown_still_blocks(self):
        for r in self.current["hits"][:-1]:
            r.update(accepted=True, classification="TYPED")
        self.current.update(classified=873, unclassified=1)
        self.assertEqual(self.plan()["total_unprotected_bytes"], 0)

    def test_zero_unknown_does_not_bypass_owner_and_indirect_gates(self):
        for r in self.current["hits"]:
            r.update(accepted=True, classification="TYPED")
        self.current.update(classified=874, unclassified=0)
        self.assertEqual(self.plan()["total_unprotected_bytes"], 0)

    def test_inventory_reorder_rejected(self):
        self.current["hits"][0], self.current["hits"][1] = self.current["hits"][1], self.current["hits"][0]
        with self.assertRaises(ValueError):
            self.plan()

    def test_inventory_missing_row_rejected(self):
        self.current["hits"].pop()
        with self.assertRaises(ValueError):
            self.plan()

    def test_target_change_rejected(self):
        self.current["hits"][726]["target"] += 1
        with self.assertRaises(ValueError):
            self.plan()

    def test_old_accepted_proof_change_rejected(self):
        self.current["hits"][0]["extra"] = "rewritten-proof"
        with self.assertRaises(ValueError):
            self.plan()

    def test_remaining_unknown_proof_change_rejected(self):
        self.current["hits"][-1]["extra"] = "invented-bound"
        with self.assertRaises(ValueError):
            self.plan()

    def test_candidate_drift_rejected(self):
        self.current["candidate"]["sha256"] = "c" * 64
        with self.assertRaises(ValueError):
            self.plan()

    def test_owner_omission_rejected(self):
        self.owners["placement"]["owner_byte_audit"].pop()
        with self.assertRaises(ValueError):
            self.plan()

    def test_donor_owner_removal_with_constant_count_rejected(self):
        self.owners["placement"]["owner_byte_audit"][0]["address"] = 300
        with self.assertRaises(ValueError):
            self.plan()

    def test_counter_drift_rejected(self):
        self.current["unclassified"] = 0
        with self.assertRaises(ValueError):
            self.plan()

class FixedInputRefusalTests(unittest.TestCase):
    def build_root(self, directory):
        from pathlib import Path
        import pr16_dex_hof_partial_space as m
        root = Path(directory)
        paths = set(m.INPUTS) | {
            'overlays/hof_journal/hof_transaction.c', 'overlays/hof_journal/hof_transaction.h',
            'scripts/pr16_dex_hof_controller_actions.py', 'tests/test_pr16_dex_hof_controller.py',
            'tools/pr16_hof_controller_host.c'}
        for path in paths:
            target = root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((m.ROOT / path).read_bytes())
        return root

    def test_changed_frontier_entire_identity_refused(self):
        import tempfile
        import pr16_dex_hof_partial_space as m
        with tempfile.TemporaryDirectory() as directory:
            root = self.build_root(directory)
            path = root / next(iter(m.INPUTS))
            path.write_bytes(path.read_bytes() + b' ')
            with self.assertRaises(ValueError): m.report(root)

    def test_changed_measured_controller_source_refused(self):
        import tempfile
        import pr16_dex_hof_partial_space as m
        with tempfile.TemporaryDirectory() as directory:
            root = self.build_root(directory)
            path = root / 'overlays/hof_journal/hof_transaction.c'
            path.write_bytes(path.read_bytes() + b'\n')
            with self.assertRaises(ValueError): m.report(root)

    def test_changed_actual_owner_checkpoint_refused(self):
        import tempfile,json
        import pr16_dex_hof_partial_space as m
        with tempfile.TemporaryDirectory() as directory:
            root = self.build_root(directory)
            path = root / 'content/modernization/pr16_dex_hof_generation_writer_checkpoint.json'
            record = json.loads(path.read_bytes())
            record['link']['free_bytes'] += 6528
            path.write_text(json.dumps(record) + '\n')
            with self.assertRaises(ValueError): m.report(root)

    def test_missing_actual_owner_checkpoint_refused(self):
        import tempfile
        import pr16_dex_hof_partial_space as m
        with tempfile.TemporaryDirectory() as directory:
            root = self.build_root(directory)
            (root / 'content/modernization/pr16_dex_hof_generation_writer_checkpoint.json').unlink()
            with self.assertRaises(ValueError): m.report(root)

class SuccessorReportTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import pr16_dex_hof_partial_space as m
        import pr16_dex_hof_space_chain as chain
        cls.parent = chain.parent(*[(m.ROOT / path).read_bytes() for path in chain.PARENT_INPUTS])

    def test_parent_projection_is_unchanged_and_never_safe(self):
        import pr16_dex_hof_partial_space as m
        result = m.current_report(self.parent, parent_audit=self.parent)
        p = result['successor_point_only_projection']
        self.assertEqual((p['unique_targets'], p['largest_gap_bytes'], p['largest_aligned_gap_bytes']), (109,1269,1266))
        self.assertFalse(p['safe_to_lease'])
        self.assertEqual(result['successor_plan']['total_unprotected_bytes'], 0)

    def test_synthetic_classification_changes_only_hypothetical_projection(self):
        import pr16_dex_hof_partial_space as m
        current = copy.deepcopy(self.parent)
        for row in current['hits']:
            if row['address'] in (0x080F3C3F,0x08C0DF31):
                row.update(accepted=True,classification='SYNTHETIC_PROJECTION_ONLY')
        current.update(classified=728,unclassified=146)
        result = m.current_report(current, parent_audit=self.parent)
        p = result['successor_point_only_projection']
        d = result['donor']
        targets = {r['target'] for r in current['hits'] if not r['accepted']}
        self.assertEqual(p['total_gap_bytes'],d['size']-len(targets))
        self.assertEqual(p['unique_targets'],len(targets))
        self.assertFalse(p['safe_to_lease'])
        self.assertFalse(result['successor_plan']['semantic_chain_acceptance_rechecked'])
        self.assertFalse(result['successor_plan']['lease_eligible'])
        self.assertEqual(result['successor_plan']['total_unprotected_bytes'],0)

    def test_materialized_parent_unknown_cannot_self_sign(self):
        import pr16_dex_hof_partial_space as m
        changed=copy.deepcopy(self.parent)
        next(r for r in changed['hits']if not r['accepted'])['reason']='forged extent'
        with self.assertRaises(ValueError):m.current_report(changed,parent_audit=changed)


if __name__ == "__main__":
    unittest.main(verbosity=2)
