"""通常BPショップの実C構造体と観測ABIを照合するhost回帰。"""
from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BpShopObserverAbiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        compiler = shutil.which("cc")
        if compiler is None:
            raise RuntimeError("BP観測ABI検証にはhost C compilerが必要")
        cls.compiler = compiler
        cls.temp = tempfile.TemporaryDirectory(prefix="bp-shop-observer-")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work = Path(cls.temp.name)
        observer = (ROOT / "tools/mgba_pr16_bp_spending.c").read_text()
        runtime = (ROOT / "overlays/bp_shop_runtime/bp_shop_runtime.c").read_text()
        header = (ROOT / "overlays/bp_shop_runtime/bp_shop_runtime.h").read_text()
        layout = re.search(
            r"typedef struct BpShopVolatileState \{.*?\} BpShopVolatileState;",
            runtime, re.S,
        )
        if layout is None:
            raise AssertionError("実BPショップのvolatile構造体が見つからない")
        defines = "\n".join(line for line in observer.splitlines()
                            if line.startswith("#define BS_"))
        state_defines = "\n".join(line for line in header.splitlines()
                                 if line.startswith("#define VEGA_BP_SHOP_VOLATILE_"))
        start = observer.index("static void bs_wait_menu(")
        stop = observer.index("\nstatic struct BSResult bs_spend(", start)
        cls.program = r'''
#include <stddef.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdlib.h>
#include <string.h>
typedef uint8_t u8;
typedef uint16_t u16;
''' + state_defines + "\n" + layout.group() + "\n" + defines + r'''
_Static_assert(BS_STATE == VEGA_BP_SHOP_VOLATILE_STATE_ADDRESS, "state address");
_Static_assert(sizeof(BpShopVolatileState) == VEGA_BP_SHOP_VOLATILE_STATE_BYTES, "state size");
#define BIND(observed, field) _Static_assert((observed) - BS_STATE == offsetof(BpShopVolatileState, field), #field)
BIND(BS_ELIGIBLE_BASE, eligible);
BIND(BS_LAST_RESULT, last_result);
BIND(BS_LAST_INDEX, last_catalog_index);
BIND(BS_ELIGIBLE_COUNT, eligible_count);
BIND(BS_PAGE, page);
BIND(BS_WINDOW_ID, window_id);
struct mCore { unsigned unused; };
static BpShopVolatileState state;
static unsigned frames;
static unsigned read8(struct mCore *c, unsigned address) {
    (void)c;
    if(address < BS_STATE || address >= BS_STATE + sizeof(state)) exit(90);
    return ((const unsigned char *)&state)[address - BS_STATE];
}
static unsigned read16(struct mCore *c, unsigned address) {
    return read8(c, address) | (read8(c, address + 1U) << 8);
}
static void b_frame(struct mCore *c, unsigned keys) {
    (void)c; if(keys) exit(91); ++frames;
}
static void b_frames_run(struct mCore *c, unsigned keys, unsigned count) {
    while(count--) b_frame(c, keys);
}
static void bs_trace(struct mCore *c, const char *label) { (void)c; (void)label; }
static void bp_require(struct mCore *c, bool valid, const char *message) {
    (void)c; (void)message;
    if(!valid) exit(frames == 2400U ? 42 : 92);
}
''' + observer[start:stop] + r'''
int main(int argc, char **argv) {
    if(argc != 2) return 93;
    struct mCore core = {0};
    state.last_result = BS_RESULT_BUSY;
    state.last_catalog_index = 0xFFFFU;
    state.eligible_count = 10U;
    state.eligible[0] = BS_CATALOG_INDEX;
    state.page = 0U;
    state.window_id = 1U;
    switch(atoi(argv[1])) {
        case 0: break;
        case 1: state.last_result = BS_RESULT_SUCCESS; break;
        case 2: state.last_catalog_index = BS_CATALOG_INDEX; break;
        case 3: state.eligible_count = 0U; break;
        case 4: state.eligible[0] = BS_CATALOG_INDEX + 1U; break;
        case 5: state.page = 1U; break;
        case 6: state.window_id = 0xFFU; break;
        default: return 94;
    }
    bs_wait_menu(&core);
    return frames == 60U ? 0 : 95;
}
'''
        cls.source = cls.work / "observer.c"
        cls.source.write_text(cls.program)
        cls.binary = cls.work / "observer"
        completed = subprocess.run(
            [compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
             str(cls.source), "-o", str(cls.binary)],
            capture_output=True, text=True, timeout=30, check=False,
        )
        if completed.returncode:
            raise AssertionError(completed.stderr)

    def test_actual_eighteen_entry_bp_menu_is_observed(self) -> None:
        result = subprocess.run([str(self.binary), "0"], capture_output=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_each_incomplete_menu_condition_fails_at_bounded_timeout(self) -> None:
        for scenario in range(1, 7):
            with self.subTest(scenario=scenario):
                result = subprocess.run([str(self.binary), str(scenario)],
                                        capture_output=True, timeout=5)
                self.assertEqual(result.returncode, 42, result.stderr)

    def test_mega_shop_45_entry_offsets_are_rejected(self) -> None:
        # 旧run34933733445の誤った45品目ABIを再導入するとcompile時点で拒否。
        mutated = self.program
        for old, new in (("0x24U", "0x5AU"), ("0x26U", "0x5CU"),
                         ("0x28U", "0x5EU"), ("0x29U", "0x5FU"),
                         ("0x2AU", "0x60U")):
            self.assertIn("BS_STATE + " + old, mutated)
            mutated = mutated.replace("BS_STATE + " + old, "BS_STATE + " + new)
        source = self.work / "wrong-mega-layout.c"
        source.write_text(mutated)
        result = subprocess.run([self.compiler, "-std=c11", "-fsyntax-only", str(source)],
                                capture_output=True, text=True, timeout=30)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("static assertion failed", result.stderr)
