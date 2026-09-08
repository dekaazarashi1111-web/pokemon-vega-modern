/* P01: 既存ROMの実収集save処理。通常プレイE2Eとは別のdirect-call回帰。 */
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#define BATTLE_CORE_EMBEDDED
#include "mgba_battle_core_smoke.c"
#include "../vendor/vega_acquisition/generated/acquisition_save_layout.h"

enum { P01_BLOCK = 0x0203E400, P01_CALLBACK = 0x0203E600, P01_CONTEXT = 0x0203E700 };

static void p01_fail(void) { fputs("P01_MGBA_ASSERTION_FAILED\n", stderr); exit(1); }
static void p01_require(int condition) { if (!condition) p01_fail(); }
static uint32_t p01_number(const char *s) {
    char *end = NULL;
    unsigned long n = strtoul(s, &end, 0);
    p01_require(s[0] && end && !*end && n <= UINT32_MAX);
    return (uint32_t)n;
}
static uint32_t p01_call(struct mCore *core, uint32_t address, uint32_t a, uint32_t b, uint32_t c) {
    struct CpuState old = capture_cpu_state(core);
    write_register(core, "cpsr", 0xFFU);
    write_register(core, "sp", 0x03007000U);
    write_register(core, "lr", 0x08000001U);
    write_register(core, "r0", a);
    write_register(core, "r1", b);
    write_register(core, "r2", c);
    write_register(core, "r3", 0);
    write_register(core, "pc", address | 1U);
    unsigned count = 0;
    while (((uint32_t)read_register(core, "pc") & ~1U) != 0x08000002U) {
        p01_require(++count < 10000000U);
        core->step(core);
    }
    uint32_t result = (uint32_t)read_register(core, "r0");
    restore_cpu_state(core, &old);
    return result;
}
int main(int argc, char **argv) {
    p01_require(argc == 8);
    char sha[65];
    sha256_file(argv[1], sha);
    p01_require(strlen(argv[2]) == 64 && strcmp(sha, argv[2]) == 0);
    uint32_t migrate = p01_number(argv[3]), finalize = p01_number(argv[4]), validate = p01_number(argv[5]);
    unsigned corrected = p01_number(argv[7]);
    p01_require(corrected <= 1);
    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mCore *core = mCoreFind(argv[1]);
    p01_require(core && core->init(core));
    p01_require(mCoreLoadFile(core, argv[1]));
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    core->reset(core);
    FILE *callback = fopen(argv[6], "rb");
    p01_require(callback != NULL);
    unsigned bytes = 0;
    int byte;
    while ((byte = fgetc(callback)) != EOF) {
        p01_require(bytes < 128);
        write8(core, P01_CALLBACK + bytes++, (uint8_t)byte);
    }
    fclose(callback);
    p01_require(bytes > 0);
    unsigned cases = 0;
    for (unsigned test = 0; test < 2; ++test) {
        unsigned sid = test == 0 ? 649 : 412;
        for (unsigned i = 0; i < sizeof(VegaAcqSaveBlock); ++i) write8(core, P01_BLOCK + i, 0);
        for (unsigned i = 0; i < 8; ++i) write8(core, P01_CONTEXT + i, 0);
        write8(core, P01_CONTEXT, sid & 255U);
        write8(core, P01_CONTEXT + 1, sid >> 8);
        p01_require(p01_call(core, migrate, P01_BLOCK, P01_CALLBACK | 1U, P01_CONTEXT) == 1);
        unsigned expected_sid = corrected ? 649 : 412;
        for (unsigned i = 0; i < VEGA_ACQ_COLLECTION_BYTES; ++i) {
            unsigned expected = sid == expected_sid && i == 386 / 8 ? 1U << (386 % 8) : 0;
            p01_require(read8(core, P01_BLOCK + offsetof(VegaAcqSaveBlock, collection_bits) + i) == expected);
        }
        p01_require(p01_call(core, validate, P01_BLOCK, 0, 0) == 1);
        ++cases;
    }
    uint8_t before[sizeof(VegaAcqSaveBlock)];
    for (unsigned i = 0; i < sizeof(before); ++i) write8(core, P01_BLOCK + i, 0xA5U);
    (void)p01_call(core, finalize, P01_BLOCK, 0, 0);
    p01_require(p01_call(core, validate, P01_BLOCK, 0, 0) == 1);
    for (unsigned i = 0; i < sizeof(before); ++i) before[i] = read8(core, P01_BLOCK + i);
    for (unsigned i = 4; i < 8; ++i) write8(core, P01_CONTEXT + i, 0);
    p01_require(p01_call(core, migrate, P01_BLOCK, P01_CALLBACK | 1U, P01_CONTEXT) == 1);
    for (unsigned i = 0; i < sizeof(before); ++i) p01_require(read8(core, P01_BLOCK + i) == before[i]);
    for (unsigned i = 4; i < 8; ++i) p01_require(read8(core, P01_CONTEXT + i) == 0);
    ++cases;
    p01_require(log_problem_count == 0);
    printf("{\"schema_version\":1,\"cases\":%u,\"corrected\":%s,\"existing_valid_save_unchanged\":true,\"normal_play_e2e\":false}\n", cases, corrected ? "true" : "false");
    core->deinit(core);
    return 0;
}
