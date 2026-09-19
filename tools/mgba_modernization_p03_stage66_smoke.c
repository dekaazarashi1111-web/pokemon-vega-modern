/*
 * P03 Stage66 bulk learnset representative direct-consumer gate.
 *
 * The read-only process validates first/middle/last corrected targets plus the
 * Caterpie correction sentinel through the linked level-up and TM/HM consumers.
 * It is bounded coverage, not scheduler E2E or full-P03 acceptance.
 */
#define BATTLE_CORE_EMBEDDED
#define BATTLE_CORE_ISOLATE_HOST_CALL_STACK 1
#define BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS 0x0203D000U
#define BATTLE_CORE_HOST_STACK_TOP_ADDRESS 0x0203E000U
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#include "mgba_battle_core_smoke.c"
#pragma GCC diagnostic pop

enum {
    P03_GET_LEVEL_UP_SYMBOL = 0x091142A0U,
    P03_GET_LEVEL_UP_THUMB = P03_GET_LEVEL_UP_SYMBOL | 1U,
    P03_CAN_LEARN_TMHM_SYMBOL = 0x09110184U,
    P03_CAN_LEARN_TMHM_THUMB = P03_CAN_LEARN_TMHM_SYMBOL | 1U,
    P03_LEVEL_ROOT_SITE = 0x0804346CU,
    P03_LEVEL_LITERAL_SITE = 0x09FDA1F8U,
    P03_LEVEL_ROOT_EXPECTED = 0x093A4CACU,
    P03_TM_COMPATIBILITY_ROOT_SITE = 0x080432B4U,
    P03_TM_COMPATIBILITY_ROOT_EXPECTED = 0x0944BD00U,
    P03_TM_CATALOG_ROOT_SITE = 0x081263D8U,
    P03_TM_CATALOG_ROOT_EXPECTED = 0x0944BB80U,
    P03_LEVEL_SCRATCH = 0x0203C000U,
    P03_COMPATIBILITY_STRIDE = 16U,
    P03_SAMPLE_COUNT = 4U,
    P03_MAX_LEVEL_ROWS = 15U,
};

struct P03Sample {
    const char *role;
    uint16_t species;
    uint32_t level_pointer;
    uint8_t level_count;
    uint16_t moves[P03_MAX_LEVEL_ROWS];
    uint8_t levels[P03_MAX_LEVEL_ROWS];
    uint8_t compatibility[P03_COMPATIBILITY_STRIDE];
    uint8_t positive_slot;
    uint16_t positive_move;
    uint8_t negative_slot;
};

static const struct P03Sample p03_samples[P03_SAMPLE_COUNT] = {
    {
        "FIRST_CORRECTED_TARGET", 10U, 0x09FDA248U, 13U,
        {45U, 64U, 116U, 98U, 17U, 104U, 332U, 708U, 97U, 373U,
         283U, 383U, 179U, 0U, 0U},
        {1U, 1U, 5U, 9U, 13U, 17U, 21U, 25U, 29U, 33U, 37U, 41U,
         45U, 0U, 0U},
        {0x00U, 0x10U, 0x00U, 0x00U, 0x00U, 0x00U, 0x1CU, 0x83U,
         0x00U, 0x00U, 0x00U, 0x00U, 0x00U, 0x00U, 0x02U, 0x02U},
        121U, 19U, 0U,
    },
    {
        "MIDDLE_CORRECTED_TARGET", 858U, 0x09FE14BAU, 15U,
        {10U, 43U, 210U, 232U, 259U, 184U, 566U, 319U, 163U, 370U,
         334U, 575U, 405U, 14U, 12U},
        {1U, 1U, 5U, 10U, 15U, 20U, 25U, 30U, 35U, 40U, 45U, 50U,
         55U, 60U, 65U},
        {0x13U, 0x14U, 0xA1U, 0x40U, 0x00U, 0x00U, 0x3CU, 0x15U,
         0x4AU, 0x18U, 0x04U, 0x01U, 0x00U, 0x20U, 0x46U, 0x00U},
        0U, 14U, 2U,
    },
    {
        "LAST_CORRECTED_TARGET", 1620U, 0x09FE8CF2U, 13U,
        {123U, 139U, 262U, 310U, 110U, 194U, 313U, 631U, 247U, 1056U,
         92U, 387U, 105U, 0U, 0U},
        {1U, 1U, 1U, 1U, 8U, 16U, 24U, 32U, 40U, 48U, 56U, 64U,
         72U, 0U, 0U},
        {0x00U, 0x10U, 0x00U, 0x20U, 0x08U, 0x00U, 0x1CU, 0x00U,
         0x20U, 0x28U, 0x80U, 0x00U, 0x04U, 0x20U, 0x40U, 0x00U},
        51U, 156U, 0U,
    },
    {
        "CATERPIE_CORRECTION_SENTINEL", 649U, 0x09FDF33CU, 3U,
        {33U, 81U, 535U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U,
         0U, 0U},
        {1U, 1U, 9U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U,
         0U},
        {0x00U, 0x00U, 0x00U, 0x00U, 0x00U, 0x00U, 0x00U, 0x00U,
         0x00U, 0x00U, 0x00U, 0x00U, 0x00U, 0x00U, 0x10U, 0x00U},
        116U, 489U, 0U,
    },
};

struct P03Observation {
    struct CallObservation level;
    struct CallObservation positive;
    struct CallObservation negative;
};

static void p03_die(const char *message)
{
    fprintf(stderr, "mgba-modernization-p03-stage66: %s\n", message);
    exit(1);
}

static uint16_t p03_read_packed_u16(struct mCore *core, uint32_t address)
{
    return (uint16_t)(read8(core, address)
        | ((uint16_t)read8(core, address + 1U) << 8U));
}

static bool p03_bit(struct mCore *core, uint32_t row, unsigned slot)
{
    return (read8(core, row + slot / 8U) & (1U << (slot % 8U))) != 0U;
}

int main(int argc, char **argv)
{
    if (argc != 3) {
        fprintf(stderr, "usage: %s ROM EXPECTED_ROM_SHA256\n", argv[0]);
        return 2;
    }
    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strlen(argv[2]) != 64U || strcmp(rom_sha256, argv[2]) != 0)
        p03_die("ROM SHA-256 mismatch");

    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {
        .sample = NULL,
        .unixTime = fixed_unix_time,
        .serialize = NULL,
        .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) p03_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1])) p03_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);

    uint32_t level_root = read32(core, P03_LEVEL_ROOT_SITE);
    uint32_t level_literal = read32(core, P03_LEVEL_LITERAL_SITE);
    uint32_t compatibility_root = read32(core, P03_TM_COMPATIBILITY_ROOT_SITE);
    uint32_t catalog_root = read32(core, P03_TM_CATALOG_ROOT_SITE);
    if (level_root != P03_LEVEL_ROOT_EXPECTED || level_literal != level_root)
        p03_die("level-up root/literal mismatch");
    if (compatibility_root != P03_TM_COMPATIBILITY_ROOT_EXPECTED)
        p03_die("TM compatibility root mismatch");
    if (catalog_root != P03_TM_CATALOG_ROOT_EXPECTED)
        p03_die("TM catalog root mismatch");

    struct P03Observation observations[P03_SAMPLE_COUNT];
    memset(observations, 0, sizeof(observations));
    for (unsigned sample_index = 0U; sample_index < P03_SAMPLE_COUNT; ++sample_index) {
        const struct P03Sample *sample = &p03_samples[sample_index];
        uint32_t level_pointer = read32(core, level_root + sample->species * 4U);
        if (level_pointer != sample->level_pointer)
            p03_die("representative level-up pointer mismatch");
        for (unsigned row = 0U; row < sample->level_count; ++row) {
            uint32_t address = level_pointer + row * 3U;
            if (p03_read_packed_u16(core, address) != sample->moves[row]
                || read8(core, address + 2U) != sample->levels[row])
                p03_die("serialized representative level-up row mismatch");
        }
        uint32_t terminator = level_pointer + sample->level_count * 3U;
        if (p03_read_packed_u16(core, terminator) != 0U
            || read8(core, terminator + 2U) != 0xFFU)
            p03_die("representative level-up terminator mismatch");

        for (unsigned row = 0U; row < P03_MAX_LEVEL_ROWS + 2U; ++row)
            write16(core, P03_LEVEL_SCRATCH + row * 2U, 0xDEADU);
        observations[sample_index].level = call_bounded(
            core, P03_GET_LEVEL_UP_THUMB,
            sample->species, P03_LEVEL_SCRATCH, 0U, 0U);
        if (observations[sample_index].level.result != sample->level_count)
            p03_die("GetLevelUpMovesBySpecies count mismatch");
        for (unsigned row = 0U; row < sample->level_count; ++row) {
            if (read16(core, P03_LEVEL_SCRATCH + row * 2U) != sample->moves[row])
                p03_die("GetLevelUpMovesBySpecies output mismatch");
        }

        uint32_t compatibility_row = compatibility_root
            + sample->species * P03_COMPATIBILITY_STRIDE;
        for (unsigned byte = 0U; byte < P03_COMPATIBILITY_STRIDE; ++byte) {
            if (read8(core, compatibility_row + byte) != sample->compatibility[byte])
                p03_die("representative TM replacement bitset mismatch");
        }
        if (read16(core, catalog_root + sample->positive_slot * 2U)
            != sample->positive_move)
            p03_die("representative positive runtime slot catalog mismatch");
        if (!p03_bit(core, compatibility_row, sample->positive_slot)
            || p03_bit(core, compatibility_row, sample->negative_slot))
            p03_die("representative positive/negative TM bit mismatch");

        create_mon(core, ADDR_PLAYER_PARTY, sample->species, 5U);
        observations[sample_index].positive = call_bounded(
            core, P03_CAN_LEARN_TMHM_THUMB,
            ADDR_PLAYER_PARTY, sample->positive_slot, 0U, 0U);
        observations[sample_index].negative = call_bounded(
            core, P03_CAN_LEARN_TMHM_THUMB,
            ADDR_PLAYER_PARTY, sample->negative_slot, 0U, 0U);
        if (observations[sample_index].positive.result != 1U
            || observations[sample_index].negative.result != 0U)
            p03_die("CanMonLearnTMHM positive/negative result mismatch");
        if (!observations[sample_index].level.payload_pc_seen
            || !observations[sample_index].positive.payload_pc_seen
            || !observations[sample_index].negative.payload_pc_seen)
            p03_die("linked consumer payload PC was not observed");
        if (observations[sample_index].level.instructions == 0U
            || observations[sample_index].positive.instructions == 0U
            || observations[sample_index].negative.instructions == 0U)
            p03_die("direct-call instruction count is zero");
    }
    if (log_problem_count != 0U)
        p03_die("mGBA warned/errored during direct consumer calls");

    printf(
        "{\"schema_version\":1,\"status\":\"PASS\","
        "\"classification\":\"REAL_CONSUMER_DIRECT_CALL_BOUNDED\","
        "\"rom_sha256\":\"%s\",\"read_only\":true,"
        "\"roots\":{\"level_up\":\"0x%08" PRIX32 "\","
        "\"level_literal\":\"0x%08" PRIX32 "\","
        "\"tm_compatibility\":\"0x%08" PRIX32 "\","
        "\"tm_catalog\":\"0x%08" PRIX32 "\"},\"samples\":[",
        rom_sha256, level_root, level_literal, compatibility_root, catalog_root);
    for (unsigned sample_index = 0U; sample_index < P03_SAMPLE_COUNT; ++sample_index) {
        const struct P03Sample *sample = &p03_samples[sample_index];
        const struct P03Observation *observation = &observations[sample_index];
        if (sample_index != 0U) printf(",");
        printf(
            "{\"role\":\"%s\",\"species_id\":%u,"
            "\"level_pointer\":\"0x%08" PRIX32 "\","
            "\"level_count\":%u,\"level_rows\":[",
            sample->role, sample->species, sample->level_pointer,
            sample->level_count);
        for (unsigned row = 0U; row < sample->level_count; ++row) {
            if (row != 0U) printf(",");
            printf("[%u,%u]", sample->moves[row], sample->levels[row]);
        }
        printf(
            "],\"level_instructions\":%" PRIu32 ","
            "\"positive_machine_slot\":%u,\"positive_machine_move\":%u,"
            "\"positive_result\":%" PRIu32 ","
            "\"positive_instructions\":%" PRIu32 ","
            "\"negative_machine_slot\":%u,\"negative_result\":%" PRIu32 ","
            "\"negative_instructions\":%" PRIu32 "}",
            observation->level.instructions,
            sample->positive_slot, sample->positive_move,
            observation->positive.result, observation->positive.instructions,
            sample->negative_slot, observation->negative.result,
            observation->negative.instructions);
    }
    printf(
        "],\"symbols\":{\"level_up\":\"0x%08" PRIX32 "\","
        "\"level_up_thumb\":\"0x%08" PRIX32 "\","
        "\"machine\":\"0x%08" PRIX32 "\","
        "\"machine_thumb\":\"0x%08" PRIX32 "\"},"
        "\"payload_pc_seen\":true,\"warnings_errors\":0,"
        "\"scheduler_e2e\":false,\"full_p03_acceptance\":false,"
        "\"artifacts_written\":[]}\n",
        (uint32_t)P03_GET_LEVEL_UP_SYMBOL,
        (uint32_t)P03_GET_LEVEL_UP_THUMB,
        (uint32_t)P03_CAN_LEARN_TMHM_SYMBOL,
        (uint32_t)P03_CAN_LEARN_TMHM_THUMB);

    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
