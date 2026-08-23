/* T29 Stage 46 exact-ROM Windows catalog validation for libmGBA. */
#define CWR_RUNTIME_EMBEDDED
#include "mgba_codex_battle_rewards_smoke.c"

enum {
    CWC_COMMAND_ITEM = 15U,
    CWC_COMMAND_MON = 16U,
    CWC_ERROR_PRIVATE_BOUNDARY = 17U,
    CWC_OWNER_FLAG_CATALOG = 0x0008U,
    CWC_SAVE_BLOCK1_POINTER = 0x03005048U,
    CWC_MAP_GROUP = 96U,
    CWC_MAP_NUMBER = 5U,
    CWC_FIELD_CALLBACK = 0x08055E75U,
    CWC_SCRIPT_CONTEXT1_DISABLE = 0x08069231U,
    CWC_SCRIPT_CONTEXT2_DISABLE = 0x0806920DU,
    CWC_PSS_INPUT_SITE = 0x0808CD48U,
    CWC_PSS_CALLSITE_HOOK = 0x093784DBU,
    CWC_CAPABILITIES = 16383U,
};

static const char *const cwc_test_names[] = {
    "stage45_identity_and_rebound_hooks",
    "idle_reception_item_exactly_once",
    "idle_reception_mon_party_pc_delivery",
    "wrong_map_ui_result_and_open_reward_rejected",
    "six_member_batch_and_capacity_stop",
    "match_bound_reward_window_regression",
    "pc_bulk_release_runtime_unchanged",
    "warnings_zero",
};

static struct CwrCases cwc_load_cases(const char *path)
{
    char *source = cbr_read_text(path);
    bool exact = true;
    for (unsigned index = 0U; index < ARRAY_LEN(cwc_test_names); ++index) {
        char quoted[160];
        snprintf(quoted, sizeof(quoted), "\"%s\"", cwc_test_names[index]);
        exact = exact && cbr_occurrences(source, quoted) == 1U;
    }
    const char *runtime = cbr_find_key(source, "runtime");
    const char *payload = runtime ? cbr_find_key(runtime, "payload") : NULL;
    const char *owner = cbr_find_key(source, "owner");
    struct CwrCases result = {
        .exact_tests = exact,
        .payload = payload ? cbr_json_number(payload, "address") : 0U,
        .owner = owner ? cbr_json_number(owner, "address") : 0U,
        .owner_size = owner ? cbr_json_number(owner, "size") : 0U,
    };
    free(source);
    return result;
}

static bool cwc_prepare_idle(struct mCore *core,
                             const struct CwrSymbols *symbols,
                             const struct CbrSymbols *t27,
                             uint32_t nonce)
{
    cwr_clear(core, CWR_OWNER, CWR_OWNER_SIZE);
    if (cwr_call(core, symbols->test_recover, 0U, 0U, 0U, 0U) != 1U)
        return false;
    cbr_test_initialize(core, t27, nonce);
    uint32_t save1 = read32(core, CWC_SAVE_BLOCK1_POINTER);
    if (save1 < 0x02000000U || save1 >= 0x02040000U)
        return false;
    write8(core, save1 + 4U, CWC_MAP_GROUP);
    write8(core, save1 + 5U, CWC_MAP_NUMBER);
    write32_bytes(core, CWR_MAIN_CALLBACK2, CWC_FIELD_CALLBACK);
    (void)cwr_call(core, CWC_SCRIPT_CONTEXT2_DISABLE, 0U, 0U, 0U, 0U);
    (void)cwr_call(core, CWC_SCRIPT_CONTEXT1_DISABLE, 0U, 0U, 0U, 0U);
    (void)cwr_call(core, symbols->read_keys, 0U, 0U, 0U, 0U);
    bool exact = cbr_snapshot_valid(core)
        && read32(core, CBR_MAILBOX + 24U) == CWC_CAPABILITIES
        && cwr_owner_valid(core)
        && read16(core, CBR_STATE + 16U) == CBR_PHASE_IDLE
        && read8(core, CBR_STATE + CBR_STATE_ACTIVE) == 0U
        && read8(core, CWR_OWNER + CWR_OWNER_WINDOW) == CWR_WINDOW_CLOSED;
    if (!exact) {
        fprintf(stderr, "catalog idle setup snapshot=%u caps=%" PRIu32
                " owner=%u phase=%u active=%u window=%u main=%08" PRIx32
                " map=%u/%u\n",
                cbr_snapshot_valid(core), read32(core, CBR_MAILBOX + 24U),
                cwr_owner_valid(core), read16(core, CBR_STATE + 16U),
                read8(core, CBR_STATE + CBR_STATE_ACTIVE),
                read8(core, CWR_OWNER + CWR_OWNER_WINDOW),
                read32(core, CWR_MAIN_CALLBACK2),
                read8(core, save1 + 4U), read8(core, save1 + 5U));
    }
    return exact;
}

static bool cwc_item_exactly_once(struct mCore *core,
                                  const struct CwrSymbols *symbols,
                                  const struct CbrSymbols *t27)
{
    const uint16_t item_id = 100U;
    uint8_t payload[4];
    uint8_t request[96];
    if (!cwc_prepare_idle(core, symbols, t27, 0x46001001U))
        return false;
    cbr_put16(payload, 0U, item_id);
    cbr_put16(payload, 2U, 3U);
    unsigned before = cwr_bag_quantity(core, item_id);
    bool exact = cwr_send(core, symbols, CWC_COMMAND_ITEM,
                          payload, sizeof(payload), 1U, request);
    unsigned after = cwr_bag_quantity(core, item_id);
    exact = exact && after == before + 3U
        && cwr_owner_valid(core)
        && read8(core, CWR_OWNER + CWR_OWNER_WINDOW) == CWR_WINDOW_CLOSED
        && read8(core, CWR_OWNER + CWR_OWNER_PHASE) == CWR_PHASE_COMMITTED
        && read8(core, CWR_OWNER + CWR_OWNER_LAST_COMMAND) == CWC_COMMAND_ITEM
        && (read16(core, CWR_OWNER + CWR_OWNER_FLAGS)
            & CWC_OWNER_FLAG_CATALOG) != 0U;
    exact = exact && cwr_process(core, symbols, request, true, 0U)
        && cwr_bag_quantity(core, item_id) == after
        && read16(core, CWR_OWNER + CWR_OWNER_COMMITTED_COUNT) == 1U;
    if (after > before)
        (void)cwr_call(core, CWR_REMOVE_BAG_ITEM,
                       item_id, after - before, 0U, 0U);
    return exact;
}

static bool cwc_mon_party_pc(struct mCore *core,
                             const struct CwrSymbols *symbols,
                             const struct CbrSymbols *t27)
{
    uint8_t payload[32];
    uint8_t request[96];
    if (!cwc_prepare_idle(core, symbols, t27, 0x46002001U))
        return false;
    cwr_clear_boxes(core);
    cwr_install_party(core, 5U);
    cwr_mon_payload(payload, 25U, 50U, 4U);
    bool exact = cwr_send(core, symbols, CWC_COMMAND_MON,
                          payload, sizeof(payload), 1U, request)
        && read8(core, CWR_PLAYER_COUNT) == 6U
        && cbr_call(core, CWR_GET_MON_DATA,
                    CWR_PLAYER_PARTY + 5U * CWR_MON_SIZE,
                    11U, 0U, 0U) == 25U
        && read8(core, CWR_OWNER + CWR_OWNER_DESTINATION_KIND) == 1U;
    cwr_mon_payload(payload, 494U, 50U, 4U);
    exact = exact && cwr_send(core, symbols, CWC_COMMAND_MON,
                              payload, sizeof(payload), 2U, request)
        && cbr_call(core, CWR_GET_BOX_MON_DATA, 0U, 0U, 11U, 0U) == 494U
        && read8(core, CWR_OWNER + CWR_OWNER_DESTINATION_KIND) == 2U
        && read8(core, CWR_OWNER + CWR_OWNER_DESTINATION_BOX) == 0U
        && read8(core, CWR_OWNER + CWR_OWNER_DESTINATION_SLOT) == 0U;
    return exact;
}

static bool cwc_boundaries(struct mCore *core,
                           const struct CwrSymbols *symbols,
                           const struct CbrSymbols *t27)
{
    uint8_t payload[4];
    uint8_t request[96];
    cbr_put16(payload, 0U, 100U);
    cbr_put16(payload, 2U, 1U);
    if (!cwc_prepare_idle(core, symbols, t27, 0x46003001U))
        return false;
    uint32_t save1 = read32(core, CWC_SAVE_BLOCK1_POINTER);
    write8(core, save1 + 4U, CWC_MAP_GROUP + 1U);
    bool exact = cwr_send_error(
        core, symbols, CWC_COMMAND_ITEM, payload, sizeof(payload), 1U,
        CWC_ERROR_PRIVATE_BOUNDARY, request);
    write8(core, save1 + 4U, CWC_MAP_GROUP);
    (void)cwr_call(core, CBR_SCRIPT_CONTEXT1_SETUP,
                   CBR_RECEPTION_POINTER, 0U, 0U, 0U);
    (void)cwr_call(core, CBR_SCRIPT_CONTEXT2_ENABLE, 0U, 0U, 0U, 0U);
    exact = exact && cwr_send_error(
        core, symbols, CWC_COMMAND_ITEM, payload, sizeof(payload), 1U,
        CWC_ERROR_PRIVATE_BOUNDARY, request);
    (void)cwr_call(core, CWC_SCRIPT_CONTEXT2_DISABLE, 0U, 0U, 0U, 0U);
    (void)cwr_call(core, CWC_SCRIPT_CONTEXT1_DISABLE, 0U, 0U, 0U, 0U);
    write32_bytes(core, CWR_MAIN_CALLBACK2, CWR_RETURN_TO_FIELD);
    exact = exact && cwr_send_error(
        core, symbols, CWC_COMMAND_ITEM, payload, sizeof(payload), 1U,
        CWC_ERROR_PRIVATE_BOUNDARY, request);
    write32_bytes(core, CWR_MAIN_CALLBACK2, CWC_FIELD_CALLBACK);
    exact = exact && cwr_open(
        core, symbols, 0x46003002U, 0x46003003U, 10U, 1U)
        && cwr_send_error(
            core, symbols, CWC_COMMAND_ITEM, payload, sizeof(payload), 11U,
            CWC_ERROR_PRIVATE_BOUNDARY, request);
    return exact;
}

static bool cwc_six_and_capacity(struct mCore *core,
                                 const struct CwrSymbols *symbols,
                                 const struct CbrSymbols *t27)
{
    uint8_t payload[32];
    uint8_t request[96];
    if (!cwc_prepare_idle(core, symbols, t27, 0x46004001U))
        return false;
    cwr_clear_boxes(core);
    cwr_install_party(core, 0U);
    bool exact = true;
    for (unsigned index = 0U; index < 6U; ++index) {
        cwr_mon_payload(payload, (uint16_t)(25U + index), 50U, 4U);
        exact = exact && cwr_send(
            core, symbols, CWC_COMMAND_MON, payload, sizeof(payload),
            index + 1U, request);
    }
    exact = exact && read8(core, CWR_PLAYER_COUNT) == 6U
        && read16(core, CWR_OWNER + CWR_OWNER_COMMITTED_COUNT) == 6U;
    cwr_fill_boxes(core);
    cwr_mon_payload(payload, 494U, 50U, 4U);
    exact = exact && cwr_send_error(
        core, symbols, CWC_COMMAND_MON, payload, sizeof(payload), 7U,
        CWR_ERROR_STORAGE_FULL, request)
        && read8(core, CWR_PLAYER_COUNT) == 6U
        && read32(core, CWR_OWNER + CWR_OWNER_LAST_SEQUENCE) == 6U
        && read16(core, CWR_OWNER + CWR_OWNER_COMMITTED_COUNT) == 6U;
    return exact;
}

static bool cwc_reward_regression(struct mCore *core,
                                  const struct CwrSymbols *symbols)
{
    bool window = false;
    bool item = false;
    bool multiple = false;
    bool exact = cwr_item_and_close_test(
        core, symbols, &window, &item, &multiple);
    return exact && window && item && multiple;
}

static bool cwc_pc_runtime_unchanged(struct mCore *core)
{
    return read16(core, CWC_PSS_INPUT_SITE) == 0x4B00U
        && read16(core, CWC_PSS_INPUT_SITE + 2U) == 0x4718U
        && read32(core, CWC_PSS_INPUT_SITE + 4U) == CWC_PSS_CALLSITE_HOOK
        && read16(core, CWC_PSS_CALLSITE_HOOK & ~1U) != 0xFFFFU;
}

int main(int argc, char **argv)
{
    if (argc != 5)
        return 2;
    bool full = !strcmp(argv[4], "full");
    if (!full && strcmp(argv[4], "quick"))
        return 2;
    struct CwrSymbols symbols = cwr_load_symbols(argv[2]);
    struct CwrCases cases = cwc_load_cases(argv[3]);
    struct CbrSymbols t27 = cbr_load_symbols(argv[2]);
    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {
        .sample = NULL, .unixTime = fixed_unix_time,
        .serialize = NULL, .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core))
        cwr_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1]))
        cwr_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);
    run_trace_prefix(core);
    run_fixed_frames(core);
    struct Snapshot base = take_snapshot(core);

    bool tests[ARRAY_LEN(cwc_test_names)] = {false};
    tests[0] = cwr_roots_test(core, &symbols, &cases);
    restore_snapshot(core, &base);
    tests[1] = cwc_item_exactly_once(core, &symbols, &t27);
    restore_snapshot(core, &base);
    tests[2] = cwc_mon_party_pc(core, &symbols, &t27);
    restore_snapshot(core, &base);
    tests[3] = cwc_boundaries(core, &symbols, &t27);
    restore_snapshot(core, &base);
    tests[4] = cwc_six_and_capacity(core, &symbols, &t27);
    restore_snapshot(core, &base);
    tests[5] = cwc_reward_regression(core, &symbols);
    restore_snapshot(core, &base);
    tests[6] = cwc_pc_runtime_unchanged(core);
    tests[7] = log_problem_count == 0U;
    bool passed = true;
    for (unsigned index = 0U; index < ARRAY_LEN(tests); ++index)
        passed = passed && tests[index];

    char rom_sha[65], runner_source_sha[65], runner_binary_sha[65];
    char symbols_sha[65], cases_sha[65];
    sha256_file(argv[1], rom_sha);
    sha256_file(__FILE__, runner_source_sha);
    sha256_file(argv[0], runner_binary_sha);
    sha256_file(argv[2], symbols_sha);
    sha256_file(argv[3], cases_sha);
    fprintf(stderr, "mgba-windows-battle-catalog %s: ",
            full ? "full" : "quick");
    for (unsigned index = 0U; index < ARRAY_LEN(tests); ++index)
        fprintf(stderr, "%s=%u%s", cwc_test_names[index], tests[index],
                index + 1U == ARRAY_LEN(tests) ? "\n" : " ");
    printf("{\"schema_version\":1,\"task\":\"T29\",\"stage\":46,"
           "\"mode\":\"%s\",\"status\":\"%s\","
           "\"rom_sha256\":\"%s\","
           "\"runner_source_sha256\":\"%s\","
           "\"runner_binary_sha256\":\"%s\","
           "\"symbols_sha256\":\"%s\",\"cases_sha256\":\"%s\","
           "\"tests\":{",
           full ? "full" : "quick", passed ? "PASS" : "FAIL",
           rom_sha, runner_source_sha, runner_binary_sha, symbols_sha,
           cases_sha);
    for (unsigned index = 0U; index < ARRAY_LEN(tests); ++index)
        printf("\"%s\":%s%s", cwc_test_names[index],
               tests[index] ? "true" : "false",
               index + 1U == ARRAY_LEN(tests) ? "" : ",");
    printf("},\"total\":%zu,\"warnings\":%u,"
           "\"transaction_iterations\":%u,"
           "\"catalog_identity\":\"CB46:catalog:v1:normal-save\"}\n",
           ARRAY_LEN(tests), log_problem_count, full ? 8U : 1U);

    free(base.bytes);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return passed ? 0 : 1;
}
