"""Semantic relocation, immutable candidate and Rare Candy boundary regressions."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import struct
import unittest
from pathlib import Path
from unittest import mock

from tools import modernization_runtime_boundary_repair as repair
from tools.modernization_p04_species_runtime import _apply_and_audit

ROOT = Path(__file__).resolve().parents[1]


class CollectionReferenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        stage = bytearray(repair.ROM_SIZE)
        for site, code in repair.COLLECTION_CODE_GUARDS.items():
            stage[site:site + len(bytes.fromhex(code))] = bytes.fromhex(code)
        for site in (*repair.ROOT_SITES, repair.POLICY_END_SITE):
            struct.pack_into('<I', stage, site, repair.COLLECTION_ROOT)
        for site in (*repair.UNRELATED_END_VALUE_SITES, repair.END_SITE):
            struct.pack_into('<I', stage, site, repair.COLLECTION_END)
        struct.pack_into('<I', stage, repair.POLICY_START_SITE, 0x092D6C10)
        cls.start = 0x1800000
        cls.size = 1670 * 8
        stage[cls.start:cls.start + cls.size] = b'\xff' * cls.size
        cls.stage = bytes(stage)
        cls.table = dict(current_address=repair.COLLECTION_ROOT, old_count=1621,
                         new_count=1670, stride_bytes=8, old_size_bytes=1621 * 8,
                         new_size_bytes=1670 * 8)
        cls.rows = [dict(site_offset=site, site_address=repair.ROM_BASE + site,
                         old_pointer=repair.COLLECTION_ROOT)
                    for site in sorted((*repair.ROOT_SITES, repair.POLICY_END_SITE))]

    def classify(self, stage=None, rows=None, table=None):
        return repair.classify_collection_consumers(
            self.stage if stage is None else stage,
            self.rows if rows is None else rows,
            self.table if table is None else table)

    def generated(self):
        rows = self.classify()
        output, spans = _apply_and_audit(
            self.stage, bytes(self.size),
            dict(start=self.start, end_exclusive=self.start + self.size),
            {'acquisition_collection_defs': dict(payload_relative_offset=0, new_size=self.size)},
            {'acquisition_collection_defs': rows}, [], [], [])
        return output, spans, rows

    def test_equal_value_is_classified_as_three_roots_and_one_policy_end(self):
        rows = self.classify()
        self.assertEqual(sum(r['reference_role'] == 'root' for r in rows), 3)
        self.assertEqual(sum(r['reference_role'] == 'collection_end' for r in rows), 1)
        self.assertEqual(sum(r['reference_role'] == 'preserve_policy_end' for r in rows), 1)
        self.assertEqual(len(rows), 5)

    def test_actual_generator_relocates_start_and_end_but_not_policy_end(self):
        output, spans, rows = self.generated()
        start = repair.ROM_BASE + self.start
        for site in repair.ROOT_SITES:
            self.assertEqual(repair.u32(output, site), start)
        self.assertEqual(repair.u32(output, repair.END_SITE), start + self.size)
        self.assertEqual(repair.u32(output, repair.POLICY_END_SITE), repair.COLLECTION_ROOT)
        self.assertFalse(any(r['start'] <= repair.POLICY_END_SITE < r['end_exclusive'] for r in spans))
        repair.validate_relocated_references(output, rows, start, self.size, repair.COLLECTION_ROOT)

    def test_actual_generator_keeps_equal_valued_unrelated_table_roots(self):
        output, _, _ = self.generated()
        for site in repair.UNRELATED_END_VALUE_SITES:
            self.assertEqual(repair.u32(output, site), repair.COLLECTION_END)
        self.assertEqual(repair.occurrences(output, repair.COLLECTION_END),
                         list(repair.UNRELATED_END_VALUE_SITES))

    def test_unknown_missing_and_duplicate_sites_fail_closed(self):
        variants = [self.rows[:-1], self.rows + [self.rows[0]],
                    [*self.rows[:-1], dict(site_offset=100, old_pointer=repair.COLLECTION_ROOT)]]
        for rows in variants:
            with self.subTest(rows=rows), self.assertRaises(repair.BoundaryRepairError):
                self.classify(rows=rows)

    def test_new_equal_valued_root_candidate_is_rejected(self):
        stage = bytearray(self.stage)
        struct.pack_into('<I', stage, 100, repair.COLLECTION_ROOT)
        with self.assertRaises(repair.BoundaryRepairError):
            self.classify(stage=bytes(stage))

    def test_new_equal_valued_end_candidate_is_rejected(self):
        stage = bytearray(self.stage)
        struct.pack_into('<I', stage, 100, repair.COLLECTION_END)
        with self.assertRaises(repair.BoundaryRepairError):
            self.classify(stage=bytes(stage))

    def test_table_dimensions_are_not_inferred_from_coincidental_values(self):
        for key in self.table:
            table = {**self.table, key: self.table[key] + 1}
            with self.subTest(key=key), self.assertRaises(repair.BoundaryRepairError):
                self.classify(table=table)

    def test_each_consumer_opcode_is_guarded(self):
        for site in repair.COLLECTION_CODE_GUARDS:
            stage = bytearray(self.stage)
            stage[site] ^= 1
            with self.subTest(site=site), self.assertRaises(repair.BoundaryRepairError):
                self.classify(stage=bytes(stage))

    def test_policy_start_and_row_preimages_are_guarded(self):
        stage = bytearray(self.stage)
        stage[repair.POLICY_START_SITE] ^= 1
        with self.assertRaises(repair.BoundaryRepairError):
            self.classify(stage=bytes(stage))
        rows = copy.deepcopy(self.rows)
        rows[0]['old_pointer'] += 4
        with self.assertRaises(repair.BoundaryRepairError):
            self.classify(rows=rows)

    def test_unknown_role_or_misclassified_endpoint_is_rejected(self):
        for row in (dict(reference_role='skip', site_offset=repair.POLICY_END_SITE),
                    dict(reference_role='preserve_policy_end', site_offset=repair.END_SITE,
                         old_pointer=repair.COLLECTION_ROOT),
                    dict(reference_role='collection_end', site_offset=repair.POLICY_END_SITE,
                         old_pointer=repair.COLLECTION_END)):
            with self.subTest(row=row), self.assertRaises(repair.BoundaryRepairError):
                repair.reference_target(row, repair.NEW_COLLECTION_ROOT, self.size)

    def test_out_of_rom_destination_is_rejected(self):
        for root, size in ((repair.ROM_BASE-4, 4), (repair.ROM_BASE+repair.ROM_SIZE-4, 8),
                           (repair.NEW_COLLECTION_ROOT, 0)):
            with self.subTest(root=root, size=size), self.assertRaises(repair.BoundaryRepairError):
                repair.reference_target(self.rows[0], root, size)

    def test_readback_rejects_old_end_policy_mispatch_and_extra_old_root(self):
        output, _, rows = self.generated()
        for site, value in ((repair.END_SITE, repair.COLLECTION_END),
                            (repair.POLICY_END_SITE, repair.ROM_BASE+self.start),
                            (100, repair.COLLECTION_ROOT)):
            corrupted = bytearray(output)
            struct.pack_into('<I', corrupted, site, value)
            with self.subTest(site=site), self.assertRaises(repair.BoundaryRepairError):
                repair.validate_relocated_references(bytes(corrupted), rows,
                    repair.ROM_BASE + self.start, self.size, repair.COLLECTION_ROOT)


class RepairedProductTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = (ROOT / repair.PARENT_PATH).read_bytes()
        cls.candidate = repair.repair_rom(cls.parent)

    def test_candidate_has_fixed_distinct_identity(self):
        self.assertEqual(hashlib.sha256(self.parent).hexdigest(), repair.PARENT_SHA256)
        self.assertEqual(hashlib.sha256(self.candidate).hexdigest(),
                         '6570b82fc062cf163fa66a6d821fea6563021e5a9ca6f26efd583bae71623442')
        self.assertNotEqual(self.parent, self.candidate)
        self.assertEqual(len(self.candidate), repair.ROM_SIZE)

    def test_exactly_eight_bytes_change_only_within_three_literal_words(self):
        allowed = {site + i for site, _, _, _ in repair.PATCHES for i in range(4)}
        changed = {i for i, (a, b) in enumerate(zip(self.parent, self.candidate)) if a != b}
        self.assertEqual(len(changed), 8)
        self.assertLessEqual(changed, allowed)

    def test_parent_mutations_and_repairing_candidate_again_are_rejected(self):
        for site in (0, repair.END_SITE, repair.POLICY_END_SITE,
                     repair.CANDY_ACCESSOR_SITE, repair.ROM_SIZE - 1):
            changed = bytearray(self.parent)
            changed[site] ^= 1
            with self.subTest(site=site), self.assertRaises(repair.BoundaryRepairError):
                repair.repair_rom(bytes(changed))
        with self.assertRaises(repair.BoundaryRepairError):
            repair.repair_rom(self.candidate)
        with self.assertRaises(repair.BoundaryRepairError):
            repair.repair_rom(self.parent[:-1])

    def test_native_level_abi_explains_zero_and_repairs_only_party_candy_accessor(self):
        self.assertEqual(repair.u32(self.parent, 0x3F544 + 56 * 4), 0x0803FA50)
        self.assertEqual(repair.u32(self.parent, 0x3F374 + (56-55) * 4), 0x0803F400)
        self.assertEqual(repair.u32(self.parent, repair.CANDY_ACCESSOR_SITE), repair.BOX_ACCESSOR)
        self.assertEqual(repair.u32(self.candidate, repair.CANDY_ACCESSOR_SITE), repair.PARTY_ACCESSOR)
        repair.guard_code(self.candidate, repair.CANDY_CODE_GUARDS)
        source = (ROOT / 'overlays/qol_production/qol_production.c').read_text()
        body = source.split('static void candy_continue_task(u8 task_id)\n{', 1)[1].split('\nPUBLIC_TEXT(', 1)[0]
        self.assertNotIn('FN_GET_BOX_MON_DATA(', body)
        self.assertEqual(body.count('FN_GET_MON_DATA('), 4)

    def test_floette_bounds_and_unrelated_equal_values_are_preserved(self):
        self.assertEqual(repair.u32(self.candidate, repair.END_SITE), repair.NEW_COLLECTION_END)
        self.assertEqual(repair.u32(self.candidate, repair.POLICY_END_SITE), repair.COLLECTION_ROOT)
        self.assertEqual(repair.u32(self.candidate, repair.POLICY_START_SITE), 0x092D6C10)
        self.assertEqual(repair.occurrences(self.candidate, repair.COLLECTION_ROOT), [repair.POLICY_END_SITE])
        self.assertEqual(repair.occurrences(self.candidate, repair.COLLECTION_END), list(repair.UNRELATED_END_VALUE_SITES))

    def test_report_never_promotes_product_or_reuses_stale_allocation_hashes(self):
        report = repair.make_report(self.parent, self.candidate)
        self.assertEqual(report['changed_bytes'], 8)
        self.assertEqual(report['active_play_baseline_stage'], 62)
        self.assertEqual(report['new_allocations'], 0)
        for key in ('runtime_acceptance', 'done', 'release_ready',
                    'parent_allocation_content_hashes_reused_as_candidate'):
            self.assertIs(report[key], False)
        with self.assertRaises(repair.BoundaryRepairError):
            repair.make_report(self.parent, self.parent)

    def test_live_acceptance_adds_exact_level_exp_and_consumption_checks(self):
        source = (ROOT / 'tools/mgba_modernization_p02_stage71_acceptance_smoke.c').read_text()
        for name in ('cancel', 'success'):
            body = source.split(f'    bool {name}_ok = ', 1)[1].split(';', 1)[0]
            self.assertIn('QOL_MON_DATA_LEVEL) == 16U', body)
            self.assertIn('QOL_MON_DATA_EXP) == 2535U', body)
            self.assertIn('p02s_bag_exact(core, P02S_ITEM_RARE_CANDY, 0U)', body)
            self.assertIn(f'p02s_scene_seen(&{name})', body)


class CandidatePlanTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location('boundary_stage79',
            ROOT / 'scripts/run_modernization_stage79_cumulative_mgba.py')
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)
        cls.config = json.loads((ROOT / 'config/modernization_stage79_cumulative_mgba.json').read_text())
        cls.parent = (ROOT / repair.PARENT_PATH).read_bytes()
        cls.audit = {'stage': 78, 'rom': repair.rom_identity(repair.PARENT_PATH, cls.parent)}

    def test_candidate_plan_is_explicit_and_original_parent_is_retained(self):
        rom, audit = self.module._validate_runtime_candidate(self.config, self.parent, self.audit)
        self.assertEqual(rom, repair.repair_rom(self.parent))
        self.assertEqual(audit['stage'], 80)
        self.assertEqual(audit['parent'], self.audit)
        self.assertEqual(audit['changed_bytes_from_parent'], 8)

    def test_missing_or_repointed_candidate_is_not_fallback_to_old_rom(self):
        for key in ('stage', 'task', 'rom', 'recipe', 'report'):
            config = copy.deepcopy(self.config)
            del config['runtime_candidate'][key]
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                self.module._validate_runtime_candidate(config, self.parent, self.audit)
        config = copy.deepcopy(self.config)
        del config['runtime_candidate']
        with self.assertRaises(RuntimeError):
            self.module._validate_runtime_candidate(config, self.parent, self.audit)

    def test_forged_report_and_candidate_content_are_rejected_after_file_read(self):
        real_fixed = self.module._fixed
        for label in ('Stage80 repair report', 'Stage80 candidate ROM'):
            def corrupt(identity, current_label):
                path, raw = real_fixed(identity, current_label)
                if current_label == label:
                    if label == 'Stage80 repair report':
                        data = json.loads(raw)
                        data['runtime_acceptance'] = True
                        raw = repair.stable(data)
                    else:
                        raw = self.parent
                return path, raw
            with self.subTest(label=label), mock.patch.object(self.module, '_fixed', side_effect=corrupt):
                with self.assertRaises(RuntimeError):
                    self.module._validate_runtime_candidate(self.config, self.parent, self.audit)


if __name__ == '__main__':
    unittest.main()
