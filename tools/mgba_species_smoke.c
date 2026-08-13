/* T07: create one DPE-appended Species in real party memory with libmGBA. */
#define main t01_ai_fixture_bundled_entry_point
#include "mgba_ai_fixture_runner.c"
#undef main

enum {
    SPECIES_SMOKE_CREATE_MON = 0x0803D1C1,
    SPECIES_SMOKE_LEVEL = 20,
    MON_DATA_SPECIES = 11,
    MON_DATA_LEVEL = 56,
    MON_DATA_MAX_HP = 58,
};

int main(int argc, char **argv) {
    if (argc != 4) {
        fprintf(stderr, "usage: %s ROM EXPECTED_SHA256 APPENDED_SPECIES_ID\n", argv[0]);
        return 2;
    }
    char actual_sha256[65];
    sha256_file(argv[1], actual_sha256);
    if (strlen(argv[2]) != 64 || strcmp(actual_sha256, argv[2]) != 0) {
        die("ROM SHA-256 mismatch");
    }
    char *end = NULL;
    unsigned long parsed = strtoul(argv[3], &end, 0);
    if (!end || *end || parsed < 412 || parsed > UINT16_MAX) {
        die("invalid appended Species ID");
    }
    uint16_t species = (uint16_t)parsed;
    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {.sample = NULL, .unixTime = fixed_unix_time,
                             .serialize = NULL, .deserialize = NULL};
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core)) die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1])) die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);
    run_boot_trace(core);
    if (log_problem_count != 0) die("mGBA emitted warning/error diagnostics");

    for (unsigned byte = 0; byte < POKEMON_SIZE; ++byte) {
        write8(core, ADDR_PLAYER_PARTY + byte, 0);
    }
    uint32_t original_sp = (uint32_t)read_register(core, "sp");
    uint32_t call_sp = (original_sp - 16U) & ~7U;
    for (unsigned byte = 0; byte < 16; ++byte) write8(core, call_sp + byte, 0);
    write_register(core, "sp", call_sp);
    struct RomCall result = call_rom_args(
        core, SPECIES_SMOKE_CREATE_MON, ADDR_PLAYER_PARTY,
        species, SPECIES_SMOKE_LEVEL, 0);
    write_register(core, "sp", original_sp);
    uint32_t read_species = get_mon_data(core, ADDR_PLAYER_PARTY, MON_DATA_SPECIES);
    uint32_t read_level = get_mon_data(core, ADDR_PLAYER_PARTY, MON_DATA_LEVEL);
    uint32_t read_max_hp = get_mon_data(core, ADDR_PLAYER_PARTY, MON_DATA_MAX_HP);
    if (read_species != species
        || read_level != SPECIES_SMOKE_LEVEL || read_max_hp == 0
        || log_problem_count != 0) {
        die("appended Species party creation failed");
    }
    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"fixture\":\"t07_appended_species_party_creation\","
           "\"rom_sha256\":\"%s\",\"species\":%u,\"level\":%u,"
           "\"max_hp\":%u,\"instructions\":%" PRIu64 ","
           "\"warnings_errors\":0,\"artifacts_written\":[]}\n",
           actual_sha256, species, (unsigned)read_level, (unsigned)read_max_hp,
           result.instructions);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return 0;
}
