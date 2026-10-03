/*
 * Modernization P02 Rayquaza Wish-Mega direct-call gate for libmGBA 0.10.2.
 *
 * The process loads the exact Stage64 ROM read-only and calls the linked
 * GetMegaSpecies Thumb routine.  It intentionally makes no scheduler/E2E
 * claim: this is a bounded ABI/runtime lookup gate for the corrected table.
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
    P02_GET_MEGA_SPECIES_SYMBOL = 0x09114CF0U,
    P02_GET_MEGA_SPECIES_THUMB = P02_GET_MEGA_SPECIES_SYMBOL | 1U,
    P02_MOVE_SCRATCH = 0x0203C000U,
    P02_RAYQUAZA = 645U,
    P02_RAYQUAZA_MEGA = 1092U,
    P02_MOVE_DRAGON_ASCENT = 630U,
    P02_MOVE_OVERDRIVE = 773U,
    P02_ITEM_NONE = 0U,
};

static void p02_die(const char *message)
{
    fprintf(stderr, "mgba-modernization-p02-evolution: %s\n", message);
    exit(1);
}

static struct CallObservation p02_call(
    struct mCore *core, const uint16_t *moves, bool null_moves)
{
    uint32_t moves_address = 0U;
    if (!null_moves) {
        moves_address = P02_MOVE_SCRATCH;
        for (unsigned slot = 0U; slot < BATTLE_CORE_MOVE_SLOTS; ++slot)
            write16(core, moves_address + slot * 2U, moves[slot]);
    }
    return call_bounded(
        core,
        P02_GET_MEGA_SPECIES_THUMB,
        P02_RAYQUAZA,
        P02_ITEM_NONE,
        moves_address,
        0U);
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
        p02_die("ROM SHA-256 mismatch");

    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {
        .sample = NULL,
        .unixTime = fixed_unix_time,
        .serialize = NULL,
        .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) p02_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1])) p02_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);

    const uint16_t dragon_ascent[BATTLE_CORE_MOVE_SLOTS] = {
        P02_MOVE_DRAGON_ASCENT, 0U, 0U, 0U,
    };
    const uint16_t overdrive[BATTLE_CORE_MOVE_SLOTS] = {
        P02_MOVE_OVERDRIVE, 0U, 0U, 0U,
    };
    struct CallObservation positive = p02_call(core, dragon_ascent, false);
    struct CallObservation old_wrong_id = p02_call(core, overdrive, false);
    struct CallObservation null_moves = p02_call(core, NULL, true);

    if (positive.result != P02_RAYQUAZA_MEGA)
        p02_die("Dragon Ascent did not select Mega Rayquaza");
    if (old_wrong_id.result != 0U)
        p02_die("historical Item-namespace value still selects Mega Rayquaza");
    if (null_moves.result != 0U)
        p02_die("NULL moves unexpectedly selects Wish Mega evolution");
    if (!positive.payload_pc_seen || !old_wrong_id.payload_pc_seen
        || !null_moves.payload_pc_seen)
        p02_die("GetMegaSpecies payload PC was not observed");
    if (positive.instructions == 0U || old_wrong_id.instructions == 0U
        || null_moves.instructions == 0U)
        p02_die("direct-call instruction count is zero");
    if (log_problem_count != 0U)
        p02_die("mGBA warned/errored during direct calls");

    printf(
        "{\"schema_version\":1,\"status\":\"PASS\","
        "\"classification\":\"DIRECT_CALL_BOUNDED\","
        "\"rom_sha256\":\"%s\",\"read_only\":true,"
        "\"get_mega_species_symbol\":\"0x%08" PRIX32 "\","
        "\"get_mega_species_thumb\":\"0x%08" PRIX32 "\","
        "\"species_id\":%u,\"target_species_id\":%u,"
        "\"item_id\":0,\"cases\":{"
        "\"dragon_ascent\":{\"moves\":[%u,0,0,0],"
        "\"result\":%" PRIu32 ",\"instructions\":%" PRIu32 "},"
        "\"historical_773\":{\"moves\":[%u,0,0,0],"
        "\"result\":%" PRIu32 ",\"instructions\":%" PRIu32 "},"
        "\"null_moves\":{\"moves\":null,\"result\":%" PRIu32 ","
        "\"instructions\":%" PRIu32 "}},"
        "\"payload_pc_seen\":true,\"warnings_errors\":0,"
        "\"artifacts_written\":[]}\n",
        rom_sha256,
        (uint32_t)P02_GET_MEGA_SPECIES_SYMBOL,
        (uint32_t)P02_GET_MEGA_SPECIES_THUMB,
        P02_RAYQUAZA,
        P02_RAYQUAZA_MEGA,
        P02_MOVE_DRAGON_ASCENT,
        positive.result,
        positive.instructions,
        P02_MOVE_OVERDRIVE,
        old_wrong_id.result,
        old_wrong_id.instructions,
        null_moves.result,
        null_moves.instructions);

    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
