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
                         '6ff621edb1c1f99c6b1feb665ddce576eff939519776a2135002ab4fa90603a3')
        self.assertNotEqual(self.parent, self.candidate)
        self.assertEqual(len(self.candidate), repair.ROM_SIZE)

    def test_exactly_51_bytes_change_only_within_reviewed_literal_and_code_spans(self):
        allowed = {site + i for site, _, _, _ in repair.PATCHES for i in range(4)}
        allowed.update(site + i for site, old_hex, _, _ in repair.CODE_PATCHES
                       for i in range(len(bytes.fromhex(old_hex))))
        changed = {i for i, (a, b) in enumerate(zip(self.parent, self.candidate)) if a != b}
        self.assertEqual(len(changed), 51)
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
        self.assertEqual(report['changed_bytes'], 51)
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
        self.assertEqual(audit['changed_bytes_from_parent'], 51)

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


# Executable regressions extracted from the actual runner, not Python copies.
import ctypes
import re
import subprocess
import tempfile


class SceneInputRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / 'tools/mgba_modernization_p02_stage71_acceptance_smoke.c').read_text()
        function = 'static uint16_t p02s_scene_key(' + cls.text.split(
            'static uint16_t p02s_scene_key(', 1)[1].split('static uint16_t p02s_move_dialog_key(', 1)[0]
        constants = 'enum {\n' + '\n'.join(re.findall(r'^    P02S_CB2_.*$', cls.text, re.M)) + '\n};'
        source = '#include <stdint.h>\n#include <stdbool.h>\n' + constants + '''
#define QOL_KEY_A 1U
#define QOL_KEY_B 2U
struct P02SScene { bool begin_seen, update_seen, physical_b; };
''' + function + '''
unsigned scene_key(unsigned callback, unsigned species, bool cancel, bool started, unsigned frame) {
    struct P02SScene trace = {0};
    unsigned key = p02s_scene_key(callback, species, cancel, started, 1, 2, frame, &trace);
    return key | (trace.begin_seen << 8) | (trace.update_seen << 9) | (trace.physical_b << 10);
}
'''
        cls.directory = tempfile.TemporaryDirectory(prefix='stage79-scene-key-')
        cls.addClassCleanup(cls.directory.cleanup)
        path = Path(cls.directory.name)
        (path / 'probe.c').write_text(source)
        subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                        str(path / 'probe.c'), '-o', str(path / 'probe.so')], check=True, capture_output=True)
        cls.lib = ctypes.CDLL(str(path / 'probe.so'))
        cls.key = cls.lib.scene_key
        cls.key.argtypes = [ctypes.c_uint, ctypes.c_uint, ctypes.c_bool, ctypes.c_bool, ctypes.c_uint]
        cls.key.restype = ctypes.c_uint

    def test_cancel_releases_before_retrying_real_b_edge(self):
        values = [self.key(0x080CF869, 1, True, True, frame) for frame in range(241)]
        self.assertEqual([i for i, v in enumerate(values) if v & 2], [0, 1, 120, 121, 240])
        self.assertTrue(all(bool(v & 2) == bool(v & 1024) for v in values))
        self.assertTrue(all(v & 512 for v in values))

    def test_start_bag_party_exit_never_reopens_with_a(self):
        for callback in (0x08055E75, 0x081089E5, 0x0811F3A9):
            for species, cancel in ((1, True), (2, False)):
                with self.subTest(callback=callback, species=species):
                    keys = [self.key(callback, species, cancel, True, f) & 255 for f in range(241)]
                    self.assertEqual([i for i, v in enumerate(keys) if v], [0, 1, 120, 121, 240])
                    self.assertNotIn(1, keys)

    def test_pre_evolution_selection_still_uses_a(self):
        self.assertEqual(self.key(0x0811F3A9, 1, True, False, 0) & 255, 1)
        self.assertEqual(self.key(0x0811F3A9, 1, False, False, 2) & 255, 0)

    def test_success_does_not_get_cancellation_input(self):
        for frame in range(240):
            self.assertEqual(self.key(0x080CF869, 1, False, True, frame) & 1026, 0)
        self.assertEqual(self.key(0x080CEE71, 1, False, True, 0) & 256, 256)

    def test_optional_move_dialog_pattern_is_preserved_off_menus(self):
        self.assertEqual(self.key(0x0813868D, 2, False, True, 0) & 255, 2)
        self.assertEqual(self.key(0x0813868D, 2, False, True, 120) & 255, 1)

    def test_scene_acceptance_still_requires_unlocked_field_and_both_callbacks(self):
        body = self.text.split('static struct P02SScene p02s_run_item_scene(', 1)[1].split(
            'static bool p02s_scene_seen', 1)[0]
        self.assertIn('QOL_SCRIPT_CONTEXT_ENABLED', body)
        self.assertIn('0U, 0U, 0U, 0U) == 0U)', body)
        self.assertIn('trace->begin_seen && trace->update_seen', self.text)


class CompactStorageFixtureRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = (ROOT / 'overlays/modernization_floette_gift/mgba_modernization_floette_gift_smoke.c').read_text()
        fill = 'static void fg_fill_boxes(' + cls.text.split('static void fg_fill_boxes(', 1)[1].split(
            'static void fg_verify_map(', 1)[0]
        clear = 'static void fg_clear_boxes(' + cls.text.split('static void fg_clear_boxes(', 1)[1].split(
            'static void fg_create_mon(', 1)[0]
        constants = '\n'.join(re.findall(r'^#define FG_.*$', cls.text, re.M))
        source = '#include <stdint.h>\n#include <stddef.h>\n#include <setjmp.h>\n#include <string.h>\n' + constants + '''
#ifndef FG_SET_BOX_MON
#define FG_SET_BOX_MON 0x09123D51U
#endif
struct mCore { unsigned unused; };
static unsigned slots[25][30], calls, zeros, reads, exps, mode;
static jmp_buf trap;
static const uint32_t fg_get_boxed_mon_ptr = 0x09123AE1U;
static const uint32_t fg_get_box_mon_data = 0x09123BE5U;
static const uint32_t fg_zero_box_mon = 0x091239C9U;
static void fg_die(const char *message) { (void)message; longjmp(trap, 1); }
static void fg_create_fixture_mon(struct mCore *core) { (void)core; }
static uint32_t fg_call_thumb(struct mCore *core, uint32_t fn, uint32_t a, uint32_t b, uint32_t c, uint32_t d) {
    (void)core; (void)d;
    if (fn == FG_GET_MON_DATA && a == FG_SCRATCH && b == 25U) return 125U;
    if (a >= 25U || b >= 30U) fg_die("out of bounds");
    if (fn == FG_SET_BOX_MON) {
        if (c != FG_SCRATCH) fg_die("bad source");
        ++calls;
        if (mode != 1U || calls != 1U) slots[a][b] = 25U;
        if (mode == 2U && calls == 420U) slots[0][0] = 0U;
        return 0;
    }
    if (fn == fg_get_boxed_mon_ptr) return 0x02000000U;
    if (fn == fg_zero_box_mon) { ++zeros; slots[a][b] = 0; return 0; }
    if (fn == fg_get_box_mon_data && c == 11U) { ++reads; return slots[a][b]; }
    if (fn == fg_get_box_mon_data && c == 25U) { ++exps; return mode == 3U ? 0U : 125U; }
    fg_die("unexpected ROM call"); return 0;
}
static unsigned __attribute__((unused)) read8(struct mCore *c, uint32_t a) { (void)c; (void)a; return 0; }
static void __attribute__((unused)) fg_write8(struct mCore *c, uint32_t a, uint8_t v) { (void)c; (void)a; (void)v; }
''' + fill + clear + '''
int exercise(unsigned failure_mode, unsigned clear_after) {
    memset(slots, 0, sizeof(slots)); calls = zeros = reads = exps = 0; mode = failure_mode;
    if (setjmp(trap)) return -1;
    struct mCore core = {0}; fg_fill_boxes(&core);
    if (calls != 420U || reads != 840U || exps != 420U) return -2;
    for (unsigned b = 0; b < 25; ++b) for (unsigned p = 0; p < 30; ++p) if (slots[b][p] != (b < 14U ? 25U : 0U)) return -3;
    if (clear_after) {
        fg_clear_boxes(&core);
        if (zeros != 420U) return -4;
        for (unsigned b = 0; b < 25; ++b) for (unsigned p = 0; p < 30; ++p) if (slots[b][p]) return -5;
    }
    return 0;
}
'''
        cls.directory = tempfile.TemporaryDirectory(prefix='stage79-compact-pc-')
        cls.addClassCleanup(cls.directory.cleanup)
        path = Path(cls.directory.name)
        (path / 'probe.c').write_text(source)
        subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-shared', '-fPIC',
                        str(path / 'probe.c'), '-o', str(path / 'probe.so')], check=True, capture_output=True)
        cls.lib = ctypes.CDLL(str(path / 'probe.so'))
        cls.exercise = cls.lib.exercise
        cls.exercise.argtypes = [ctypes.c_uint, ctypes.c_uint]
        cls.exercise.restype = ctypes.c_int

    def test_all_420_field_slots_are_written_and_pc_only_pools_untouched(self):
        self.assertEqual(self.exercise(0, 0), 0)

    def test_all_14_field_boxes_are_cleared_without_touching_pc_only_pools(self):
        self.assertEqual(self.exercise(0, 1), 0)

    def test_failed_native_write_cannot_be_counted_as_full(self):
        self.assertEqual(self.exercise(1, 0), -1)

    def test_late_alias_corruption_is_detected_by_second_pass(self):
        self.assertEqual(self.exercise(2, 0), -1)

    def test_wrong_stored_experience_is_rejected(self):
        self.assertEqual(self.exercise(3, 0), -1)

    def test_actual_native_setter_body_is_guarded_before_fixture_setup(self):
        body = self.text.split('static void fg_verify_storage_abi(', 1)[1].split('static void fg_clear_boxes(', 1)[0]
        expected = bytes(int(v, 16) for v in re.findall(r'0x([0-9A-F]{2})\b', body))
        rom = (ROOT / 'build/stages/80_modernization_runtime_boundary_repair.gba').read_bytes()
        self.assertEqual(expected, rom[0x1123D50:0x1123D90])
        self.assertEqual(len(expected), 64)
        self.assertLess(self.text.index('    fg_verify_storage_abi(core);'), self.text.index('    fg_clear_boxes(core);'))
        self.assertIn('fg_verify_field_capacity(core, claim);', self.text)


if __name__ == '__main__':
    unittest.main()
