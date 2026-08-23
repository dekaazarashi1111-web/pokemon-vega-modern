/* T30 Stage 47 exact-ROM Box 14⇔Windows vault validation for libmGBA. */
#define CWC_RUNTIME_EMBEDDED
#include "mgba_windows_battle_catalog_smoke.c"

enum {
    VW_COMMAND_SCAN = 17U,
    VW_COMMAND_EXPORT = 18U,
    VW_COMMAND_REMOVE = 19U,
    VW_COMMAND_IMPORT = 20U,
    VW_ERROR_PRIVATE_BOUNDARY = 17U,
    VW_ERROR_MAIL = 29U,
    VW_OWNER_FLAG = 0x0010U,
    VW_TRANSFER = 0x0203D880U,
    VW_TRANSFER_SIZE = 128U,
    VW_RECORD_OFFSET = 44U,
    VW_RECORD_SIZE = 80U,
    VW_BLOCK_CRC_OFFSET = 124U,
    VW_MAGIC = 0x31564257U,
    VW_ABI_CRC = 0x41876DF7U,
    VW_BOX = 13U,
    VW_CAPABILITIES = 32767U,
    VW_SET_BOX_MON_DATA = 0x0803FBC5U,
};

static const char *const vw_test_names[] = {
    "stage46_identity_and_rebound_hooks",
    "box14_scan_export_exact80",
    "deposit_remove_normal_save",
    "withdraw_import_exact80_and_reload",
    "any_field_busy_and_mail_rejected",
    "catalog_reward_regression",
    "warnings_zero",
};

static struct CwrCases vw_load_cases(const char *path)
{
    char *source = cbr_read_text(path);
    bool exact = true;
    for (unsigned index = 0U; index < ARRAY_LEN(vw_test_names); ++index) {
        char quoted[160];
        snprintf(quoted, sizeof(quoted), "\"%s\"", vw_test_names[index]);
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

static bool vw_prepare_idle(struct mCore *core,
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
    return cbr_snapshot_valid(core)
        && read32(core, CBR_MAILBOX + 24U) == VW_CAPABILITIES
        && cwr_owner_valid(core)
        && read16(core, CBR_STATE + 16U) == CBR_PHASE_IDLE
        && read8(core, CBR_STATE + CBR_STATE_ACTIVE) == 0U
        && read8(core, CWR_OWNER + CWR_OWNER_WINDOW) == CWR_WINDOW_CLOSED;
}

static uint32_t vw_box_address(struct mCore *core, unsigned slot)
{
    uint32_t storage = read32(core, CWR_STORAGE_POINTER);
    return storage + 4U + ((VW_BOX * CWR_BOX_CAPACITY) + slot) * VW_RECORD_SIZE;
}

static void vw_read_bytes(struct mCore *core, uint32_t address,
                          uint8_t *out, size_t size)
{
    for (size_t index = 0U; index < size; ++index)
        out[index] = read8(core, address + (uint32_t)index);
}

static void vw_write_bytes(struct mCore *core, uint32_t address,
                           const uint8_t *raw, size_t size)
{
    for (size_t index = 0U; index < size; ++index)
        write8(core, address + (uint32_t)index, raw[index]);
}

static uint16_t vw_get16(const uint8_t *raw, size_t offset)
{
    return (uint16_t)raw[offset]
        | ((uint16_t)raw[offset + 1U] << 8U);
}

static uint32_t vw_get32(const uint8_t *raw, size_t offset)
{
    return (uint32_t)raw[offset]
        | ((uint32_t)raw[offset + 1U] << 8U)
        | ((uint32_t)raw[offset + 2U] << 16U)
        | ((uint32_t)raw[offset + 3U] << 24U);
}

static bool vw_transfer_valid(struct mCore *core, uint16_t command,
                              uint8_t slot, uint32_t nonce,
                              uint8_t out[VW_TRANSFER_SIZE])
{
    vw_read_bytes(core, VW_TRANSFER, out, VW_TRANSFER_SIZE);
    uint32_t generation = vw_get32(out, 12U);
    return vw_get32(out, 0U) == VW_MAGIC
        && vw_get32(out, 4U) == ~(uint32_t)VW_MAGIC
        && vw_get16(out, 8U) == 1U
        && vw_get16(out, 10U) == VW_TRANSFER_SIZE
        && generation != 0U
        && vw_get32(out, 16U) == ~generation
        && vw_get16(out, 20U) == command
        && vw_get16(out, 22U) == 1U
        && out[24] == VW_BOX && out[25] == slot
        && vw_get32(out, 36U) == VW_ABI_CRC
        && vw_get32(out, 40U) == nonce
        && vw_get32(out, VW_BLOCK_CRC_OFFSET)
            == cbr_crc_bytes(out, VW_BLOCK_CRC_OFFSET);
}

static void vw_install_mon(struct mCore *core, unsigned slot,
                           uint16_t species, uint32_t personality)
{
    cwr_create_mon(core, CWR_SCRATCH, species, 50U, personality);
    (void)cbr_call(core, CWR_SET_BOX_MON, VW_BOX, slot, CWR_SCRATCH, 0U);
}

static bool vw_scan_export_test(struct mCore *core,
                                const struct CwrSymbols *symbols,
                                const struct CbrSymbols *t27)
{
    const uint32_t nonce = 0x47001001U;
    uint8_t request[96], transfer[VW_TRANSFER_SIZE], expected[VW_RECORD_SIZE];
    uint8_t slot = 0U;
    if (!vw_prepare_idle(core, symbols, t27, nonce))
        return false;
    cwr_clear_boxes(core);
    vw_install_mon(core, 0U, 25U, 0x11112222U);
    vw_install_mon(core, 5U, 494U, 0x33334444U);
    vw_read_bytes(core, vw_box_address(core, 0U), expected, sizeof(expected));
    bool exact = cwr_send(core, symbols, VW_COMMAND_SCAN,
                          NULL, 0U, 1U, request)
        && vw_transfer_valid(core, VW_COMMAND_SCAN, 0xFFU, nonce, transfer)
        && vw_get16(transfer, 26U) == 0U
        && vw_get32(transfer, 28U) == ((1U << 0U) | (1U << 5U));
    exact = exact && cwr_send(core, symbols, VW_COMMAND_EXPORT,
                              &slot, 1U, 2U, request)
        && vw_transfer_valid(core, VW_COMMAND_EXPORT, slot, nonce, transfer)
        && vw_get16(transfer, 26U) == VW_RECORD_SIZE
        && vw_get32(transfer, 32U)
            == cbr_crc_bytes(expected, sizeof(expected))
        && !memcmp(transfer + VW_RECORD_OFFSET, expected, sizeof(expected));
    return exact;
}

static bool vw_remove_test(struct mCore *core,
                           const struct CwrSymbols *symbols,
                           const struct CbrSymbols *t27)
{
    uint8_t request[96], payload[5], expected[VW_RECORD_SIZE];
    if (!vw_prepare_idle(core, symbols, t27, 0x47002001U))
        return false;
    cwr_clear_boxes(core);
    vw_install_mon(core, 0U, 494U, 0x55667788U);
    vw_read_bytes(core, vw_box_address(core, 0U), expected, sizeof(expected));
    payload[0] = 0U;
    cbr_put32(payload, 1U, cbr_crc_bytes(expected, sizeof(expected)));
    bool exact = cwr_send(core, symbols, VW_COMMAND_REMOVE,
                          payload, sizeof(payload), 1U, request)
        && cbr_call(core, CWR_GET_BOX_MON_DATA, VW_BOX, 0U, 11U, 0U) == 0U
        && (read16(core, CWR_OWNER + CWR_OWNER_FLAGS) & VW_OWNER_FLAG) != 0U
        && read8(core, CWR_OWNER + CWR_OWNER_LAST_COMMAND) == VW_COMMAND_REMOVE;
    (void)cbr_call(core, CWR_LOAD_GAME_DATA, 0U, 0U, 0U, 0U);
    return exact
        && cbr_call(core, CWR_GET_BOX_MON_DATA, VW_BOX, 0U, 11U, 0U) == 0U;
}

static void vw_build_input(uint8_t transfer[VW_TRANSFER_SIZE], uint8_t slot,
                           uint32_t generation, uint32_t nonce,
                           const uint8_t record[VW_RECORD_SIZE])
{
    memset(transfer, 0, VW_TRANSFER_SIZE);
    cbr_put32(transfer, 0U, VW_MAGIC);
    cbr_put32(transfer, 4U, ~VW_MAGIC);
    cbr_put16(transfer, 8U, 1U);
    cbr_put16(transfer, 10U, VW_TRANSFER_SIZE);
    cbr_put32(transfer, 12U, generation);
    cbr_put32(transfer, 16U, ~generation);
    cbr_put16(transfer, 20U, VW_COMMAND_IMPORT);
    cbr_put16(transfer, 22U, 2U);
    transfer[24] = VW_BOX;
    transfer[25] = slot;
    cbr_put16(transfer, 26U, VW_RECORD_SIZE);
    cbr_put32(transfer, 32U, cbr_crc_bytes(record, VW_RECORD_SIZE));
    cbr_put32(transfer, 36U, VW_ABI_CRC);
    cbr_put32(transfer, 40U, nonce);
    memcpy(transfer + VW_RECORD_OFFSET, record, VW_RECORD_SIZE);
    cbr_put32(transfer, VW_BLOCK_CRC_OFFSET,
              cbr_crc_bytes(transfer, VW_BLOCK_CRC_OFFSET));
}

static bool vw_import_reload_test(struct mCore *core,
                                  const struct CwrSymbols *symbols,
                                  const struct CbrSymbols *t27)
{
    const uint32_t nonce = 0x47003001U;
    const uint32_t generation = 0x12340001U;
    uint8_t request[96], payload[9], transfer[VW_TRANSFER_SIZE];
    uint8_t expected[VW_RECORD_SIZE], loaded[VW_RECORD_SIZE];
    if (!vw_prepare_idle(core, symbols, t27, nonce))
        return false;
    cwr_clear_boxes(core);
    cwr_create_mon(core, CWR_SCRATCH, 25U, 50U, 0xA1B2C3D4U);
    vw_read_bytes(core, CWR_SCRATCH, expected, sizeof(expected));
    vw_build_input(transfer, 7U, generation, nonce, expected);
    vw_write_bytes(core, VW_TRANSFER, transfer, sizeof(transfer));
    payload[0] = 7U;
    cbr_put32(payload, 1U, generation);
    cbr_put32(payload, 5U, cbr_crc_bytes(expected, sizeof(expected)));
    bool exact = cwr_send(core, symbols, VW_COMMAND_IMPORT,
                          payload, sizeof(payload), 1U, request);
    vw_read_bytes(core, vw_box_address(core, 7U), loaded, sizeof(loaded));
    exact = exact && !memcmp(loaded, expected, sizeof(expected));
    (void)cbr_call(core, CWR_ZERO_BOX_MON, VW_BOX, 7U, 0U, 0U);
    uint32_t load = cbr_call(core, CWR_LOAD_GAME_DATA, 0U, 0U, 0U, 0U);
    vw_read_bytes(core, vw_box_address(core, 7U), loaded, sizeof(loaded));
    return exact && load == 1U
        && !memcmp(loaded, expected, sizeof(expected));
}

static bool vw_context_mail_test(struct mCore *core,
                                 const struct CwrSymbols *symbols,
                                 const struct CbrSymbols *t27)
{
    uint8_t request[96];
    if (!vw_prepare_idle(core, symbols, t27, 0x47004001U))
        return false;
    uint32_t save1 = read32(core, CWC_SAVE_BLOCK1_POINTER);
    write8(core, save1 + 4U, CWC_MAP_GROUP + 1U);
    bool exact = cwr_send(core, symbols, VW_COMMAND_SCAN,
                          NULL, 0U, 1U, request);
    if (!vw_prepare_idle(core, symbols, t27, 0x47004002U))
        return false;
    (void)cwr_call(core, CBR_SCRIPT_CONTEXT2_ENABLE, 0U, 0U, 0U, 0U);
    exact = exact && cwr_send_error(core, symbols, VW_COMMAND_SCAN,
                                    NULL, 0U, 1U,
                                    VW_ERROR_PRIVATE_BOUNDARY, request);
    if (!vw_prepare_idle(core, symbols, t27, 0x47004003U))
        return false;
    cwr_clear_boxes(core);
    cwr_create_mon(core, CWR_SCRATCH, 25U, 50U, 0x01020304U);
    cwr_write16(core, CWR_SCRATCH + 0x100U, 121U);
    (void)cbr_call(core, VW_SET_BOX_MON_DATA, CWR_SCRATCH, 12U,
                   CWR_SCRATCH + 0x100U, 0U);
    (void)cbr_call(core, CWR_SET_BOX_MON, VW_BOX, 0U, CWR_SCRATCH, 0U);
    exact = exact && cbr_call(core, CWR_GET_BOX_MON_DATA,
                              VW_BOX, 0U, 12U, 0U) == 121U
        && cwr_send_error(core, symbols, VW_COMMAND_SCAN,
                          NULL, 0U, 1U, VW_ERROR_MAIL, request);
    return exact;
}

static bool vw_catalog_reward_regression(struct mCore *core,
                                         const struct CwrSymbols *symbols,
                                         const struct CbrSymbols *t27)
{
    uint8_t payload[4], request[96];
    if (!vw_prepare_idle(core, symbols, t27, 0x47005001U))
        return false;
    uint32_t save1 = read32(core, CWC_SAVE_BLOCK1_POINTER);
    write8(core, save1 + 4U, CWC_MAP_GROUP + 1U);
    write8(core, save1 + 5U, CWC_MAP_NUMBER + 1U);
    cbr_put16(payload, 0U, 100U);
    cbr_put16(payload, 2U, 1U);
    unsigned before = cwr_bag_quantity(core, 100U);
    bool catalog = cwr_send(core, symbols, CWC_COMMAND_ITEM,
                            payload, sizeof(payload), 1U, request)
        && cwr_bag_quantity(core, 100U) == before + 1U;
    if (cwr_bag_quantity(core, 100U) > before)
        (void)cwr_call(core, CWR_REMOVE_BAG_ITEM, 100U, 1U, 0U, 0U);
    return catalog && cwc_reward_regression(core, symbols);
}

int main(int argc, char **argv)
{
    if (argc != 5 || strcmp(argv[4], "quick"))
        return 2;
    struct CwrSymbols symbols = cwr_load_symbols(argv[2]);
    struct CwrCases cases = vw_load_cases(argv[3]);
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

    bool tests[ARRAY_LEN(vw_test_names)] = {false};
    tests[0] = cwr_roots_test(core, &symbols, &cases);
    restore_snapshot(core, &base);
    tests[1] = vw_scan_export_test(core, &symbols, &t27);
    restore_snapshot(core, &base);
    tests[2] = vw_remove_test(core, &symbols, &t27);
    restore_snapshot(core, &base);
    tests[3] = vw_import_reload_test(core, &symbols, &t27);
    restore_snapshot(core, &base);
    tests[4] = vw_context_mail_test(core, &symbols, &t27);
    restore_snapshot(core, &base);
    tests[5] = vw_catalog_reward_regression(core, &symbols, &t27);
    tests[6] = log_problem_count == 0U;
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
    fprintf(stderr, "mgba-windows-box14-vault quick: ");
    for (unsigned index = 0U; index < ARRAY_LEN(tests); ++index)
        fprintf(stderr, "%s=%u%s", vw_test_names[index], tests[index],
                index + 1U == ARRAY_LEN(tests) ? "\n" : " ");
    printf("{\"schema_version\":1,\"task\":\"T30\",\"stage\":47,"
           "\"mode\":\"quick\",\"status\":\"%s\","
           "\"rom_sha256\":\"%s\","
           "\"runner_source_sha256\":\"%s\","
           "\"runner_binary_sha256\":\"%s\","
           "\"symbols_sha256\":\"%s\",\"cases_sha256\":\"%s\","
           "\"tests\":{",
           passed ? "PASS" : "FAIL", rom_sha, runner_source_sha,
           runner_binary_sha, symbols_sha, cases_sha);
    for (unsigned index = 0U; index < ARRAY_LEN(tests); ++index)
        printf("\"%s\":%s%s", vw_test_names[index],
               tests[index] ? "true" : "false",
               index + 1U == ARRAY_LEN(tests) ? "" : ",");
    printf("},\"total\":%zu,\"warnings\":%u,"
           "\"vault_identity\":\"WBV47:box14:raw80:v1\"}\n",
           ARRAY_LEN(tests), log_problem_count);

    free(base.bytes);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return passed ? 0 : 1;
}
