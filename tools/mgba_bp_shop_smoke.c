/* Focused stage27 exact-ROM smoke for the manifest-backed Factory BP shop. */
#define main mgba_regression_smoke_embedded_main
#include "mgba_regression_smoke.c"
#undef main

#include <string.h>

#define BP_MAX_CALL_STEPS UINT64_C(30000000)
#define BP_SAVE_FILE_SIZE UINT32_C(0x20000)
#define BP_ABI_MARKER UINT32_C(0xB927)
#define BP_LEDGER UINT32_C(0x0203D000)
#define BP_LEDGER_SIZE UINT32_C(0x800)
#define BP_FACTORY_OFFSET UINT32_C(0x392)
#define BP_BALANCE_OFFSET UINT32_C(0)
#define BP_KANTO_TRAVEL_OFFSET UINT32_C(16)
#define BP_KANTO_VISITED_OFFSET UINT32_C(17)
#define BP_HALL_OF_FAME_OFFSET UINT32_C(18)
#define BP_LEAGUE_I_OFFSET UINT32_C(20)
#define BP_LEAGUE_II_OFFSET UINT32_C(21)
#define BP_CERTIFICATIONS_OFFSET UINT32_C(24)
#define BP_FLASH_LEDGER UINT32_C(0x0E01F064)
#define BP_FLAG_SET UINT32_C(0x0806DE75)
#define BP_FLAG_CLEAR UINT32_C(0x0806DE9D)
#define BP_CHECK_BAG UINT32_C(0x08099949)
#define BP_ADD_BAG UINT32_C(0x08099A8D)
#define BP_REMOVE_BAG UINT32_C(0x08099BE1)
#define BP_SAVE_LOAD UINT32_C(0x080DB4E5)
#define BP_FLAG_BADGE_1 UINT32_C(0x0820)
#define BP_FLAG_DH_CLEAR UINT32_C(0x114B)
#define BP_ITEM_EXP_XS UINT32_C(988)
#define BP_ITEM_EXP_S UINT32_C(989)
#define BP_ITEM_GOLD_CAP UINT32_C(854)
#define BP_RESULT_SUCCESS UINT32_C(0)
#define BP_RESULT_LOCKED UINT32_C(3)
#define BP_RESULT_INSUFFICIENT UINT32_C(14)
#define BP_RESULT_BAG_FULL UINT32_C(15)

static void bp_die(const char *message)
{
    fprintf(stderr, "mgba-bp-shop-smoke: %s\n", message);
    exit(1);
}

static void bp_phase(const char *phase)
{
    fprintf(stderr, "mgba-bp-shop-smoke: phase=%s\n", phase);
    fflush(stderr);
}

static void bp_initialize_save(const char *path)
{
    FILE *stream = fopen(path, "wb");
    if (stream == NULL)
        bp_die("temporary save creation failed");
    uint8_t block[4096];
    memset(block, 0xFF, sizeof(block));
    uint32_t remaining = BP_SAVE_FILE_SIZE;
    while (remaining != 0U) {
        size_t amount = remaining < sizeof(block) ? remaining : sizeof(block);
        if (fwrite(block, 1U, amount, stream) != amount) {
            (void)fclose(stream);
            bp_die("temporary save initialization failed");
        }
        remaining -= (uint32_t)amount;
    }
    if (fclose(stream) != 0)
        bp_die("temporary save close failed");
}

static void bp_write8(struct mCore *core, uint32_t address, uint8_t value)
{
    core->rawWrite8(core, address, -1, value);
}

static void bp_write16(struct mCore *core, uint32_t address, uint16_t value)
{
    core->rawWrite16(core, address, -1, value);
}

static uint32_t bp_read_u32_unaligned(struct mCore *core, uint32_t address)
{
    return (uint32_t)read8(core, address)
        | ((uint32_t)read8(core, address + 1U) << 8U)
        | ((uint32_t)read8(core, address + 2U) << 16U)
        | ((uint32_t)read8(core, address + 3U) << 24U);
}

static void bp_clear_region(struct mCore *core, uint32_t address, size_t size)
{
    for (size_t index = 0; index < size; ++index)
        bp_write8(core, address + (uint32_t)index, 0U);
}

static uint64_t bp_hash_region(struct mCore *core, uint32_t address,
                               size_t size)
{
    uint64_t hash = UINT64_C(14695981039346656037);
    for (size_t index = 0; index < size; ++index) {
        hash ^= read8(core, address + (uint32_t)index);
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

static uint32_t bp_call_thumb(struct mCore *core, uint32_t function,
                              uint32_t r0, uint32_t r1,
                              uint32_t r2, uint32_t r3)
{
    struct CpuContext original = capture_cpu(core);
    write_register(core, "cpsr", original.registers[16] | 0xA0);
    write_register(core, "lr", (int32_t)UINT32_C(0x08000001));
    write_register(core, "r0", (int32_t)r0);
    write_register(core, "r1", (int32_t)r1);
    write_register(core, "r2", (int32_t)r2);
    write_register(core, "r3", (int32_t)r3);
    write_register(core, "pc", (int32_t)function);
    uint64_t steps = 0;
    while ((((uint32_t)read_register(core, "pc")) & ~1U)
           != UINT32_C(0x08000002)) {
        if (++steps > BP_MAX_CALL_STEPS) {
            fprintf(stderr,
                    "mgba-bp-shop-smoke: instruction limit "
                    "function=%#010" PRIx32 " pc=%#010" PRIx32 "\n",
                    function, (uint32_t)read_register(core, "pc"));
            bp_die("runtime instruction limit exceeded");
        }
        core->step(core);
    }
    uint32_t result = (uint32_t)read_register(core, "r0");
    restore_cpu(core, &original);
    return result;
}

static uint32_t bp_invoke_result(struct mCore *core, uint32_t entrypoint,
                                 uint32_t argument)
{
    bp_write16(core, SPECIAL_VAR_RESULT, UINT16_C(0xFFFF));
    uint32_t direct = bp_call_thumb(core, entrypoint, argument, 0, 0, 0);
    uint32_t script = read16(core, SPECIAL_VAR_RESULT);
    if ((direct & UINT32_C(0xFFFF)) != script) {
        fprintf(stderr,
                "mgba-bp-shop-smoke: direct/script result differs "
                "entry=%#010" PRIx32 " direct=%" PRIu32
                " script=%" PRIu32 "\n",
                entrypoint, direct, script);
        exit(1);
    }
    return script;
}

static void bp_finalize(struct mCore *core, uint32_t finalize)
{
    (void)bp_call_thumb(core, finalize, BP_LEDGER, 0, 0, 0);
}

static void bp_set_flag(struct mCore *core, uint16_t flag, bool enabled)
{
    (void)bp_call_thumb(core, enabled ? BP_FLAG_SET : BP_FLAG_CLEAR,
                        flag, 0, 0, 0);
}

static bool bp_has_item(struct mCore *core, uint16_t item, uint16_t quantity)
{
    return bp_call_thumb(core, BP_CHECK_BAG, item, quantity, 0, 0) != 0U;
}

static void bp_empty_item(struct mCore *core, uint16_t item)
{
    uint32_t removed = 0;
    while (bp_has_item(core, item, 1U)) {
        if (bp_call_thumb(core, BP_REMOVE_BAG, item, 1U, 0, 0) == 0U)
            bp_die("bag item could not be removed");
        if (++removed > 2000U)
            bp_die("bag cleanup exceeded item capacity");
    }
}

static uint32_t bp_fill_item(struct mCore *core, uint16_t item)
{
    uint32_t count = 0;

    /* Fill to the exact engine limit with O(log capacity) native calls. */
    for (uint32_t chunk = 1024U; chunk != 0U; chunk >>= 1U) {
        while (bp_call_thumb(core, BP_ADD_BAG, item, chunk, 0, 0) != 0U) {
            count += chunk;
            if (count > 4096U)
                bp_die("bag fill exceeded item capacity");
        }
    }
    if (count == 0U || !bp_has_item(core, item, 1U)
        || bp_call_thumb(core, BP_ADD_BAG, item, 1U, 0, 0) != 0U)
        bp_die("bag fill did not create a full stack");
    return count;
}

static void bp_remove_count(struct mCore *core, uint16_t item, uint32_t count)
{
    if (count == 0U || count > UINT16_MAX
        || bp_call_thumb(core, BP_REMOVE_BAG, item, count, 0, 0) == 0U
        || bp_has_item(core, item, 1U))
        bp_die("bag full fixture cleanup failed");
}

static void bp_require_flash_ledger(struct mCore *core, const char *label)
{
    for (uint32_t index = 0; index < BP_LEDGER_SIZE; ++index) {
        uint8_t ewram = read8(core, BP_LEDGER + index);
        uint8_t flash = read8(core, BP_FLASH_LEDGER + index);
        if (ewram != flash) {
            fprintf(stderr,
                    "mgba-bp-shop-smoke: ledger mismatch %s offset=%#06" PRIx32
                    " ewram=%#04x flash=%#04x\n",
                    label, index, ewram, flash);
            bp_die("EWRAM ledger differs from sector 31 payload");
        }
    }
}

static void bp_verify_map(struct mCore *core, uint32_t npc_script,
                          uint32_t expected_events,
                          uint32_t expected_map_scripts)
{
    uint32_t map_root = read32(core, ROM_BASE + UINT32_C(0x54B0C));
    uint32_t group96 = read32(core, map_root + 96U * 4U);
    uint32_t header = read32(core, group96 + 5U * 4U);
    uint32_t events = read32(core, header + 4U);
    uint32_t scripts = read32(core, header + 8U);
    uint32_t objects = read32(core, events + 4U);
    uint32_t first = objects;
    uint32_t trial = objects + 0x18U;
    uint32_t shop = objects + 0x30U;
    if (!rom_pointer(map_root) || !rom_pointer(group96) || !rom_pointer(header)
        || events != expected_events || scripts != expected_map_scripts
        || !rom_pointer(objects)
        || read8(core, events) != 3U || read8(core, events + 1U) != 10U
        || read8(core, events + 2U) != 0U || read8(core, events + 3U) != 0U
        || read8(core, first) != 1U
        || read16(core, first + 4U) != 24U
        || read16(core, first + 6U) != 33U
        || read8(core, trial) != 2U
        || read16(core, trial + 4U) != 20U
        || read16(core, trial + 6U) != 19U
        || read8(core, shop) != 3U
        || read16(core, shop + 4U) != 22U
        || read16(core, shop + 6U) != 19U
        || read32(core, shop + 0x10U) != npc_script
        || read8(core, npc_script) != 0x6AU
        || read8(core, npc_script + 1U) != 0x5AU
        || read8(core, npc_script + 2U) != 0x23U)
        bp_die("physical Factory BP shop graph is invalid");
    for (uint32_t offset = 1U; offset < 0x18U; ++offset) {
        if (offset == 4U || offset == 5U || offset == 6U || offset == 7U
            || (offset >= 0x10U && offset <= 0x13U))
            continue;
        if (read8(core, trial + offset) != read8(core, shop + offset))
            bp_die("shop NPC is not an exact Trial-NPC clone outside bindings");
    }
    uint32_t open_entry = bp_read_u32_unaligned(core, npc_script + 3U);
    if ((open_entry & 1U) == 0U || !rom_pointer(open_entry & ~1U))
        bp_die("shop NPC callnative target is invalid");
}

static void bp_expect_unlock(struct mCore *core, uint32_t unlock,
                             uint16_t index, uint16_t expected,
                             const char *label)
{
    uint32_t actual = bp_invoke_result(core, unlock, index);
    if (actual != expected) {
        fprintf(stderr,
                "mgba-bp-shop-smoke: unlock %s index=%u expected=%u got=%" PRIu32 "\n",
                label, index, expected, actual);
        exit(1);
    }
}

static void bp_reset_unlock_state(struct mCore *core, uint32_t finalize)
{
    bp_set_flag(core, BP_FLAG_DH_CLEAR, false);
    for (uint16_t flag = BP_FLAG_BADGE_1; flag <= BP_FLAG_BADGE_1 + 7U; ++flag)
        bp_set_flag(core, flag, false);
    bp_set_flag(core, UINT16_C(0x082C), false);
    bp_write8(core, BP_LEDGER + BP_KANTO_TRAVEL_OFFSET, 0U);
    bp_write8(core, BP_LEDGER + BP_KANTO_VISITED_OFFSET, 0U);
    bp_write8(core, BP_LEDGER + BP_HALL_OF_FAME_OFFSET, 0U);
    bp_write8(core, BP_LEDGER + BP_LEAGUE_I_OFFSET, 0U);
    bp_write8(core, BP_LEDGER + BP_LEAGUE_II_OFFSET, 0U);
    bp_write8(core, BP_LEDGER + BP_CERTIFICATIONS_OFFSET, 0U);
    bp_finalize(core, finalize);
}

int main(int argc, char **argv)
{
    if (argc != 12) {
        fprintf(stderr,
                "usage: %s ROM SAVE PROBE ENSURE BALANCE UNLOCK PURCHASE "
                "FINALIZE NPC_SCRIPT EVENTS MAP_SCRIPTS\n", argv[0]);
        return 2;
    }
    uint32_t probe = parse_u32(argv[3], "probe");
    uint32_t ensure = parse_u32(argv[4], "ensure");
    uint32_t balance = parse_u32(argv[5], "balance");
    uint32_t unlock = parse_u32(argv[6], "unlock");
    uint32_t purchase = parse_u32(argv[7], "purchase");
    uint32_t finalize = parse_u32(argv[8], "finalize");
    uint32_t npc_script = parse_u32(argv[9], "NPC script");
    uint32_t events = parse_u32(argv[10], "events");
    uint32_t map_scripts = parse_u32(argv[11], "map scripts");
    const uint32_t entrypoints[] = {
        probe, ensure, balance, unlock, purchase, finalize,
    };
    for (size_t index = 0;
         index < sizeof(entrypoints) / sizeof(entrypoints[0]); ++index) {
        if ((entrypoints[index] & 1U) == 0U
            || !rom_pointer(entrypoints[index] & ~1U))
            bp_die("runtime entrypoint contract failed");
    }
    if (!rom_pointer(npc_script) || !rom_pointer(events)
        || !rom_pointer(map_scripts))
        bp_die("map/script address contract failed");

    struct mLogger logger = {.log = silent_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mCore *core = mCoreFind(argv[1]);
    if (core == NULL || !core->init(core))
        bp_die("core initialization failed");
    if (!mCoreLoadFile(core, argv[1]))
        bp_die("ROM load failed");
    bp_initialize_save(argv[2]);
    if (!mCoreLoadSaveFile(core, argv[2], false))
        bp_die("temporary save attachment failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    color_t *video = calloc(GBA_WIDTH * GBA_HEIGHT, sizeof(*video));
    if (video == NULL)
        bp_die("video allocation failed");
    core->setVideoBuffer(core, video, GBA_WIDTH);
    core->reset(core);
    bp_phase("natural-new-game");
    uint32_t transitions = run_natural_new_game(core, video);
    bp_phase("map-and-probe");

    bp_verify_map(core, npc_script, events, map_scripts);
    bp_write16(core, SPECIAL_VAR_RESULT, 0U);
    if (bp_call_thumb(core, probe, 0, 0, 0, 0) != BP_ABI_MARKER
        || read16(core, SPECIAL_VAR_RESULT) != BP_ABI_MARKER)
        bp_die("BP shop ABI probe failed");
    if (bp_invoke_result(core, ensure, 0U) != 1U)
        bp_die("BP shop save initialization failed");

    bp_phase("unlock-mapping");
    /* Exercise every distinct unlock-kind mapping used by the 18-row catalog. */
    bp_reset_unlock_state(core, finalize);
    const uint16_t representative[] = {0, 2, 3, 4, 5, 8, 9, 10, 11, 12, 17};
    for (size_t index = 0;
         index < sizeof(representative) / sizeof(representative[0]); ++index)
        bp_expect_unlock(core, unlock, representative[index], 0U, "initial");
    bp_set_flag(core, BP_FLAG_DH_CLEAR, true);
    bp_expect_unlock(core, unlock, 0U, 1U, "DH clear");
    bp_write8(core, BP_LEDGER + BP_KANTO_TRAVEL_OFFSET, 1U);
    bp_finalize(core, finalize);
    bp_expect_unlock(core, unlock, 2U, 1U, "Kanto early");
    bp_set_flag(core, BP_FLAG_BADGE_1, true);
    bp_expect_unlock(core, unlock, 3U, 1U, "badge 1");
    bp_write8(core, BP_LEDGER + BP_KANTO_VISITED_OFFSET, 1U);
    bp_finalize(core, finalize);
    bp_expect_unlock(core, unlock, 4U, 1U, "daycare visit");
    bp_set_flag(core, BP_FLAG_BADGE_1 + 4U, true);
    bp_expect_unlock(core, unlock, 5U, 1U, "badge 5");
    bp_set_flag(core, BP_FLAG_BADGE_1 + 5U, true);
    bp_expect_unlock(core, unlock, 8U, 1U, "badge 6");
    bp_write8(core, BP_LEDGER + BP_HALL_OF_FAME_OFFSET, 1U);
    bp_write8(core, BP_LEDGER + BP_CERTIFICATIONS_OFFSET, UINT8_C(0x0F));
    bp_finalize(core, finalize);
    bp_expect_unlock(core, unlock, 9U, 1U, "competitive supply");
    bp_set_flag(core, BP_FLAG_BADGE_1 + 6U, true);
    bp_expect_unlock(core, unlock, 10U, 1U, "badge 7");
    bp_set_flag(core, BP_FLAG_BADGE_1 + 7U, true);
    bp_expect_unlock(core, unlock, 11U, 1U, "badge 8");
    bp_write8(core, BP_LEDGER + BP_LEAGUE_I_OFFSET, 1U);
    bp_write8(core, BP_LEDGER + BP_LEAGUE_II_OFFSET, 1U);
    bp_finalize(core, finalize);
    bp_expect_unlock(core, unlock, 12U, 1U, "Kanto league");
    bp_expect_unlock(core, unlock, 17U, 1U, "UB/Paradox");

    bp_phase("successful-purchase");
    /* Success: item is durable in the normal save; BP is durable in sector 31. */
    bp_empty_item(core, BP_ITEM_EXP_XS);
    bp_write16(core, BP_LEDGER + BP_FACTORY_OFFSET + BP_BALANCE_OFFSET, 100U);
    bp_finalize(core, finalize);
    if (bp_invoke_result(core, purchase, 0U) != BP_RESULT_SUCCESS
        || read16(core, BP_LEDGER + BP_FACTORY_OFFSET + BP_BALANCE_OFFSET) != 99U
        || !bp_has_item(core, BP_ITEM_EXP_XS, 1U))
        bp_die("successful purchase did not add item and debit BP");
    bp_require_flash_ledger(core, "after purchase");
    bp_clear_region(core, BP_LEDGER, BP_LEDGER_SIZE);
    if (bp_call_thumb(core, BP_SAVE_LOAD, 0, 0, 0, 0) != 1U
        || !bp_has_item(core, BP_ITEM_EXP_XS, 1U))
        bp_die("normal-save item round trip failed");
    if (bp_invoke_result(core, ensure, 0U) != 1U
        || bp_invoke_result(core, balance, 0U) != 99U)
        bp_die("sector31 BP reload failed");

    bp_phase("insufficient-bp");
    /* Insufficient balance rejects before bag/save mutation. */
    bp_empty_item(core, BP_ITEM_EXP_S);
    bp_write16(core, BP_LEDGER + BP_FACTORY_OFFSET + BP_BALANCE_OFFSET, 1U);
    bp_finalize(core, finalize);
    uint64_t insufficient_flash = bp_hash_region(core, BP_FLASH_LEDGER,
                                                  BP_LEDGER_SIZE);
    if (bp_invoke_result(core, purchase, 1U) != BP_RESULT_INSUFFICIENT
        || read16(core, BP_LEDGER + BP_FACTORY_OFFSET + BP_BALANCE_OFFSET) != 1U
        || bp_has_item(core, BP_ITEM_EXP_S, 1U)
        || bp_hash_region(core, BP_FLASH_LEDGER, BP_LEDGER_SIZE)
               != insufficient_flash)
        bp_die("insufficient-BP rejection mutated state");

    bp_phase("bag-full-fill");
    /* A full item stack rejects before BP/save mutation. */
    bp_write16(core, BP_LEDGER + BP_FACTORY_OFFSET + BP_BALANCE_OFFSET, 100U);
    bp_finalize(core, finalize);
    uint32_t full_count = bp_fill_item(core, BP_ITEM_EXP_S);
    bp_phase("bag-full-purchase");
    uint64_t full_flash = bp_hash_region(core, BP_FLASH_LEDGER, BP_LEDGER_SIZE);
    if (bp_invoke_result(core, purchase, 1U) != BP_RESULT_BAG_FULL
        || read16(core, BP_LEDGER + BP_FACTORY_OFFSET + BP_BALANCE_OFFSET) != 100U
        || bp_hash_region(core, BP_FLASH_LEDGER, BP_LEDGER_SIZE) != full_flash)
        bp_die("bag-full rejection mutated BP or flash");
    bp_remove_count(core, BP_ITEM_EXP_S, full_count);

    bp_phase("locked-item");
    /* A late catalog row remains unavailable without the league signal. */
    bp_empty_item(core, BP_ITEM_GOLD_CAP);
    bp_write8(core, BP_LEDGER + BP_LEAGUE_I_OFFSET, 0U);
    bp_write8(core, BP_LEDGER + BP_LEAGUE_II_OFFSET, 0U);
    bp_write16(core, BP_LEDGER + BP_FACTORY_OFFSET + BP_BALANCE_OFFSET, 1000U);
    bp_finalize(core, finalize);
    uint64_t locked_flash = bp_hash_region(core, BP_FLASH_LEDGER, BP_LEDGER_SIZE);
    if (bp_invoke_result(core, purchase, 12U) != BP_RESULT_LOCKED
        || read16(core, BP_LEDGER + BP_FACTORY_OFFSET + BP_BALANCE_OFFSET) != 1000U
        || bp_has_item(core, BP_ITEM_GOLD_CAP, 1U)
        || bp_hash_region(core, BP_FLASH_LEDGER, BP_LEDGER_SIZE) != locked_flash)
        bp_die("locked rejection mutated state");

    bp_phase("complete");
    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"checks\":{\"physical_npc_event_graph\":true,"
           "\"probe_and_save_init\":true,\"unlock_mapping\":true,"
           "\"successful_purchase\":true,\"sector31_reload\":true,"
           "\"insufficient_no_mutation\":true,"
           "\"bag_full_no_mutation\":true,"
           "\"locked_no_mutation\":true},"
           "\"catalog_representative_unlocks\":11,"
           "\"success_item_id\":988,\"success_price_bp\":1,"
           "\"success_balance_after\":99,"
           "\"bag_full_capacity\":%" PRIu32 ","
           "\"framebuffer_transitions\":%" PRIu32 ","
           "\"artifacts_written\":[]}\n",
           full_count, transitions);

    fflush(stdout);
    bp_phase("free-video");
    free(video);
    bp_phase("config-deinit");
    mCoreConfigDeinit(&core->config);
    bp_phase("core-deinit");
    core->deinit(core);
    bp_phase("process-exit");
    fflush(stderr);
    _Exit(EXIT_SUCCESS);
}
