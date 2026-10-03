/* Real libmGBA regression: no product ROM, save, or prerecorded PASS data. */
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#if defined(TEST_REGRESSION_HELPER)
#define main bundled_regression_entrypoint
#include "mgba_regression_smoke.c"
#undef main
typedef struct CpuContext SavedContext;
#define capture_context capture_cpu
#define restore_context restore_cpu
#define invoke_probe call_thumb
#else
#define BATTLE_CORE_EMBEDDED
#include "mgba_battle_core_smoke.c"
typedef struct CpuState SavedContext;
#define capture_context capture_cpu_state
#define restore_context restore_cpu_state
#define invoke_probe call_preserving
#endif
#include <mgba/gba/core.h>
#include <mgba-util/vfs.h>

static int exercise_mode(struct mCore *core, uint32_t cpsr)
{
    const uint32_t code = UINT32_C(0x02001000);
    const uint32_t probe = UINT32_C(0x02001100);
    const char *const names[17] = {
        "r0", "r1", "r2", "r3", "r4", "r5", "r6", "r7", "r8",
        "r9", "r10", "r11", "r12", "sp", "lr", "pc", "cpsr",
    };
    /* The next instruction must set r0=17, not the following r0=34. */
    if (cpsr & UINT32_C(0x20)) {
        core->rawWrite16(core, code, -1, UINT16_C(0x2011));
        core->rawWrite16(core, code + 2U, -1, UINT16_C(0x2022));
    } else {
        core->rawWrite32(core, code, -1, UINT32_C(0xE3A00011));
        core->rawWrite32(core, code + 4U, -1, UINT32_C(0xE3A00022));
    }
    core->rawWrite16(core, probe, -1, UINT16_C(0x2055)); /* mov r0,#85 */
    core->rawWrite16(core, probe + 2U, -1, UINT16_C(0x4770)); /* bx lr */
    write_register(core, "cpsr", cpsr);
    for (unsigned index = 0U; index < 13U; ++index)
        write_register(core, names[index], UINT32_C(0x1000) + index);
    write_register(core, "sp", UINT32_C(0x0203F000));
    write_register(core, "lr", UINT32_C(0x08000001));
    write_register(core, "pc", code);
    SavedContext before = capture_context(core);
    if (invoke_probe(core, probe | 1U, 0U, 0U, 0U, 0U) != 85U) {
        fprintf(stderr, "synthetic probe returned the wrong value\n");
        return 1;
    }
    for (unsigned index = 0U; index < 17U; ++index) {
        uint32_t actual = (uint32_t)read_register(core, names[index]);
        uint32_t expected = (uint32_t)before.registers[index];
        if (actual != expected) {
            fprintf(stderr, "CPU_RESTORE_MISMATCH cpsr=%08" PRIx32
                    " register=%s expected=%08" PRIx32 " actual=%08" PRIx32 "\n",
                    cpsr, names[index], expected, actual);
            return 1;
        }
    }
    core->step(core);
    if ((uint32_t)read_register(core, "r0") != 17U) {
        fprintf(stderr, "CPU_RESTORE_SKIPPED_NEXT_INSTRUCTION cpsr=%08" PRIx32 "\n", cpsr);
        return 1;
    }
    printf("CPU_RESTORE_CASE_PASS cpsr=%08" PRIx32 "\n", cpsr);
    return 0;
}

int main(void)
{
    static const uint8_t synthetic_rom[512] = {0};
    struct mCore *core = GBACoreCreate();
    if (core == NULL || !core->init(core))
        return 2;
    struct VFile *rom = VFileMemChunk(synthetic_rom, sizeof(synthetic_rom));
    if (rom == NULL || !core->loadROM(core, rom))
        return 2;
    mCoreInitConfig(core, NULL);
    core->reset(core);
    /* ARM/Thumb in System and IRQ mode, all with IRQs masked. */
    const uint32_t modes[] = {0x9FU, 0xBFU, 0x92U, 0xB2U};
    int status = 0;
    for (unsigned index = 0U; index < 4U; ++index)
        status |= exercise_mode(core, modes[index]);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    if (status == 0)
        puts("CPU_RESTORE_REGRESSION_PASS cases=4");
    return status;
}
