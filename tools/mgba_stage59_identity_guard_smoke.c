/* Exhaustive Stage59 canonical wild-identity guard smoke for exact-ROM mGBA. */

#define BATTLE_CORE_EMBEDDED
#pragma GCC diagnostic push
#pragma GCC diagnostic ignored "-Wunused-function"
#include "mgba_battle_core_smoke.c"
#pragma GCC diagnostic pop

enum {
    STAGE59_SPECIES_COUNT = 1621U,
    STAGE59_ABI_VERSION = 0x35394449U,
    STAGE59_NAME_LENGTH = 11U,
    STAGE59_MON_DATA_NICKNAME = 2U,
    STAGE59_MON_DATA_SPECIES = 11U,
    STAGE59_MON_DATA_MOVE1 = 13U,
    STAGE59_GET_SPECIES_NAME = 0x080406C5U,
    STAGE59_SPECIES_SCRATCH = 0x0203E700U,
    STAGE59_BAD_NAME_SCRATCH = 0x0203E720U,
    STAGE59_NAME_SCRATCH = 0x0203E740U,
    STAGE59_CANONICAL_SCRATCH = 0x0203E760U,
    STAGE59_LAND_HOOK = 0x080826D8U,
    STAGE59_FISHING_HOOK = 0x08082750U,
    STAGE59_HIDDEN_HOOK = 0x09220198U,
};

static uint32_t stage59_parse_u32(const char *text, const char *label)
{
    char *end = NULL;
    unsigned long value;
    errno = 0;
    value = strtoul(text, &end, 0);
    if (errno != 0 || end == text || *end != '\0' || value > UINT32_MAX) {
        fprintf(stderr, "mgba-stage59-identity-guard: invalid %s: %s\n",
                label, text);
        exit(2);
    }
    return (uint32_t)value;
}

static void stage59_require_hook(struct mCore *core, uint32_t site,
                                 uint32_t target, const char *label)
{
    if (read16(core, site) != 0x4B00U
        || read16(core, site + 2U) != 0x4718U
        || read32(core, site + 4U) != (target | 1U)) {
        fprintf(stderr,
                "mgba-stage59-identity-guard: %s hook differs "
                "site=%08" PRIX32 " bytes=%04X/%04X/%08" PRIX32
                " expected=%08" PRIX32 "\n",
                label, site, read16(core, site), read16(core, site + 2U),
                read32(core, site + 4U), target | 1U);
        exit(1);
    }
}

static void stage59_set_species(struct mCore *core, uint16_t species)
{
    write16(core, STAGE59_SPECIES_SCRATCH, species);
    (void)call_preserving(core, ROM_SET_MON_DATA, ADDR_ENEMY_PARTY,
                          STAGE59_MON_DATA_SPECIES,
                          STAGE59_SPECIES_SCRATCH, 0U);
    if (call_preserving(core, BATTLE_CORE_GET_MON_DATA, ADDR_ENEMY_PARTY,
                        STAGE59_MON_DATA_SPECIES, 0U, 0U) != species) {
        fprintf(stderr,
                "mgba-stage59-identity-guard: Species writeback differs: %u\n",
                species);
        exit(1);
    }
}

static void stage59_corrupt_nickname(struct mCore *core, uint16_t species)
{
    for (unsigned index = 0U; index < STAGE59_NAME_LENGTH; ++index)
        write8(core, STAGE59_BAD_NAME_SCRATCH + index, 0x00U);
    /* Include the Species ID so the encrypted payload changes on every case,
     * while remaining an intentionally noncanonical terminated name. */
    write8(core, STAGE59_BAD_NAME_SCRATCH,
           (uint8_t)(0x01U + (species & 0x7FU)));
    write8(core, STAGE59_BAD_NAME_SCRATCH + 1U,
           (uint8_t)(0x01U + ((species >> 7U) & 0x7FU)));
    write8(core, STAGE59_BAD_NAME_SCRATCH + 2U, 0xFFU);
    (void)call_preserving(core, ROM_SET_MON_DATA, ADDR_ENEMY_PARTY,
                          STAGE59_MON_DATA_NICKNAME,
                          STAGE59_BAD_NAME_SCRATCH, 0U);
}

static void stage59_read_name(struct mCore *core, uint32_t destination)
{
    for (unsigned index = 0U; index < STAGE59_NAME_LENGTH; ++index)
        write8(core, destination + index, 0xA5U);
    (void)call_preserving(core, BATTLE_CORE_GET_MON_DATA, ADDR_ENEMY_PARTY,
                          STAGE59_MON_DATA_NICKNAME, destination, 0U);
}

static void stage59_require_canonical_name(struct mCore *core,
                                           uint16_t species)
{
    bool terminated = false;
    stage59_read_name(core, STAGE59_NAME_SCRATCH);
    for (unsigned index = 0U; index < STAGE59_NAME_LENGTH; ++index)
        write8(core, STAGE59_CANONICAL_SCRATCH + index, 0xA5U);
    (void)call_preserving(core, STAGE59_GET_SPECIES_NAME,
                          STAGE59_CANONICAL_SCRATCH, species, 0U, 0U);
    for (unsigned index = 0U; index < STAGE59_NAME_LENGTH; ++index) {
        uint8_t actual = read8(core, STAGE59_NAME_SCRATCH + index);
        uint8_t expected = read8(core, STAGE59_CANONICAL_SCRATCH + index);
        if (actual != expected) {
            fprintf(stderr,
                    "mgba-stage59-identity-guard: nickname mismatch "
                    "species=%u index=%u actual=%02X expected=%02X\n",
                    species, index, actual, expected);
            exit(1);
        }
        if (expected == 0xFFU) {
            terminated = true;
            break;
        }
    }
    if (!terminated) {
        fprintf(stderr,
                "mgba-stage59-identity-guard: canonical name unterminated "
                "species=%u\n", species);
        exit(1);
    }
}

int main(int argc, char **argv)
{
    if (argc != 8) {
        fprintf(stderr,
                "usage: %s ROM EXPECTED_SHA256 NORMALIZER LAND FISH HIDDEN PROBE\n",
                argv[0]);
        return 2;
    }

    char rom_sha256[65];
    sha256_file(argv[1], rom_sha256);
    if (strlen(argv[2]) != 64U || strcmp(rom_sha256, argv[2]) != 0)
        battle_core_die("Stage59 exact candidate SHA-256 mismatch");

    uint32_t normalizer = stage59_parse_u32(argv[3], "normalizer");
    uint32_t land = stage59_parse_u32(argv[4], "land adapter");
    uint32_t fishing = stage59_parse_u32(argv[5], "fishing adapter");
    uint32_t hidden = stage59_parse_u32(argv[6], "hidden adapter");
    uint32_t probe = stage59_parse_u32(argv[7], "probe");
    if ((normalizer | land | fishing | hidden | probe) & 1U) {
        battle_core_die("Stage59 symbol arguments must be even linked addresses");
    }

    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {
        .sample = NULL, .unixTime = fixed_unix_time,
        .serialize = NULL, .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core) || !mCoreLoadFile(core, argv[1]))
        battle_core_die("Stage59 identity core/ROM initialization failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);

    stage59_require_hook(core, STAGE59_LAND_HOOK, land, "land/water");
    stage59_require_hook(core, STAGE59_FISHING_HOOK, fishing, "fishing");
    stage59_require_hook(core, STAGE59_HIDDEN_HOOK, hidden, "hidden");

    if (call_preserving(core, probe | 1U, 0U, 0U, 0U, 0U)
            != STAGE59_ABI_VERSION
        || call_preserving(core, probe | 1U, 1U, 0U, 0U, 0U)
            != STAGE59_SPECIES_COUNT
        || call_preserving(core, probe | 1U, 2U, 0U, 0U, 0U)
            != 0x094141BDU
        || call_preserving(core, probe | 1U, 3U, 0U, 0U, 0U)
            != 0x093BEA69U
        || call_preserving(core, probe | 1U, 4U, 0U, 0U, 0U)
            != 0x093BEA99U
        || call_preserving(core, probe | 1U, 5U, 0U, 0U, 0U)
            != 0x09414159U
        || call_preserving(core, probe | 1U, 6U, 0U, 0U, 0U) != 0U) {
        battle_core_die("Stage59 runtime probe ABI differs");
    }

    run_trace_prefix(core);
    clear_parties(core);
    seed_fixture(core);
    create_mon(core, ADDR_ENEMY_PARTY, 1U, 5U);
    write8(core, BATTLE_CORE_ENEMY_PARTY_COUNT, 1U);

    unsigned checked = 0U;
    unsigned moves_preserved = 0U;
    for (unsigned value = 1U; value < STAGE59_SPECIES_COUNT; ++value) {
        uint16_t species = (uint16_t)value;
        uint32_t moves_before[BATTLE_CORE_MOVE_SLOTS];
        stage59_set_species(core, species);
        stage59_corrupt_nickname(core, species);
        for (unsigned slot = 0U; slot < BATTLE_CORE_MOVE_SLOTS; ++slot) {
            moves_before[slot] = call_preserving(
                core, BATTLE_CORE_GET_MON_DATA, ADDR_ENEMY_PARTY,
                STAGE59_MON_DATA_MOVE1 + slot, 0U, 0U);
        }
        uint32_t normalized = call_preserving(
            core, normalizer | 1U, 0U, 0U, 0U, 0U);
        if (normalized != species
            || call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                               ADDR_ENEMY_PARTY,
                               STAGE59_MON_DATA_SPECIES, 0U, 0U) != species) {
            fprintf(stderr,
                    "mgba-stage59-identity-guard: normalizer Species differs "
                    "species=%u result=%" PRIu32 "\n", species, normalized);
            exit(1);
        }
        stage59_require_canonical_name(core, species);
        for (unsigned slot = 0U; slot < BATTLE_CORE_MOVE_SLOTS; ++slot) {
            uint32_t after = call_preserving(
                core, BATTLE_CORE_GET_MON_DATA, ADDR_ENEMY_PARTY,
                STAGE59_MON_DATA_MOVE1 + slot, 0U, 0U);
            if (after != moves_before[slot]) {
                fprintf(stderr,
                        "mgba-stage59-identity-guard: move changed "
                        "species=%u slot=%u before=%" PRIu32
                        " after=%" PRIu32 "\n",
                        species, slot, moves_before[slot], after);
                exit(1);
            }
        }
        ++moves_preserved;
        ++checked;
    }

    if (log_problem_count != 0U)
        battle_core_die("mGBA warned/errored during Stage59 identity guard");

    printf(
        "{\"schema_version\":1,\"status\":\"PASS\","
        "\"rom_sha256\":\"%s\",\"hook_count\":3,"
        "\"probe_queries\":7,\"species_checked\":%u,"
        "\"canonical_names_checked\":%u,"
        "\"move_sets_preserved\":%u,\"warnings_errors\":0,"
        "\"claims\":{\"all_species_default_names_canonical\":true,"
        "\"normalizer_preserves_species\":true,"
        "\"name_only_guard_preserves_moves\":true,"
        "\"all_three_wild_hooks_target_stage59\":true}}\n",
        rom_sha256, checked, checked, moves_preserved);

    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
