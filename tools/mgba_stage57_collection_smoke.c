/* Stage57 exact-ROM wrapper around the exhaustive Collection Supply smoke. */
#define COLLECTION_SUPPLY_EMBEDDED
#include "mgba_collection_supply_v1_smoke.c"

#define S57_COLLECTION_EXPECTED_ROM_SHA256 \
    "546136a6baa26efd7a70c2b6826bf902c4841a4a1113cb53bfdc44c77971663d"

static bool s57_collection_probe_test(
    struct mCore *core,
    const struct CsSymbols *symbols,
    const struct CsCases *cases,
    uint32_t stage57_wild_adapter)
{
    static const uint32_t expected[] = {
        CS_ABI_VERSION, 388U, 34U, 999U, 14U, 292U, 217U,
        CS_OWNER, CS_OWNER_SIZE,
    };
    bool passed = cases->exact_tests;
    for (unsigned query = 0U; query < ARRAY_LEN(expected); ++query)
        passed = passed && cs_call(core, symbols->probe, query, 0U, 0U, 0U)
            == expected[query];
    return passed
        && read32(core, CS_READ_KEYS_SITE) == symbols->read_keys
        && cs_jump_root(core, CS_SAVE_LOAD_SITE, symbols->save_load)
        && cs_jump_root(core, CS_LAND_WATER_SITE, stage57_wild_adapter)
        && cs_jump_root(core, CS_WILD_END_SITE, symbols->wild_end);
}

int main(int argc, char **argv)
{
    if (argc != 7) {
        fprintf(stderr,
                "usage: %s ROM COLLECTION_SYMBOLS STAGE57_SYMBOLS "
                "CASES quick|full SAVE\n", argv[0]);
        return 2;
    }
    bool full = !strcmp(argv[5], "full");
    if (!full && strcmp(argv[5], "quick"))
        return 2;

    char rom_sha[65];
    sha256_file(argv[1], rom_sha);
    if (strcmp(rom_sha, S57_COLLECTION_EXPECTED_ROM_SHA256) != 0) {
        fprintf(stderr, "Stage57 Collection ROM SHA-256 differs: %s\n", rom_sha);
        return 1;
    }
    (void)argv[6];
    struct CsSymbols symbols = cs_load_symbols(argv[2]);
    struct CsCases cases = cs_load_cases(argv[4]);
    struct CwrSymbols vault = cwr_load_symbols(argv[2]);
    struct CbrSymbols t27 = cbr_load_symbols(argv[2]);
    char *stage57_symbols = cbr_read_text(argv[3]);
    uint32_t stage57_wild_adapter = cbr_json_symbol(
        stage57_symbols, "Stage57Debug_TryGenerateWildMonAdapter");
    free(stage57_symbols);
    if (stage57_wild_adapter < 0x08000001U
        || stage57_wild_adapter >= 0x0A000000U
        || !(stage57_wild_adapter & 1U))
        cwr_die("Stage57 wild adapter symbol differs");

    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {
        .sample = NULL, .unixTime = fixed_unix_time,
        .serialize = NULL, .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core))
        cwr_die("Stage57 Collection mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1]))
        cwr_die("Stage57 Collection ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);
    run_trace_prefix(core);
    run_fixed_frames(core);
    struct Snapshot base = take_snapshot(core);

    bool tests[ARRAY_LEN(cs_test_names)] = {false};
    tests[0] = s57_collection_probe_test(
        core, &symbols, &cases, stage57_wild_adapter);
    restore_snapshot(core, &base);
    tests[1] = cs_owner_test(core, &symbols);
    restore_snapshot(core, &base);
    tests[2] = cs_transaction_test(core, &symbols, &cases);
    restore_snapshot(core, &base);
    tests[3] = cs_form_gift_test(core, &symbols, &cases);
    restore_snapshot(core, &base);
    bool toggle = cs_gmax_toggle_test(core, &symbols, &cases);
    restore_snapshot(core, &base);
    bool vault_batch = cs_vault_batch_once(
        core, &vault, &t27, full ? 0x57005002U : 0x57005001U);
    bool mail = vw_context_mail_test(core, &vault, &t27);
    tests[4] = toggle && vault_batch && mail;
    restore_snapshot(core, &base);
    unsigned iterations = full ? cases.full_iterations : cases.quick_iterations;
    tests[5] = iterations > 0U
        && cs_raid_test(core, &symbols, &cases, iterations);
    restore_snapshot(core, &base);
    tests[6] = cs_world_hosts_test(core, &symbols, &cases);
    tests[7] = cases.stage55_fixtures == 22U
        && cases.stage55_processes == 2U;
    tests[8] = log_problem_count == 0U;
    bool passed = true;
    for (unsigned index = 0U; index < ARRAY_LEN(tests); ++index)
        passed = passed && tests[index];

    char runner_sha[65], symbols_sha[65], stage57_symbols_sha[65], cases_sha[65];
    sha256_file(argv[0], runner_sha);
    sha256_file(argv[2], symbols_sha);
    sha256_file(argv[3], stage57_symbols_sha);
    sha256_file(argv[4], cases_sha);
    printf("{\"schema_version\":1,\"task\":"
           "\"USER-20260827-STAGE56-COMPREHENSIVE-DEBUG-REPAIR\","
           "\"stage\":57,\"mode\":\"%s\",\"status\":\"%s\","
           "\"result_identity\":\"S57:CSV56:388:34:999:14:292:217:raw80x30\","
           "\"rom_sha256\":\"%s\",\"runner_sha256\":\"%s\","
           "\"symbols_sha256\":\"%s\","
           "\"stage57_symbols_sha256\":\"%s\","
           "\"cases_sha256\":\"%s\",\"tests\":{",
           argv[5], passed ? "PASS" : "FAIL", rom_sha, runner_sha,
           symbols_sha, stage57_symbols_sha, cases_sha);
    for (unsigned index = 0U; index < ARRAY_LEN(tests); ++index)
        printf("\"%s\":%s%s", cs_test_names[index],
               tests[index] ? "true" : "false",
               index + 1U == ARRAY_LEN(tests) ? "" : ",");
    printf("},\"total\":%zu,\"warnings\":%u,\"warnings_errors\":%u,"
           "\"coverage\":{\"forms\":388,\"gmax\":34,\"items\":999,"
           "\"hosts\":14,\"pool_entries\":292,\"reward_entries\":217,"
           "\"vault_batch\":30,\"raw_record_bytes\":80}}\n",
           ARRAY_LEN(tests), log_problem_count, log_problem_count);

    free(base.bytes);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return passed ? 0 : 1;
}
