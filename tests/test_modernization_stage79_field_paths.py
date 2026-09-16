"""Executable regressions for the native field paths, not relaxed PASS fixtures."""
from __future__ import annotations

import ctypes
import hashlib
from pathlib import Path
import re
import shutil
import struct
import subprocess
import tempfile
import unittest

from tools import modernization_runtime_boundary_repair as repair

ROOT = Path(__file__).resolve().parents[1]
P02 = ROOT / 'tools/mgba_modernization_p02_stage71_acceptance_smoke.c'
FG = ROOT / 'overlays/modernization_floette_gift/mgba_modernization_floette_gift_smoke.c'


def function(text: str, signature: str) -> str:
    start = text.index(signature)
    opening = text.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (text[end] == '{') - (text[end] == '}')
        end += 1
    return text[start:end]


def compile_probe(owner: unittest.TestCase, source: str) -> ctypes.CDLL:
    directory = tempfile.TemporaryDirectory(prefix='stage79-field-regression-')
    owner.addClassCleanup(directory.cleanup)
    path = Path(directory.name)
    (path / 'probe.c').write_text(source)
    subprocess.run(['cc', '-std=c11', '-Wall', '-Wextra', '-Werror', '-shared',
                    '-fPIC', str(path / 'probe.c'), '-o', str(path / 'probe.so')],
                   check=True, capture_output=True)
    return ctypes.CDLL(str(path / 'probe.so'))


class NativeMoveDialogTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = P02.read_text()
        body = function(cls.text, 'static uint16_t p02s_move_dialog_key(')
        cls.lib = compile_probe(cls, '''#include <stdint.h>
#include <stdbool.h>
#define P02S_CB2_PARTY 0x0811F3A9U
#define QOL_KEY_A 1U
#define QOL_KEY_B 2U
''' + body + '''
unsigned key(unsigned cb, unsigned active, unsigned task, unsigned frame, unsigned fallback) {
    return p02s_move_dialog_key(cb, active != 0, task, frame, fallback);
}
''')
        cls.key = cls.lib.key
        cls.key.argtypes = [ctypes.c_uint] * 5
        cls.key.restype = ctypes.c_uint

    def test_replace_prompt_is_refused_with_physical_b(self):
        self.assertEqual(self.key(0x0811F3A9, 1, 0x08126705, 0, 1), 2)

    def test_stop_learning_confirmation_is_accepted_with_physical_a(self):
        self.assertEqual(self.key(0x0811F3A9, 1, 0x08126AB9, 0, 2), 1)

    def test_both_dialogs_release_between_retries(self):
        for task, expected in ((0x08126705, 2), (0x08126AB9, 1)):
            values = [self.key(0x0811F3A9, 1, task, i, 4) for i in range(241)]
            self.assertEqual([i for i, v in enumerate(values) if v], [0, 1, 120, 121, 240])
            self.assertEqual(set(values), {0, expected})

    def test_inactive_or_other_tasks_do_not_override_scheduler(self):
        for task in (0x08126705, 0x08126AB9):
            self.assertEqual(self.key(0x0811F3A9, 0, task, 0, 4), 4)
            self.assertEqual(self.key(0x080CF869, 1, task, 0, 2), 2)
        self.assertEqual(self.key(0x0811F3A9, 1, 0x08120319, 0, 1), 1)

    def test_real_scene_observes_tasks_but_does_not_repair_mon_afterward(self):
        body = function(self.text, 'static struct P02SScene p02s_run_item_scene(')
        self.assertIn('p02s_move_dialog_key(callback, read8(core, task + 4U) != 0U,', body)
        self.assertIn('core->setKeys(core, key);', body)
        self.assertNotIn('p02s_set_data(', body)
        self.assertNotIn('write8(', body)
        self.assertIn('cancelled form evolution consumed the condition item', self.text)
        self.assertIn('native Bag evolution target missed the P02 payload', self.text)


class FieldCapacityAndBootstrapTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = FG.read_text()
        constants = '\n'.join(re.findall(r'^#define FG_.*$', cls.text, re.M))
        capacity = function(cls.text, 'static void fg_verify_field_capacity(')
        pointer = function(cls.text, 'static bool fg_ewram_pointer(')
        bootstrap = function(cls.text, 'static void fg_prepare_fresh_save_pointers(')
        cls.lib = compile_probe(cls, '''#include <stdint.h>
#include <stdbool.h>
#include <setjmp.h>
''' + constants + '''
struct mCore { unsigned unused; };
static jmp_buf trap;
static unsigned mode, calls;
static uint32_t pointers[3];
static void fg_die(const char *s) { (void)s; longjmp(trap, 1); }
static uint16_t read16(struct mCore *c, uint32_t a) {
    (void)c;
    if (a == 0x09462B82U) return mode == 1 ? 0x2E1DU : 0x2E1EU;
    if (a == 0x09462B8CU) return mode == 2 ? 0x2C19U : 0x2C0EU;
    if (a == 0x09462B90U) return mode == 3 ? 0x2007U : 0x2004U;
    fg_die("unexpected code read"); return 0;
}
static uint32_t read32(struct mCore *c, uint32_t a) {
    (void)c;
    if (a >= 0x03005048U && a <= 0x03005050U) return pointers[(a-0x03005048U)/4U];
    if (a >= 0x09169228U && a < 0x09169228U + 14U*4U) {
        if (mode == 4) return 0x0203CFFCU;
        if (mode == 5) return 0xFFFFFFFFU;
        if (mode == 6) return 0x0203FFFCU;
        return 0x02029250U + (a-0x09169228U)/4U * 30U*58U;
    }
    fg_die("fixture accessed a non-field PC pool"); return 0;
}
static unsigned fg_call_thumb(struct mCore *c, uint32_t fn, uint32_t a, uint32_t b, uint32_t d, uint32_t e) {
    (void)c;
    if (fn != 0x0804B811U || a || b || d || e) fg_die("non-native bootstrap");
    ++calls;
    if (mode != 9) { pointers[0]=0x020254BCU; pointers[1]=0x02024518U; pointers[2]=0x0202927CU; }
    return 0;
}
''' + capacity + pointer + bootstrap + '''
int capacity(unsigned failure, unsigned claim) {
    mode=failure; struct mCore c={0};
    if (setjmp(trap)) return -1;
    fg_verify_field_capacity(&c, claim); return 0;
}
int bootstrap(unsigned failure, unsigned ready) {
    mode=failure; calls=0; struct mCore c={0};
    pointers[0]=0x020254BCU; pointers[1]=0x02024518U; pointers[2]=ready ? 0x0202927CU : 0;
    if (setjmp(trap)) return -1;
    fg_prepare_fresh_save_pointers(&c); return (int)calls;
}
''')
        cls.lib.capacity.argtypes = cls.lib.bootstrap.argtypes = [ctypes.c_uint] * 2
        cls.lib.capacity.restype = cls.lib.bootstrap.restype = ctypes.c_int

    def test_exact_production_14_box_contract_passes(self):
        self.assertEqual(self.lib.capacity(0, 0x09462B15), 0)
        production = (ROOT / 'overlays/modernization_floette_gift/modernization_floette_gift.c').read_text()
        self.assertIn('FLOETTE_GIFT_BOX_COUNT = 14', production)
        rom = (ROOT / repair.OUTPUT_PATH).read_bytes()
        for offset, opcode in ((0x1462B82, 0x2E1E), (0x1462B8C, 0x2C0E), (0x1462B90, 0x2004)):
            self.assertEqual(struct.unpack_from('<H', rom, offset)[0], opcode)

    def test_changed_count_stride_result_or_claim_entry_is_rejected(self):
        for mode in (1, 2, 3):
            self.assertEqual(self.lib.capacity(mode, 0x09462B15), -1)
        self.assertEqual(self.lib.capacity(0, 0x09462B17), -1)

    def test_ledger_overlap_overflow_and_out_of_ewram_are_rejected(self):
        for mode in (4, 5, 6):
            self.assertEqual(self.lib.capacity(mode, 0x09462B15), -1)

    def test_extra_dpe_pool_really_overlaps_field_ledger(self):
        rom = (ROOT / repair.OUTPUT_PATH).read_bytes()
        box19 = struct.unpack_from('<I', rom, 0x1169228 + 19*4)[0]
        self.assertLess(box19, 0x0203D000)
        self.assertGreater(box19 + 30*58, 0x0203D000)
        main = self.text[self.text.index('int main('):]
        self.assertLess(main.index('uint64_t before_fill'), main.index('    fg_fill_boxes(core);'))
        self.assertIn('filling PC fixture mutated the acquisition ledger', main)
        self.assertIn('clearing PC fixture mutated the acquisition ledger', main)

    def test_missing_storage_pointer_calls_native_initializer_once(self):
        self.assertEqual(self.lib.bootstrap(0, 0), 1)

    def test_valid_save_pointers_are_not_reinitialized(self):
        self.assertEqual(self.lib.bootstrap(0, 1), 0)

    def test_failed_native_initializer_is_not_accepted(self):
        self.assertEqual(self.lib.bootstrap(9, 0), -1)

    def test_load_success_and_every_durability_assertion_remain_required(self):
        reload = self.text.split('fg_phase("fresh-core-reload");', 1)[1]
        self.assertLess(reload.index('fg_prepare_fresh_save_pointers(core);'), reload.index('FG_SAVE_LOAD'))
        self.assertIn('UINT32_C(0x0809984D)', reload)
        for token in ('load_status != 1U', '!fg_has_ring(core)', '!fg_flag(core)',
                      '!fg_collection_bit(core, FG_LEDGER)', '!= FG_SPECIES', '!= FG_LEVEL', 'FG_RESULT_ALREADY'):
            self.assertIn(token, reload)


class RTCSaveFileTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        body = function(FG.read_text(), 'static void fg_initialize_save(')
        cls.lib = compile_probe(cls, '''#include <stdint.h>
#include <stdio.h>
#include <string.h>
#include <time.h>
#include <setjmp.h>
#define FG_SAVE_FILE_SIZE 0x20000U
static jmp_buf trap;
static unsigned bad_clock;
static time_t fixture_time(time_t *unused) { (void)unused; return bad_clock ? (time_t)-1 : (time_t)946684800; }
#define time fixture_time
static void fg_die(const char *s) { (void)s; longjmp(trap, 1); }
''' + body + '''
int initialize(const char *path, unsigned fail_clock) {
    bad_clock=fail_clock;
    if (setjmp(trap)) return -1;
    fg_initialize_save(path); return 0;
}
''')
        cls.lib.initialize.argtypes = [ctypes.c_char_p, ctypes.c_uint]
        cls.lib.initialize.restype = ctypes.c_int

    def test_erased_flash_has_valid_16_byte_rtc_trailer_before_first_boot(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'private.sav'
            self.assertEqual(self.lib.initialize(str(path).encode(), 0), 0)
            data = path.read_bytes()
        self.assertEqual(len(data), 0x20010)
        self.assertEqual(data[:0x20000], b'\xff' * 0x20000)
        self.assertEqual(data[0x20000:0x20008], bytes([0, 1, 1, 6, 0, 0, 0, 0x40]))
        self.assertEqual(struct.unpack_from('<q', data, 0x20008)[0], 946684800)

    def test_invalid_clock_is_not_used_as_rtc_state(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'private.sav'
            self.assertEqual(self.lib.initialize(str(path).encode(), 1), -1)

    def test_invalid_output_directory_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(self.lib.initialize(directory.encode(), 0), -1)


class NativeEvolutionBridgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.parent = (ROOT / repair.PARENT_PATH).read_bytes()
        cls.rom = repair.repair_rom(cls.parent)

    def test_stock_bag_entry_forwards_to_the_modern_native_target(self):
        self.assertEqual(self.parent[0x425B4:0x425BC].hex(), 'f0b557464e464546')
        self.assertEqual(self.rom[0x425B4:0x425BC].hex(), '004b184775b70f09')
        self.assertEqual(struct.unpack_from('<I', self.rom, 0x425B8)[0], 0x090FB775)

    def test_success_call_decodes_to_the_completion_shim(self):
        high, low = struct.unpack_from('<HH', self.rom, 0xCFE8C)
        self.assertEqual((high & 0xF800, low & 0xF800), (0xF000, 0xF800))
        delta = ((high & 0x7FF) << 12) | ((low & 0x7FF) << 1)
        if delta & (1 << 22):
            delta -= 1 << 23
        self.assertEqual(0x080CFE8C + 4 + delta, 0x080425BC)
        self.assertEqual(self.rom[0x425D4:0x425DC], struct.pack('<II', 0x090FB631, 0x0803DBE9))

    def test_native_consumer_guards_reject_every_changed_instruction(self):
        repair.guard_code(self.parent, repair.EVOLUTION_CODE_GUARDS)
        for site, guard in repair.EVOLUTION_CODE_GUARDS.items():
            mutant = bytearray(self.parent)
            mutant[site] ^= 1
            with self.subTest(site=site), self.assertRaises(repair.BoundaryRepairError):
                repair.guard_code(mutant, {site: guard})

    def test_reviewable_arm_source_compiles_to_exact_installed_shim(self):
        source = ROOT / 'overlays/modernization_runtime_boundary_repair/evolution_completion.S'
        compiler = shutil.which('arm-none-eabi-gcc')
        if compiler:
            flags, objcopy = [], shutil.which('arm-none-eabi-objcopy')
        else:
            compiler, objcopy = shutil.which('clang'), shutil.which('llvm-objcopy')
            flags = ['--target=arm-none-eabi']
        self.assertIsNotNone(compiler, 'An ARM compiler is required; this is not a skipped test')
        self.assertIsNotNone(objcopy)
        with tempfile.TemporaryDirectory() as directory:
            obj, binary = Path(directory)/'shim.o', Path(directory)/'shim.bin'
            subprocess.run([compiler, *flags, '-mcpu=arm7tdmi', '-mthumb', '-c', str(source), '-o', str(obj)], check=True, capture_output=True)
            subprocess.run([objcopy, '-O', 'binary', str(obj), str(binary)], check=True, capture_output=True)
            self.assertEqual(binary.read_bytes(), self.rom[0x425BC:0x425DC])

    def test_conditional_cancellation_still_requires_item_and_source_retained(self):
        text = P02.read_text()
        cancel = text.split('struct P02SScene form_cancel =', 1)[1].split('restore_snapshot(core, &field);', 1)[0]
        for token in ('true, "conditional_form_cancel_entry"', 'form_cancel.physical_b',
                      '!= P02S_SPECIES_QUILAVA', '!= P02S_ITEM_SPOOKY_PLATE', '!p02s_moves_equal', '!p02s_hidden'):
            self.assertIn(token, cancel)
        self.assertEqual(hashlib.sha256(self.parent).hexdigest(), repair.PARENT_SHA256)


if __name__ == '__main__':
    unittest.main()
