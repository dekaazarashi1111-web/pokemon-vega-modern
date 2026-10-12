/*
 * P03 Stage67 direct-consumer gate.
 *
 * The generated header enumerates every materialized evolution/tutor/normal-
 * egg target. Calls are bounded and read-only; this is not UI scheduler,
 * breeding, save/reload, or full-P03 E2E acceptance.
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
    P03_EVOLUTION_SYMBOL = 0x09114120U,
    P03_EVOLUTION_THUMB = P03_EVOLUTION_SYMBOL | 1U,
    P03_TUTOR_SYMBOL = 0x09110228U,
    P03_TUTOR_THUMB = P03_TUTOR_SYMBOL | 1U,
    P03_EGG_SYMBOL = 0x090EB970U,
    P03_EGG_THUMB = P03_EGG_SYMBOL | 1U,
    P03_LEVEL_ROOT_SITE = 0x0804346CU,
    P03_LEVEL_LITERAL_SITE = 0x09FDA1F8U,
    P03_LEVEL_ROOT_EXPECTED = 0x093A4CACU,
    P03_EVOLUTION_PAYLOAD_START = 0x09FE8D1CU,
    P03_EVOLUTION_PAYLOAD_END = 0x09FED0C3U,
    P03_TUTOR_ROOT_SITE = 0x08121420U,
    P03_TUTOR_ROOT_EXPECTED = 0x093B1B28U,
    P03_TUTOR_CATALOG_SITE = 0x081213D4U,
    P03_TUTOR_CATALOG_EXPECTED = 0x0944BC80U,
    P03_TUTOR_SLOTS = 64U,
    P03_TUTOR_STRIDE = 16U,
    P03_EGG_PRIMARY_SITE = 0x08045214U,
    P03_EGG_SECONDARY_SITE = 0x0804528CU,
    P03_EGG_LIMIT_SITE = 0x08045288U,
    P03_EGG_ROOT_EXPECTED = 0x09FED0C4U,
    P03_EGG_SCAN_LIMIT_EXPECTED = 7557U,
    P03_EGG_SCRATCH = 0x0203C000U,
    P03_MAX_EGG_MOVES = 50U,
    P03_EXPECTED_EVOLUTION_SPECIES = 330U,
    P03_EXPECTED_EVOLUTION_ROUTES = 341U,
    P03_EXPECTED_TUTOR_SPECIES = 290U,
    P03_EXPECTED_TUTOR_ROUTES = 740U,
    P03_EXPECTED_EGG_SPECIES = 450U,
    P03_EXPECTED_EGG_ROUTES = 2522U,
};

struct P03ConsumerCase {
    uint16_t species;
    uint8_t count;
};

#include "p03_stage67_cases.h"

struct P03Totals {
    uint32_t evolution_routes;
    uint32_t tutor_positive_routes;
    uint32_t tutor_negative_calls;
    uint32_t egg_routes;
    uint32_t evolution_instructions;
    uint32_t tutor_instructions;
    uint32_t egg_instructions;
    uint64_t semantic_digest;
    bool payload_pc_seen;
};

static void p03_die(const char *message)
{
    fprintf(stderr, "mgba-modernization-p03-stage67: %s\n", message);
    exit(1);
}

static uint16_t p03_read_packed_u16(struct mCore *core, uint32_t address)
{
    return (uint16_t)(read8(core, address)
        | ((uint16_t)read8(core, address + 1U) << 8U));
}

static void p03_digest_u8(uint64_t *digest, uint8_t value)
{
    *digest ^= value;
    *digest *= UINT64_C(1099511628211);
}

static void p03_digest_u16(uint64_t *digest, uint16_t value)
{
    p03_digest_u8(digest, (uint8_t)value);
    p03_digest_u8(digest, (uint8_t)(value >> 8U));
}

static uint32_t p03_find_egg_row(
    struct mCore *core, uint32_t root, uint16_t species
)
{
    uint16_t marker = (uint16_t)(20000U + species);
    for (uint32_t index = 0U; index <= P03_EGG_SCAN_LIMIT_EXPECTED; ++index) {
        uint16_t value = read16(core, root + index * 2U);
        if (value == marker) return root + (index + 1U) * 2U;
        if (value == 0xFFFFU) break;
    }
    p03_die("materialized egg marker was not found");
    return 0U;
}

static void p03_clear_moves(struct mCore *core)
{
    for (unsigned slot = 0U; slot < BATTLE_CORE_MOVE_SLOTS; ++slot) {
        set_mon_data_u32(core, ADDR_PLAYER_PARTY, MON_DATA_MOVE1 + slot, 0U);
        set_mon_data_u32(core, ADDR_PLAYER_PARTY, MON_DATA_PP1 + slot, 0U);
    }
}

static void p03_check_p02_overlay(struct mCore *core)
{
    static const uint32_t spans[] = {
        0x09F898B8U, 0x09F91AB8U, 0x09F94DB8U,
        0x09F98FB8U, 0x09F993B8U, 0x09F9CFB8U,
    };
    for (unsigned row = 0U; row < ARRAY_LEN(spans); ++row) {
        if (read16(core, spans[row]) != 4U
            || read16(core, spans[row] + 8U) != 35U)
            p03_die("P02 regular-before-conditional row order was not preserved");
    }
}

static void p03_run_evolution(struct mCore *core, struct P03Totals *totals)
{
    uint32_t root = read32(core, P03_LEVEL_ROOT_SITE);
    if (root != P03_LEVEL_ROOT_EXPECTED
        || read32(core, P03_LEVEL_LITERAL_SITE) != root)
        p03_die("level root/literal mismatch");
    if (ARRAY_LEN(p03_evolution_cases) != P03_EXPECTED_EVOLUTION_SPECIES)
        p03_die("generated evolution species count mismatch");
    for (unsigned index = 0U; index < ARRAY_LEN(p03_evolution_cases); ++index) {
        const struct P03ConsumerCase *test = &p03_evolution_cases[index];
        uint32_t pointer = read32(core, root + test->species * 4U);
        if (pointer < P03_EVOLUTION_PAYLOAD_START
            || pointer >= P03_EVOLUTION_PAYLOAD_END)
            p03_die("evolution pointer is outside Stage67 payload");
        unsigned count = 0U;
        while (count < 5U && read8(core, pointer + count * 3U + 2U) == 0U)
            ++count;
        if (count != test->count || count == 0U || count > 4U)
            p03_die("leading evolution row count mismatch");
        create_mon(core, ADDR_PLAYER_PARTY, test->species, 5U);
        p03_clear_moves(core);
        for (unsigned route = 0U; route < count; ++route) {
            uint16_t move = p03_read_packed_u16(core, pointer + route * 3U);
            if (move == 0U || move > 1062U)
                p03_die("evolution Move ID is outside implemented runtime");
            struct CallObservation call = call_bounded(
                core, P03_EVOLUTION_THUMB, ADDR_PLAYER_PARTY,
                route == 0U ? 1U : 0U, 0U, 0U);
            if (call.result != move || call.instructions == 0U
                || !call.payload_pc_seen)
                p03_die("MonTryLearningNewMoveAfterEvolution result mismatch");
            if (call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                                ADDR_PLAYER_PARTY, MON_DATA_MOVE1 + route, 0U, 0U)
                != move)
                p03_die("evolution move was not added to the real mon");
            p03_digest_u8(&totals->semantic_digest, 1U);
            p03_digest_u16(&totals->semantic_digest, test->species);
            p03_digest_u8(&totals->semantic_digest, (uint8_t)route);
            p03_digest_u16(&totals->semantic_digest, move);
            p03_digest_u16(&totals->semantic_digest, (uint16_t)call.result);
            ++totals->evolution_routes;
            totals->evolution_instructions += call.instructions;
            totals->payload_pc_seen = true;
        }
    }
    if (totals->evolution_routes != P03_EXPECTED_EVOLUTION_ROUTES)
        p03_die("evolution route total mismatch");
}

static void p03_run_tutor(struct mCore *core, struct P03Totals *totals)
{
    uint32_t root = read32(core, P03_TUTOR_ROOT_SITE);
    uint32_t catalog = read32(core, P03_TUTOR_CATALOG_SITE);
    if (root != P03_TUTOR_ROOT_EXPECTED || catalog != P03_TUTOR_CATALOG_EXPECTED)
        p03_die("tutor root/catalog mismatch");
    if (ARRAY_LEN(p03_tutor_cases) != P03_EXPECTED_TUTOR_SPECIES)
        p03_die("generated tutor species count mismatch");
    for (unsigned index = 0U; index < ARRAY_LEN(p03_tutor_cases); ++index) {
        const struct P03ConsumerCase *test = &p03_tutor_cases[index];
        uint32_t row = root + test->species * P03_TUTOR_STRIDE;
        unsigned count = 0U;
        int negative = -1;
        create_mon(core, ADDR_PLAYER_PARTY, test->species, 5U);
        for (unsigned slot = 0U; slot < P03_TUTOR_SLOTS; ++slot) {
            bool set = (read8(core, row + slot / 8U) & (1U << (slot % 8U))) != 0U;
            if (!set) {
                if (negative < 0) negative = (int)slot;
                continue;
            }
            uint16_t move = read16(core, catalog + slot * 2U);
            struct CallObservation call = call_bounded(
                core, P03_TUTOR_THUMB, ADDR_PLAYER_PARTY, slot, 0U, 0U);
            if (call.result != 1U || call.instructions == 0U
                || !call.payload_pc_seen || move == 0U || move > 1062U)
                p03_die("CanMonLearnTutorMove positive result mismatch");
            p03_digest_u8(&totals->semantic_digest, 2U);
            p03_digest_u16(&totals->semantic_digest, test->species);
            p03_digest_u8(&totals->semantic_digest, (uint8_t)slot);
            p03_digest_u16(&totals->semantic_digest, move);
            p03_digest_u8(&totals->semantic_digest, (uint8_t)call.result);
            ++count;
            ++totals->tutor_positive_routes;
            totals->tutor_instructions += call.instructions;
            totals->payload_pc_seen = true;
        }
        if (count != test->count || negative < 0)
            p03_die("tutor materialized row count/negative slot mismatch");
        struct CallObservation call = call_bounded(
            core, P03_TUTOR_THUMB, ADDR_PLAYER_PARTY,
            (uint32_t)negative, 0U, 0U);
        if (call.result != 0U || call.instructions == 0U || !call.payload_pc_seen)
            p03_die("CanMonLearnTutorMove negative result mismatch");
        p03_digest_u8(&totals->semantic_digest, 3U);
        p03_digest_u16(&totals->semantic_digest, test->species);
        p03_digest_u8(&totals->semantic_digest, (uint8_t)negative);
        p03_digest_u8(&totals->semantic_digest, (uint8_t)call.result);
        ++totals->tutor_negative_calls;
        totals->tutor_instructions += call.instructions;
    }
    if (totals->tutor_positive_routes != P03_EXPECTED_TUTOR_ROUTES
        || totals->tutor_negative_calls != P03_EXPECTED_TUTOR_SPECIES)
        p03_die("tutor route/case total mismatch");
}

static void p03_run_egg(struct mCore *core, struct P03Totals *totals)
{
    uint32_t primary = read32(core, P03_EGG_PRIMARY_SITE);
    uint32_t secondary = read32(core, P03_EGG_SECONDARY_SITE);
    uint32_t limit = read32(core, P03_EGG_LIMIT_SITE);
    if (primary != P03_EGG_ROOT_EXPECTED || secondary != primary
        || limit != P03_EGG_SCAN_LIMIT_EXPECTED)
        p03_die("egg dual root/scan limit mismatch");
    if (ARRAY_LEN(p03_egg_cases) != P03_EXPECTED_EGG_SPECIES)
        p03_die("generated egg species count mismatch");
    for (unsigned index = 0U; index < ARRAY_LEN(p03_egg_cases); ++index) {
        const struct P03ConsumerCase *test = &p03_egg_cases[index];
        uint32_t row = p03_find_egg_row(core, primary, test->species);
        uint16_t expected[P03_MAX_EGG_MOVES];
        unsigned count = 0U;
        while (count < P03_MAX_EGG_MOVES) {
            uint16_t value = read16(core, row + count * 2U);
            if (value >= 20000U || value == 0xFFFFU) break;
            expected[count++] = value;
        }
        if (count != test->count || count == P03_MAX_EGG_MOVES)
            p03_die("normal egg table row count mismatch");
        create_mon(core, ADDR_PLAYER_PARTY, test->species, 5U);
        for (unsigned move = 0U; move < P03_MAX_EGG_MOVES; ++move)
            write16(core, P03_EGG_SCRATCH + move * 2U, 0xDEADU);
        struct CallObservation call = call_bounded(
            core, P03_EGG_THUMB, ADDR_PLAYER_PARTY, P03_EGG_SCRATCH, 0U, 0U);
        if (call.result != count || call.instructions == 0U || !call.payload_pc_seen)
            p03_die("GetAllEggMoves count/result mismatch");
        p03_digest_u8(&totals->semantic_digest, 4U);
        p03_digest_u16(&totals->semantic_digest, test->species);
        p03_digest_u8(&totals->semantic_digest, (uint8_t)count);
        for (unsigned move = 0U; move < count; ++move) {
            uint16_t actual = read16(core, P03_EGG_SCRATCH + move * 2U);
            if (actual != expected[move])
                p03_die("GetAllEggMoves exact ordered row mismatch");
            if (test->species == 24U && actual == 344U)
                p03_die("conditional Volt Tackle leaked into normal egg table");
            p03_digest_u8(&totals->semantic_digest, (uint8_t)move);
            p03_digest_u16(&totals->semantic_digest, actual);
            ++totals->egg_routes;
        }
        totals->egg_instructions += call.instructions;
        totals->payload_pc_seen = true;
    }
    if (totals->egg_routes != P03_EXPECTED_EGG_ROUTES)
        p03_die("normal egg route total mismatch");
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

    struct P03Totals totals = {
        .semantic_digest = UINT64_C(14695981039346656037),
    };
    p03_check_p02_overlay(core);
    p03_run_evolution(core, &totals);
    p03_run_tutor(core, &totals);
    p03_run_egg(core, &totals);
    if (!totals.payload_pc_seen || log_problem_count != 0U)
        p03_die("payload PC missing or mGBA warning/error observed");

    printf(
        "{\"schema_version\":1,\"status\":\"PASS\","
        "\"classification\":\"REAL_CONSUMER_DIRECT_CALL_ALL_MATERIALIZED\","
        "\"rom_sha256\":\"%s\",\"read_only\":true,"
        "\"p02_overlay_rows_preserved\":6,"
        "\"roots\":{\"level\":\"0x%08" PRIX32 "\","
        "\"tutor\":\"0x%08" PRIX32 "\","
        "\"tutor_catalog\":\"0x%08" PRIX32 "\","
        "\"egg_primary\":\"0x%08" PRIX32 "\","
        "\"egg_secondary\":\"0x%08" PRIX32 "\","
        "\"egg_scan_limit\":%" PRIu32 "},"
        "\"counts\":{\"evolution_species\":%u,\"evolution_routes\":%" PRIu32 ","
        "\"tutor_species\":%u,\"tutor_positive_routes\":%" PRIu32 ","
        "\"tutor_negative_calls\":%" PRIu32 ",\"egg_species\":%u,"
        "\"egg_routes\":%" PRIu32 "},"
        "\"instructions\":{\"evolution\":%" PRIu32 ","
        "\"tutor\":%" PRIu32 ",\"egg\":%" PRIu32 "},"
        "\"semantic_digest_fnv1a64\":\"%016" PRIx64 "\","
        "\"representatives\":{\"evolution\":[%u,%u,%u,%u],"
        "\"tutor\":[%u,%u,%u],\"egg\":[%u,%u,%u,%u,%u]},"
        "\"symbols\":{\"evolution\":\"0x%08" PRIX32 "\","
        "\"tutor\":\"0x%08" PRIX32 "\",\"egg\":\"0x%08" PRIX32 "\"},"
        "\"payload_pc_seen\":true,\"warnings_errors\":0,"
        "\"scheduler_e2e\":false,\"breeding_e2e\":false,"
        "\"save_reload_e2e\":false,\"full_p03_acceptance\":false,"
        "\"artifacts_written\":[]}\n",
        rom_sha256,
        read32(core, P03_LEVEL_ROOT_SITE), read32(core, P03_TUTOR_ROOT_SITE),
        read32(core, P03_TUTOR_CATALOG_SITE), read32(core, P03_EGG_PRIMARY_SITE),
        read32(core, P03_EGG_SECONDARY_SITE), read32(core, P03_EGG_LIMIT_SITE),
        (unsigned)ARRAY_LEN(p03_evolution_cases), totals.evolution_routes,
        (unsigned)ARRAY_LEN(p03_tutor_cases), totals.tutor_positive_routes,
        totals.tutor_negative_calls, (unsigned)ARRAY_LEN(p03_egg_cases),
        totals.egg_routes, totals.evolution_instructions,
        totals.tutor_instructions, totals.egg_instructions,
        totals.semantic_digest,
        p03_evolution_cases[0].species,
        p03_evolution_cases[ARRAY_LEN(p03_evolution_cases) / 2U].species,
        p03_evolution_cases[ARRAY_LEN(p03_evolution_cases) - 1U].species, 534U,
        p03_tutor_cases[0].species,
        p03_tutor_cases[ARRAY_LEN(p03_tutor_cases) / 2U].species,
        p03_tutor_cases[ARRAY_LEN(p03_tutor_cases) - 1U].species,
        p03_egg_cases[0].species,
        p03_egg_cases[ARRAY_LEN(p03_egg_cases) / 2U].species,
        p03_egg_cases[ARRAY_LEN(p03_egg_cases) - 1U].species, 24U, 1048U,
        (uint32_t)P03_EVOLUTION_SYMBOL, (uint32_t)P03_TUTOR_SYMBOL,
        (uint32_t)P03_EGG_SYMBOL);

    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
