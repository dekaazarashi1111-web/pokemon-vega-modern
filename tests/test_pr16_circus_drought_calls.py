"""定数callback消失・実関数ABI・相対path証拠・重複実行防止の回帰。"""
import copy
import importlib.util
import json
from pathlib import Path
import re
import struct
import subprocess
import sys
import tempfile
import unittest
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import pr16_circus_drought_calls as t


class DroughtCallsTests(unittest.TestCase):
    def source(self):
        return '#define NATIVE(a) ((void (*)(void))(uintptr_t)(a))\n__attribute__((used, noinline, externally_visible))\nvoid entry(void) { apply(' + t.OLD_ARGS + '); }\n'

    def test_exact_source_repair_and_three_symbol_boundaries(self):
        result = t.repair(self.source())
        self.assertEqual(result.count('__attribute__((noinline)) static void'), 3)
        self.assertNotIn(t.OLD_ARGS, result)
        self.assertIn(t.NEW_ARGS, result)
        self.assertEqual(result.count('__attribute__((used, noinline, externally_visible))'), 1)

    def test_repair_rejects_already_applied_and_different_inputs(self):
        for text in (t.repair(self.source()), self.source() + self.source(), self.source().replace('AD09', 'AD0B')):
            with self.subTest(text=text[:40]), self.assertRaises(ValueError):
                t.repair(text)

    def target(self):
        text = '''09ff6b3c <CircusDroughtInitAll>:
  9ff6b3c: d001 beq.n 9ff6b44
  9ff6b3e: 7003 strb r3, [r0, #0]
  9ff6b40: bd10 pop {r4, pc}
09ff6b44 <DroughtOriginal>:
  9ff6b44: 4718 bx r3
09ff6b48 <DroughtInitVars>:
  9ff6b48: 4718 bx r3
09ff6b4c <DroughtStep>:
  9ff6b4c: 4718 bx r3
'''
        return struct.pack('<III', 0x0807AD09, 0x0807ACD5, 0x0807AD39), text

    def test_target_requires_condition_cursor_store_return_and_three_natives(self):
        raw, text = self.target()
        self.assertEqual(t.verify_target(raw, text)['native_symbol_boundaries'], 3)
        for token in ('beq.n', 'strb', 'pop', 'DroughtOriginal', 'DroughtInitVars', 'DroughtStep'):
            with self.subTest(token=token), self.assertRaises(ValueError):
                t.verify_target(raw, text.replace(token, 'invalid'))
        for i in range(3):
            with self.subTest(address=i), self.assertRaises(ValueError):
                t.verify_target(raw[:4*i] + b'\0'*4 + raw[4*i+4:], text)

    def test_entry_not_satisfied_by_instructions_in_other_function(self):
        raw, text = self.target()
        with self.assertRaises(ValueError):
            t.verify_target(raw, text.replace('  9ff6b3e: 7003 strb r3, [r0, #0]\n', '') + '  9ff6b50: 7003 strb r3, [r0, #0]\n')

    def test_recorded_failed_arm_entry_is_rejected_without_relink(self):
        path = ROOT / 'evidence/pr16_circus_drought_calls/35434591898/compile-1/disassembly.txt'
        if not path.exists():
            self.fail('prepare must export original ARM before host tests')
        raw, _ = self.target()
        with self.assertRaises(ValueError):
            t.verify_target(raw, path.read_text())

    def test_relative_excerpt_preserves_content_and_original_identity(self):
        root = Path('/temporary/workspace')
        raw = b'/temporary/workspace/overlays/a.c:22:5:f\t64\tstatic\n'
        normalized = t.relative_text(raw, root)
        self.assertEqual(normalized, b'overlays/a.c:22:5:f\t64\tstatic\n')
        self.assertNotEqual(t.identity(raw), t.identity(normalized))
        self.assertEqual(t.relative_text(normalized, root), normalized)
        self.assertEqual(t.relative_text(b'native addresses unchanged\n', root), b'native addresses unchanged\n')

    def test_private_machine_path_guard_accepts_relative_excerpt_only(self):
        from guard_private_files import document_user_path_lines
        # 絶対pathを検出するguard自体は変更しない。
        root = Path('/' + 'home' + '/runner/work/project/project')
        raw = (str(root) + '/overlays/a.c:22:5:f\t64\tstatic\n').encode()
        self.assertTrue(document_user_path_lines(raw))
        self.assertFalse(document_user_path_lines(t.relative_text(raw, root)))

    def test_non_utf8_and_nul_evidence_rejected(self):
        for raw in (b'\xff', b'one\0two'):
            with self.subTest(raw=raw), self.assertRaises((UnicodeError, ValueError)):
                t.relative_text(raw, ROOT)

    def events(self):
        p = ROOT / 'evidence/pr16_circus_drought_calls/35434591898/native/circus-continuous-30-save.stderr'
        return p.read_bytes()

    def test_original_seventeen_outcomes_are_not_seventeen_settlements(self):
        result = t.failed_events(self.events())
        self.assertEqual((result['real_win_outcomes'], result['settled_wins'], result['bp']), (17, 16, 45))
        self.assertFalse(result['saved'] or result['reloaded'] or result['native_return_verified'])
        self.assertEqual(result['original_conclusion'], 'failure')

    def test_changed_old_outcome_or_save_is_rejected(self):
        rows = [json.loads(line.split(b' ', 1)[1]) for line in self.events().splitlines() if line.startswith(b'CIRCUS_CONTINUOUS ')]
        for index, key, value in ((78, 'outcome', 2), (79, 'label', 'saved'), (79, 'bp', 48), (5, 'label', 'reloaded')):
            changed = copy.deepcopy(rows)
            changed[index][key] = value
            with self.subTest(index=index, key=key), self.assertRaises(ValueError):
                t.failed_events(b'\n'.join(b'CIRCUS_CONTINUOUS ' + json.dumps(r).encode() for r in changed))

    def test_gcc_reduced_callback_keeps_real_symbol_and_return(self):
        # native addressを実行せず、同じ最適化条件の生成assemblyだけ検査。
        # 旧inline形のcompiler不具合が将来直っても、修正版の必要条件を維持する。
        source = '''#include <stdint.h>
static inline void apply(int b, void (*original)(void), void (*init)(void)) {
    if (!b) { original(); return; } init();
}
__attribute__((noinline)) static void original(void) { ((void (*)(void))(uintptr_t)0x0807AD09u)(); }
__attribute__((noinline)) static void init(void) { ((void (*)(void))(uintptr_t)0x0807ACD5u)(); }
void boundary(int b) { apply(b, original, init); }
'''
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder); (p/'test.c').write_text(source)
            subprocess.run(['gcc', '-std=c11', '-Os', '-ffreestanding', '-fno-builtin', '-Wall', '-Wextra', '-Werror', '-S', str(p/'test.c'), '-o', str(p/'test.s')], check=True, capture_output=True)
            asm = (p/'test.s').read_text()
        body = asm.split('boundary:', 1)[1].split('.size', 1)[0]
        self.assertIn('original', body)
        self.assertIn('init', body)
        self.assertRegex(body, r'\bj(?:e|ne|z|nz)\b')

    def test_runtime_source_uses_symbol_callbacks_not_integer_arguments(self):
        source = (ROOT / t.SOURCE).read_text()
        self.assertNotIn(t.OLD_ARGS, source)
        self.assertIn(t.NEW_ARGS, source)
        self.assertEqual(source.count('__attribute__((noinline)) static void Drought'), 3)
        for token in ('VegaSaveValidate(', 'CIRCUS_DROUGHT_ARMED'):
            self.assertIn(token, source)

    def test_repeated_configure_preserves_original_compiler_without_recursive_wrapper(self):
        d, b = t.configure()
        original = d._calls_original_compile
        d2, b2 = t.configure()
        self.assertIs(d, d2)
        self.assertIs(d._calls_original_compile, original)
        self.assertIsNot(d.compile_bridge, original)
        self.assertEqual(d.SELF, t.SELF)
        self.assertIn('scripts/pr16_circus_drought.py', d.FILES)
        self.assertIn(t.SOURCE, d.FILES)
        self.assertEqual(b2.SELF, t.SELF)


if __name__ == '__main__':
    unittest.main()
