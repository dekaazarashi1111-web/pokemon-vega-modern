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
            'static uint16_t p02s_scene_key(', 1)[1].split('static struct P02SScene p02s_run_item_scene(', 1)[0]
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
        if (mode == 2U && calls == 750U) slots[0][0] = 0U;
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
    if (calls != 750U || reads != 1500U || exps != 750U) return -2;
    for (unsigned b = 0; b < 25; ++b) for (unsigned p = 0; p < 30; ++p) if (slots[b][p] != 25U) return -3;
    if (clear_after) {
        fg_clear_boxes(&core);
        if (zeros != 750U) return -4;
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

    def test_all_750_slots_are_written_with_native_compressor_and_rechecked(self):
        self.assertEqual(self.exercise(0, 0), 0)

    def test_all_25_boxes_are_cleared_not_only_vanilla_14(self):
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
        self.assertIn('fg_verify_storage_abi(core);\n    fg_clear_boxes(core);', self.text)
