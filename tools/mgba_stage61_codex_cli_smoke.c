/* Stage61 cold-boot Codex CLI/item/mon focused validation for libmGBA. */
#define CWC_RUNTIME_EMBEDDED
#include "mgba_windows_battle_catalog_smoke.c"

static bool stage61_runtime_ready(struct mCore *core)
{
    uint32_t nonce = read32(core, CBR_MAILBOX + 36U);
    return read32(core, CBR_STATE) == CBR_MAGIC
        && read32(core, CBR_STATE + 4U) == ~(uint32_t)CBR_MAGIC
        && read32(core, CBR_MAILBOX) == CBR_MAGIC
        && read16(core, CBR_MAILBOX + 4U) == 2U
        && read16(core, CBR_MAILBOX + 6U) == 2U
        && read16(core, CBR_MAILBOX + 8U) == 256U
        && read16(core, CBR_MAILBOX + 22U) == 44U
        && nonce != 0U
        && read32(core, CBR_MAILBOX + 40U) == ~nonce
        && cbr_snapshot_valid(core);
}

static bool stage61_prepare_idle(struct mCore *core,
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
        && read32(core, CBR_MAILBOX + 24U) == 32767U
        && cwr_owner_valid(core)
        && read16(core, CBR_STATE + 16U) == CBR_PHASE_IDLE
        && read8(core, CBR_STATE + CBR_STATE_ACTIVE) == 0U
        && read8(core, CWR_OWNER + CWR_OWNER_WINDOW) == CWR_WINDOW_CLOSED;
}

static bool stage61_item_exactly_once(struct mCore *core,
                                      const struct CwrSymbols *symbols,
                                      const struct CbrSymbols *t27)
{
    const uint16_t item_id = 110U;
    uint8_t payload[4];
    uint8_t request[96];
    if (!stage61_prepare_idle(core, symbols, t27, 0x61001001U))
        return false;
    cbr_put16(payload, 0U, item_id);
    cbr_put16(payload, 2U, 1U);
    unsigned before = cwr_bag_quantity(core, item_id);
    bool exact = cwr_send(core, symbols, CWC_COMMAND_ITEM,
                          payload, sizeof(payload), 1U, request);
    unsigned after = cwr_bag_quantity(core, item_id);
    exact = exact && after == before + 1U
        && cwr_owner_valid(core)
        && read8(core, CWR_OWNER + CWR_OWNER_WINDOW) == CWR_WINDOW_CLOSED
        && read8(core, CWR_OWNER + CWR_OWNER_PHASE) == CWR_PHASE_COMMITTED
        && read8(core, CWR_OWNER + CWR_OWNER_LAST_COMMAND) == CWC_COMMAND_ITEM
        && (read16(core, CWR_OWNER + CWR_OWNER_FLAGS)
            & CWC_OWNER_FLAG_CATALOG) != 0U
        && cwr_process(core, symbols, request, true, 0U)
        && cwr_bag_quantity(core, item_id) == after
        && read16(core, CWR_OWNER + CWR_OWNER_COMMITTED_COUNT) == 1U;
    if (after > before)
        (void)cwr_call(core, CWR_REMOVE_BAG_ITEM,
                       item_id, after - before, 0U, 0U);
    return exact;
}

static bool stage61_mon_party_pc(struct mCore *core,
                                 const struct CwrSymbols *symbols,
                                 const struct CbrSymbols *t27)
{
    uint8_t payload[32];
    uint8_t request[96];
    if (!stage61_prepare_idle(core, symbols, t27, 0x61002001U))
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
    return exact && cwr_send(core, symbols, CWC_COMMAND_MON,
                             payload, sizeof(payload), 2U, request)
        && cbr_call(core, CWR_GET_BOX_MON_DATA, 0U, 0U, 11U, 0U) == 494U
        && read8(core, CWR_OWNER + CWR_OWNER_DESTINATION_KIND) == 2U
        && read8(core, CWR_OWNER + CWR_OWNER_DESTINATION_BOX) == 0U
        && read8(core, CWR_OWNER + CWR_OWNER_DESTINATION_SLOT) == 0U;
}

int main(int argc, char **argv)
{
    if (argc != 4)
        return 2;
    struct CwrSymbols symbols = cwr_load_symbols(argv[2]);
    struct CbrSymbols t27 = cbr_load_symbols(argv[2]);
    char *stage61_symbols = cbr_read_text(argv[3]);
    uint32_t bootstrap = cbr_json_symbol(
        stage61_symbols, "Stage61Codex_ReadKeysBootstrapAdapter");
    free(stage61_symbols);

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

    bool root = read32(core, CWR_READ_KEYS_POINTER) == (bootstrap | 1U);
    bool cold_boot = stage61_runtime_ready(core);
    struct Snapshot base = take_snapshot(core);

    bool item = stage61_item_exactly_once(core, &symbols, &t27);
    restore_snapshot(core, &base);
    bool mon = stage61_mon_party_pc(core, &symbols, &t27);
    restore_snapshot(core, &base);
    cbr_test_initialize(core, &t27, 0x61004001U);
    cbr_seed_player_party(core);
    bool codex = cbr_configure(core, &t27, 0U);
    bool warnings = log_problem_count == 0U;
    bool passed = root && cold_boot && item && mon && codex && warnings;

    printf("{\"schema_version\":1,\"stage\":61,\"status\":\"%s\","
           "\"tests\":{\"read_keys_root\":%s,\"cold_boot_runtime\":%s,"
           "\"catalog_item\":%s,\"catalog_mon\":%s,"
           "\"codex_configure\":%s,\"warnings_zero\":%s}}\n",
           passed ? "PASS" : "FAIL",
           root ? "true" : "false",
           cold_boot ? "true" : "false",
           item ? "true" : "false",
           mon ? "true" : "false",
           codex ? "true" : "false",
           warnings ? "true" : "false");

    free(base.bytes);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return passed ? 0 : 1;
}
