"""Apply pinned runner-only input/compact-PC fixes; the product is immutable."""
from pathlib import Path
import hashlib
import importlib.util
import json
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
P02 = 'tools/mgba_modernization_p02_stage71_acceptance_smoke.c'
FG = 'overlays/modernization_floette_gift/mgba_modernization_floette_gift_smoke.c'
TEST = 'tests/test_modernization_stage79_runtime_boundaries.py'
PREIMAGES = {P02: 'c4d4183d8e422900f9323d45e1fb0e8531b1d0f28f2d4355739973b81512547a',
             FG: '35306047c3f052b13761edfbab1ae6bf7f7220b15d0d31fa4ec69faaed8fd8eb'}
for relative, digest in PREIMAGES.items():
    assert hashlib.sha256((ROOT / relative).read_bytes()).hexdigest() == digest, relative


def edit(path, old, new):
    target = ROOT / path
    text = target.read_text()
    assert text.count(old) == 1, (path, old, text.count(old))
    target.write_text(text.replace(old, new, 1))


edit(P02, '''        trace->physical_b = true;
        return QOL_KEY_B;''', '''        /* Cancellation is edge-triggered after the animation's input gate.
         * Release between presses, so an early B does not consume the edge. */
        if (frame % 120U < 2U) {
            trace->physical_b = true;
            return QOL_KEY_B;
        }
        return 0U;''')
edit(P02, '''    if (!cancel && species == target) {''', '''    /* Returning from Bag leaves the Start menu open on the field callback.
     * Close all three menus before optional-move dialog input can reopen Bag. */
    if (callback == P02S_CB2_PARTY || callback == P02S_CB2_BAG
        || callback == P02S_CB2_FIELD)
        return frame % 120U < 2U ? QOL_KEY_B : 0U;
    if (!cancel && species == target) {''')
edit(P02, '''    if (callback == P02S_CB2_PARTY || callback == P02S_CB2_BAG)
        return frame % 120U < 2U ? QOL_KEY_B : 0U;
''', '')
edit(FG, '#define FG_BOX_COUNT UINT32_C(14)', '''/* The linked DPE bounds check accepts box IDs 0..24, not vanilla 0..13. */
#define FG_BOX_COUNT UINT32_C(25)
#define FG_SET_BOX_MON UINT32_C(0x09123D51)''')
old = (ROOT / FG).read_text().split('static void fg_fill_boxes(struct mCore *core)\n',1)[1].split('static void fg_verify_map(',1)[0]
new = '''{
    fg_create_fixture_mon(core);
    uint32_t experience = fg_call_thumb(
        core, FG_GET_MON_DATA, FG_SCRATCH, 25U, 0U, 0U);
    for (uint32_t box = 0U; box < FG_BOX_COUNT; ++box) {
        for (uint32_t slot = 0U; slot < FG_BOX_CAPACITY; ++slot) {
            /* GetBoxedMonPtr returns the disposable 80-byte expansion, not
             * the 58-byte persistent slot. Use the production compressor. */
            (void)fg_call_thumb(core, FG_SET_BOX_MON, box, slot, FG_SCRATCH, 0U);
            if (fg_call_thumb(core, fg_get_box_mon_data,
                              box, slot, 11U, 0U) != 25U)
                fg_die("DPE SetBoxMonAt fixture write failed");
        }
    }
    /* Check all 750 slots after the last write, catching storage aliasing and
     * incomplete fixtures before exercising the real full-capacity rejection. */
    for (uint32_t box = 0U; box < FG_BOX_COUNT; ++box)
        for (uint32_t slot = 0U; slot < FG_BOX_CAPACITY; ++slot)
            if (fg_call_thumb(core, fg_get_box_mon_data,
                              box, slot, 11U, 0U) != 25U
                || fg_call_thumb(core, fg_get_box_mon_data,
                                 box, slot, 25U, 0U) != experience)
                fg_die("DPE full-capacity fixture readback failed");
}

'''
edit(FG, old, new)
rom = (ROOT / 'build/stages/80_modernization_runtime_boundary_repair.gba').read_bytes()
assert hashlib.sha256(rom).hexdigest() == '6570b82fc062cf163fa66a6d821fea6563021e5a9ca6f26efd583bae71623442'
# Pin the complete native setter, including its 25x30 bounds and compact table.
code = rom[0x1123D50:0x1123D90]
assert code.hex() == '70b504000e00150090b0182801d81d2901d910b070bd10000021ddf7dff9280001a9fff75dff054ba400e0583a2373433a22c01801a976f744f8eae728921609'
array = ', '.join(f'0x{byte:02X}' for byte in code)
guard = '''static void fg_verify_storage_abi(struct mCore *core)
{
    static const uint8_t expected[] = {''' + array + '''};
    _Static_assert(FG_BOX_COUNT == 25U && FG_BOX_CAPACITY == 30U,
                   "linked compact PC dimensions changed");
    for (uint32_t index = 0U; index < sizeof(expected); ++index)
        if (read8(core, (FG_SET_BOX_MON & ~1U) + index) != expected[index])
            fg_die("DPE SetBoxMonAt ABI mismatch");
}

'''
edit(FG, 'static void fg_clear_boxes(struct mCore *core)\n', guard + 'static void fg_clear_boxes(struct mCore *core)\n')
edit(FG, '    fg_clear_boxes(core);', '    fg_verify_storage_abi(core);\n    fg_clear_boxes(core);')
regressions = (ROOT / '.github/repairs/stage79-harness-regressions.py').read_text()
edit(TEST, "if __name__ == '__main__':\n    unittest.main()", regressions + "\n\nif __name__ == '__main__':\n    unittest.main()")
configpath = ROOT / 'config/modernization_stage79_cumulative_mgba.json'
config = json.loads(configpath.read_text())
for domain in config['domains']:
    for record in [domain['runner'], *domain.get('dependencies', [])]:
        if record['path'] in PREIMAGES:
            raw = (ROOT / record['path']).read_bytes()
            record.update(size=len(raw), sha256=hashlib.sha256(raw).hexdigest())
configpath.write_text(json.dumps(config, ensure_ascii=False, sort_keys=True, indent=2)+'\n')
spec = importlib.util.spec_from_file_location('stage79_harness_fixed', ROOT / 'scripts/run_modernization_stage79_cumulative_mgba.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
assert module.prepare()['status'] == 'READY_NOT_RUN'
assert (ROOT / config['runtime_candidate']['rom']['path']).read_bytes() == rom
print('P02 controller edges, field-menu exit and 25x30 native PC fixtures materialized; product unchanged')
