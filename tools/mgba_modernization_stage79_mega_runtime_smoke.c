/*
 * Modernization Stage79 exact-ROM Mega mapping gate for libmGBA 0.10.2.
 *
 * The caller supplies the canonical (base species, Mega Stone, Mega species)
 * triples.  Every triple is exercised against the ROM's linked CFRU routines:
 * GetMegaSpecies, IsMegaSpecies, and TryRevertMega.  This is deliberately a
 * bounded direct-call gate; battle scheduling and one-mechanic policy remain
 * the responsibility of the existing battle-policy runner.
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
    MEGA_GET_SPECIES_SYMBOL = 0x09114CF0U,
    MEGA_GET_SPECIES_THUMB = MEGA_GET_SPECIES_SYMBOL | 1U,
    MEGA_TRY_REVERT_SYMBOL = 0x09114F74U,
    MEGA_TRY_REVERT_THUMB = MEGA_TRY_REVERT_SYMBOL | 1U,
    MEGA_IS_SPECIES_SYMBOL = 0x09115098U,
    MEGA_IS_SPECIES_THUMB = MEGA_IS_SPECIES_SYMBOL | 1U,
    MEGA_MON_DATA_SPECIES = 11U,
    MEGA_PARTY_SPECIES_OFFSET = 0x20U,
    MEGA_ITEM_NONE = 0U,
    MEGA_TEST_LEVEL = 50U,
    MEGA_MAX_MAPPINGS = 128U,
};

struct MegaMapping {
    uint16_t base_species;
    uint16_t stone;
    uint16_t mega_species;
};

static void mega_die(const char *message)
{
    fprintf(stderr, "mgba-modernization-stage79-mega-runtime: %s\n", message);
    exit(1);
}

static uint32_t parse_u32(const char *text, const char *label)
{
    char *end = NULL;
    errno = 0;
    unsigned long value = strtoul(text, &end, 0);
    if (errno != 0 || end == text || *end != '\0' || value > UINT32_MAX) {
        fprintf(stderr,
                "mgba-modernization-stage79-mega-runtime: invalid %s: %s\n",
                label, text);
        exit(2);
    }
    return (uint32_t)value;
}

static struct CallObservation mega_call(struct mCore *core,
                                        uint32_t function,
                                        uint32_t r0,
                                        uint32_t r1,
                                        uint32_t r2,
                                        uint32_t r3,
                                        uint64_t *instructions,
                                        uint32_t *calls)
{
    struct CallObservation result = call_bounded(
        core, function, r0, r1, r2, r3);
    if (!result.payload_pc_seen || result.instructions == 0U)
        mega_die("direct call did not execute the linked CFRU payload");
    *instructions += result.instructions;
    ++*calls;
    return result;
}

static void require_mapping_unique(const struct MegaMapping *mappings,
                                   uint32_t count)
{
    for (uint32_t i = 0U; i < count; ++i) {
        if (mappings[i].base_species == 0U
            || mappings[i].stone == MEGA_ITEM_NONE
            || mappings[i].mega_species == 0U) {
            mega_die("mapping contains a zero base, stone, or Mega species");
        }
        for (uint32_t j = 0U; j < i; ++j) {
            if (mappings[i].base_species == mappings[j].base_species
                && mappings[i].stone == mappings[j].stone) {
                mega_die("duplicate base-species/Mega-Stone mapping");
            }
            if (mappings[i].mega_species == mappings[j].mega_species)
                mega_die("duplicate Mega target species mapping");
        }
    }
}

int main(int argc, char **argv)
{
    if (argc < 6) {
        fprintf(stderr,
                "usage: %s ROM EXPECTED_ROM_SHA256 COUNT "
                "BASE STONE MEGA [BASE STONE MEGA ...]\n",
                argv[0]);
        return 2;
    }

    uint32_t count = parse_u32(argv[3], "mapping count");
    if (count == 0U || count > MEGA_MAX_MAPPINGS
        || argc != 4 + (int)(count * 3U)) {
        mega_die("mapping count does not match the supplied triples");
    }

    struct MegaMapping *mappings = calloc(count, sizeof(*mappings));
    if (mappings == NULL)
        mega_die("mapping allocation failed");
    for (uint32_t i = 0U; i < count; ++i) {
        uint32_t base = parse_u32(argv[4 + i * 3U], "base species");
        uint32_t stone = parse_u32(argv[5 + i * 3U], "Mega Stone");
        uint32_t mega = parse_u32(argv[6 + i * 3U], "Mega species");
        if (base > UINT16_MAX || stone > UINT16_MAX || mega > UINT16_MAX)
            mega_die("mapping value exceeds the ROM u16 ABI");
        mappings[i].base_species = (uint16_t)base;
        mappings[i].stone = (uint16_t)stone;
        mappings[i].mega_species = (uint16_t)mega;
    }
    require_mapping_unique(mappings, count);

    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strlen(argv[2]) != 64U || strcmp(rom_sha256, argv[2]) != 0)
        mega_die("ROM SHA-256 mismatch");

    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {
        .sample = NULL,
        .unixTime = fixed_unix_time,
        .serialize = NULL,
        .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(argv[1]);
    if (core == NULL || !core->init(core))
        mega_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1]))
        mega_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);

    uint64_t instructions = 0U;
    uint32_t direct_calls = 0U;
    for (uint32_t i = 0U; i < count; ++i) {
        const struct MegaMapping *row = &mappings[i];
        struct CallObservation forward = mega_call(
            core, MEGA_GET_SPECIES_THUMB,
            row->base_species, row->stone, 0U, 0U,
            &instructions, &direct_calls);
        if (forward.result != row->mega_species) {
            fprintf(stderr,
                    "mgba-modernization-stage79-mega-runtime: "
                    "forward mismatch row=%" PRIu32 " base=%u stone=%u "
                    "expected=%u actual=%" PRIu32 "\n",
                    i, row->base_species, row->stone,
                    row->mega_species, forward.result);
            exit(1);
        }

        struct CallObservation no_item = mega_call(
            core, MEGA_GET_SPECIES_THUMB,
            row->base_species, MEGA_ITEM_NONE, 0U, 0U,
            &instructions, &direct_calls);
        if (no_item.result != 0U)
            mega_die("stone-less Mega lookup unexpectedly succeeded");

        struct CallObservation target_is_mega = mega_call(
            core, MEGA_IS_SPECIES_THUMB,
            row->mega_species, 0U, 0U, 0U,
            &instructions, &direct_calls);
        if (target_is_mega.result != 1U)
            mega_die("Mega target is not recognized by IsMegaSpecies");

        struct CallObservation base_is_mega = mega_call(
            core, MEGA_IS_SPECIES_THUMB,
            row->base_species, 0U, 0U, 0U,
            &instructions, &direct_calls);
        if (base_is_mega.result != 0U)
            mega_die("base species is unexpectedly recognized as a Mega species");

        clear_parties(core);
        create_mon(core, ADDR_PLAYER_PARTY, row->mega_species, MEGA_TEST_LEVEL);
        if (read16(core, ADDR_PLAYER_PARTY + MEGA_PARTY_SPECIES_OFFSET)
                != row->mega_species)
            mega_die("Mega party fixture direct species differs before revert");
        (void)mega_call(
            core, MEGA_TRY_REVERT_THUMB,
            ADDR_PLAYER_PARTY, 0U, 0U, 0U,
            &instructions, &direct_calls);
        uint32_t reverted = call_preserving(
            core, BATTLE_CORE_GET_MON_DATA,
            ADDR_PLAYER_PARTY, MEGA_MON_DATA_SPECIES, 0U, 0U);
        if (reverted != row->base_species
            || read16(core, ADDR_PLAYER_PARTY + MEGA_PARTY_SPECIES_OFFSET)
                != row->base_species) {
            fprintf(stderr,
                    "mgba-modernization-stage79-mega-runtime: "
                    "revert mismatch row=%" PRIu32 " mega=%u "
                    "expected=%u actual=%" PRIu32 "\n",
                    i, row->mega_species, row->base_species, reverted);
            exit(1);
        }
    }

    if (log_problem_count != 0U)
        mega_die("mGBA warned/errored during Mega mapping calls");

    printf(
        "{\"schema_version\":1,\"status\":\"PASS\","
        "\"classification\":\"DIRECT_CALL_BOUNDED\","
        "\"rom_sha256\":\"%s\",\"read_only\":true,"
        "\"mapping_count\":%" PRIu32 ","
        "\"correct_stone_matches\":%" PRIu32 ","
        "\"stone_less_rejections\":%" PRIu32 ","
        "\"mega_species_recognized\":%" PRIu32 ","
        "\"base_species_rejected_as_mega\":%" PRIu32 ","
        "\"reversions_to_base\":%" PRIu32 ","
        "\"direct_calls\":%" PRIu32 ","
        "\"instructions\":%" PRIu64 ","
        "\"symbols\":{"
        "\"GetMegaSpecies\":\"0x%08" PRIX32 "\","
        "\"TryRevertMega\":\"0x%08" PRIX32 "\","
        "\"IsMegaSpecies\":\"0x%08" PRIX32 "\"},"
        "\"payload_pc_seen\":true,\"warnings_errors\":0,"
        "\"artifacts_written\":[]}\n",
        rom_sha256, count, count, count, count, count, count,
        direct_calls, instructions,
        (uint32_t)MEGA_GET_SPECIES_SYMBOL,
        (uint32_t)MEGA_TRY_REVERT_SYMBOL,
        (uint32_t)MEGA_IS_SPECIES_SYMBOL);

    free(mappings);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);  /* mGBA owns and frees core here. */
    return 0;
}
