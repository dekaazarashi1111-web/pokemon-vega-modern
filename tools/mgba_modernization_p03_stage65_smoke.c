/*
 * P03 Stage65 Caterpie representative learnset direct-consumer gate.
 *
 * This read-only libmGBA process calls the linked level-up and TM/HM
 * consumers and also reads their actual roots/rows.  It is deliberately a
 * bounded lookup gate, not scheduler E2E and not full-P03 acceptance.
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
    P03_LEVEL_SPECIES_POINTER_EXPECTED = 0x09FDA23CU,
    P03_TM_COMPATIBILITY_ROOT_SITE = 0x080432B4U,
    P03_TM_COMPATIBILITY_ROOT_EXPECTED = 0x0944BD00U,
    P03_TM_CATALOG_ROOT_SITE = 0x081263D8U,
    P03_TM_CATALOG_ROOT_EXPECTED = 0x0944BB80U,
    P03_LEVEL_SCRATCH = 0x0203C000U,
    P03_CATERPIE = 649U,
    P03_MOVE_TACKLE = 33U,
    P03_MOVE_STRING_SHOT = 81U,
    P03_MOVE_BUG_BITE = 535U,
    P03_MOVE_ELECTROWEB = 489U,
    P03_TM_SLOT_ELECTROWEB = 116U,
    P03_PARENT_TM_SLOT_44 = 44U,
    P03_PARENT_TM_SLOT_63 = 63U,
    P03_COMPATIBILITY_STRIDE = 16U,
};

static void p03_die(const char *message)
{
    fprintf(stderr, "mgba-modernization-p03-stage65: %s\n", message);
    exit(1);
}

static bool p03_bit(struct mCore *core, uint32_t row, unsigned slot)
{
    return (read8(core, row + slot / 8U) & (1U << (slot % 8U))) != 0U;
}

static uint16_t p03_read_packed_u16(struct mCore *core, uint32_t address)
{
    /* Level rows have a 3-byte stride, so every second U16 is unaligned. */
    return (uint16_t)(read8(core, address)
        | ((uint16_t)read8(core, address + 1U) << 8U));
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
    uint32_t level_pointer = read32(core, level_root + P03_CATERPIE * 4U);
    if (level_root != P03_LEVEL_ROOT_EXPECTED || level_literal != level_root)
        p03_die("level-up root/literal mismatch");
    if (level_pointer != P03_LEVEL_SPECIES_POINTER_EXPECTED)
        p03_die("Caterpie level-up pointer mismatch");
    const uint16_t expected_moves[3] = {
        P03_MOVE_TACKLE, P03_MOVE_STRING_SHOT, P03_MOVE_BUG_BITE,
    };
    const uint8_t expected_levels[3] = {1U, 1U, 9U};
    for (unsigned row = 0U; row < 3U; ++row) {
        uint32_t address = level_pointer + row * 3U;
        if (p03_read_packed_u16(core, address) != expected_moves[row]
            || read8(core, address + 2U) != expected_levels[row])
            p03_die("serialized Caterpie level-up row mismatch");
    }
    if (p03_read_packed_u16(core, level_pointer + 9U) != 0U
        || read8(core, level_pointer + 11U) != 0xFFU)
        p03_die("Caterpie level-up terminator mismatch");

    for (unsigned slot = 0U; slot < 8U; ++slot)
        write16(core, P03_LEVEL_SCRATCH + slot * 2U, 0xDEADU);
    struct CallObservation level_call = call_bounded(
        core, P03_GET_LEVEL_UP_THUMB, P03_CATERPIE, P03_LEVEL_SCRATCH, 0U, 0U);
    if (level_call.result != 3U)
        p03_die("GetLevelUpMovesBySpecies count mismatch");
    for (unsigned row = 0U; row < 3U; ++row) {
        if (read16(core, P03_LEVEL_SCRATCH + row * 2U) != expected_moves[row])
            p03_die("GetLevelUpMovesBySpecies output mismatch");
    }

    uint32_t compatibility_root = read32(core, P03_TM_COMPATIBILITY_ROOT_SITE);
    uint32_t compatibility_row =
        compatibility_root + P03_CATERPIE * P03_COMPATIBILITY_STRIDE;
    uint32_t catalog_root = read32(core, P03_TM_CATALOG_ROOT_SITE);
    if (compatibility_root != P03_TM_COMPATIBILITY_ROOT_EXPECTED)
        p03_die("TM compatibility root mismatch");
    if (catalog_root != P03_TM_CATALOG_ROOT_EXPECTED)
        p03_die("TM catalog root mismatch");
    if (read16(core, catalog_root + P03_TM_SLOT_ELECTROWEB * 2U)
        != P03_MOVE_ELECTROWEB)
        p03_die("TM runtime slot116 catalog is not Move489");
    if (!p03_bit(core, compatibility_row, P03_TM_SLOT_ELECTROWEB)
        || p03_bit(core, compatibility_row, P03_PARENT_TM_SLOT_44)
        || p03_bit(core, compatibility_row, P03_PARENT_TM_SLOT_63))
        p03_die("Caterpie TM replacement bitset mismatch");

    create_mon(core, ADDR_PLAYER_PARTY, P03_CATERPIE, 5U);
    struct CallObservation tm116 = call_bounded(
        core, P03_CAN_LEARN_TMHM_THUMB,
        ADDR_PLAYER_PARTY, P03_TM_SLOT_ELECTROWEB, 0U, 0U);
    struct CallObservation tm44 = call_bounded(
        core, P03_CAN_LEARN_TMHM_THUMB,
        ADDR_PLAYER_PARTY, P03_PARENT_TM_SLOT_44, 0U, 0U);
    struct CallObservation tm63 = call_bounded(
        core, P03_CAN_LEARN_TMHM_THUMB,
        ADDR_PLAYER_PARTY, P03_PARENT_TM_SLOT_63, 0U, 0U);
    if (tm116.result != 1U || tm44.result != 0U || tm63.result != 0U)
        p03_die("CanMonLearnTMHM positive/negative result mismatch");
    if (!level_call.payload_pc_seen || !tm116.payload_pc_seen
        || !tm44.payload_pc_seen || !tm63.payload_pc_seen)
        p03_die("linked consumer payload PC was not observed");
    if (level_call.instructions == 0U || tm116.instructions == 0U
        || tm44.instructions == 0U || tm63.instructions == 0U)
        p03_die("direct-call instruction count is zero");
    if (log_problem_count != 0U)
        p03_die("mGBA warned/errored during direct consumer calls");

    printf(
        "{\"schema_version\":1,\"status\":\"PASS\","
        "\"classification\":\"REAL_CONSUMER_DIRECT_CALL_BOUNDED\","
        "\"rom_sha256\":\"%s\",\"read_only\":true,"
        "\"species_id\":%u,"
        "\"roots\":{\"level_up\":\"0x%08" PRIX32 "\","
        "\"level_literal\":\"0x%08" PRIX32 "\","
        "\"species_pointer\":\"0x%08" PRIX32 "\","
        "\"tm_compatibility\":\"0x%08" PRIX32 "\","
        "\"tm_catalog\":\"0x%08" PRIX32 "\"},"
        "\"level_up\":{\"symbol\":\"0x%08" PRIX32 "\","
        "\"thumb\":\"0x%08" PRIX32 "\",\"count\":%" PRIu32 ","
        "\"rows\":[[33,1],[81,1],[535,9]],"
        "\"moves\":[33,81,535],\"instructions\":%" PRIu32 "},"
        "\"machine\":{\"symbol\":\"0x%08" PRIX32 "\","
        "\"thumb\":\"0x%08" PRIX32 "\",\"source_item\":\"TM82\","
        "\"runtime_slot_zero_based\":116,\"catalog_move_id\":489,"
        "\"set_slots\":[116],"
        "\"cases\":{\"slot116\":{\"result\":%" PRIu32 ","
        "\"instructions\":%" PRIu32 "},"
        "\"old_slot44\":{\"result\":%" PRIu32 ","
        "\"instructions\":%" PRIu32 "},"
        "\"old_slot63\":{\"result\":%" PRIu32 ","
        "\"instructions\":%" PRIu32 "}}},"
        "\"payload_pc_seen\":true,\"warnings_errors\":0,"
        "\"scheduler_e2e\":false,\"full_p03_acceptance\":false,"
        "\"artifacts_written\":[]}\n",
        rom_sha256,
        P03_CATERPIE,
        level_root,
        level_literal,
        level_pointer,
        compatibility_root,
        catalog_root,
        (uint32_t)P03_GET_LEVEL_UP_SYMBOL,
        (uint32_t)P03_GET_LEVEL_UP_THUMB,
        level_call.result,
        level_call.instructions,
        (uint32_t)P03_CAN_LEARN_TMHM_SYMBOL,
        (uint32_t)P03_CAN_LEARN_TMHM_THUMB,
        tm116.result,
        tm116.instructions,
        tm44.result,
        tm44.instructions,
        tm63.result,
        tm63.instructions);

    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
