/* Focused stage29 exact-ROM smoke for Factory Trial repeat rewards. */
#define main mgba_regression_smoke_embedded_main
#include "mgba_regression_smoke.c"
#undef main

#include <string.h>

#define REWARD_MAX_CALL_STEPS UINT64_C(60000000)
#define REWARD_SAVE_FILE_SIZE UINT32_C(0x20000)
#define REWARD_ABI_MARKER UINT32_C(0xB929)
#define REWARD_LEDGER UINT32_C(0x0203D000)
#define REWARD_LEDGER_SIZE UINT32_C(0x800)
#define REWARD_FACTORY_OFFSET UINT32_C(0x392)
#define REWARD_BP_OFFSET UINT32_C(0)
#define REWARD_CURRENT_STREAK_OFFSET UINT32_C(2)
#define REWARD_BEST_STREAK_OFFSET UINT32_C(50)
#define REWARD_CLAIM_BITS_OFFSET UINT32_C(98)
#define REWARD_TRANSACTION_OFFSET UINT32_C(106)
#define REWARD_MARKER_OFFSET UINT32_C(110)
#define REWARD_SNAPSHOT_VALID_OFFSET UINT32_C(111)
#define REWARD_PARTY_COUNT_SNAPSHOT_OFFSET UINT32_C(112)
#define REWARD_PENDING_OFFSET UINT32_C(113)
#define REWARD_PARTY_SNAPSHOT_OFFSET UINT32_C(114)
#define REWARD_CREDITS_OFFSET UINT32_C(0x684)
#define REWARD_FLASH_LEDGER UINT32_C(0x0E01F064)
#define REWARD_PLAYER_PARTY UINT32_C(0x020241E4)
#define REWARD_PLAYER_PARTY_COUNT UINT32_C(0x02023F89)
#define REWARD_MON_SIZE UINT32_C(100)
#define REWARD_PARTY_CAPACITY UINT32_C(6)
#define REWARD_CHECK_BAG UINT32_C(0x08099949)
#define REWARD_ADD_BAG UINT32_C(0x08099A8D)
#define REWARD_REMOVE_BAG UINT32_C(0x08099BE1)
#define REWARD_SAVE_LOAD UINT32_C(0x080DB4E5)
#define REWARD_ITEM_XS UINT32_C(988)
#define REWARD_ITEM_S UINT32_C(989)
#define REWARD_ITEM_ORAN UINT32_C(432)
#define REWARD_ITEM_ULTRA UINT32_C(2)
#define REWARD_RNG_STATE UINT32_C(0x03005040)
#define REWARD_RESULT UINT32_C(9)
#define REWARD_MARKER_BATTLE_ACTIVE UINT32_C(2)

static void reward_die(const char *message)
{
    fprintf(stderr, "mgba-factory-reward-smoke: %s\n", message);
    exit(1);
}

static void reward_phase(const char *phase)
{
    fprintf(stderr, "mgba-factory-reward-smoke: phase=%s\n", phase);
    fflush(stderr);
}

static void reward_initialize_save(const char *path)
{
    FILE *stream = fopen(path, "wb");
    if (stream == NULL)
        reward_die("temporary save creation failed");
    uint8_t block[4096];
    memset(block, 0xFF, sizeof(block));
    uint32_t remaining = REWARD_SAVE_FILE_SIZE;
    while (remaining != 0U) {
        size_t amount = remaining < sizeof(block) ? remaining : sizeof(block);
        if (fwrite(block, 1U, amount, stream) != amount) {
            (void)fclose(stream);
            reward_die("temporary save initialization failed");
        }
        remaining -= (uint32_t)amount;
    }
    if (fclose(stream) != 0)
        reward_die("temporary save close failed");
}

static void reward_write8(struct mCore *core, uint32_t address, uint8_t value)
{
    core->rawWrite8(core, address, -1, value);
}

static void reward_write16(struct mCore *core, uint32_t address, uint16_t value)
{
    core->rawWrite16(core, address, -1, value);
}

static void reward_write32(struct mCore *core, uint32_t address, uint32_t value)
{
    reward_write8(core, address, (uint8_t)value);
    reward_write8(core, address + 1U, (uint8_t)(value >> 8U));
    reward_write8(core, address + 2U, (uint8_t)(value >> 16U));
    reward_write8(core, address + 3U, (uint8_t)(value >> 24U));
}

static uint32_t reward_read32_unaligned(struct mCore *core, uint32_t address)
{
    return (uint32_t)read8(core, address)
        | ((uint32_t)read8(core, address + 1U) << 8U)
        | ((uint32_t)read8(core, address + 2U) << 16U)
        | ((uint32_t)read8(core, address + 3U) << 24U);
}

static void reward_read_bytes(struct mCore *core, uint32_t address,
                              uint8_t *destination, size_t size)
{
    for (size_t index = 0; index < size; ++index)
        destination[index] = read8(core, address + (uint32_t)index);
}

static void reward_write_bytes(struct mCore *core, uint32_t address,
                               const uint8_t *source, size_t size)
{
    for (size_t index = 0; index < size; ++index)
        reward_write8(core, address + (uint32_t)index, source[index]);
}

static void reward_clear_region(struct mCore *core, uint32_t address,
                                size_t size)
{
    for (size_t index = 0; index < size; ++index)
        reward_write8(core, address + (uint32_t)index, 0U);
}

static bool reward_memory_equals(struct mCore *core, uint32_t address,
                                 const uint8_t *expected, size_t size)
{
    for (size_t index = 0; index < size; ++index) {
        if (read8(core, address + (uint32_t)index) != expected[index])
            return false;
    }
    return true;
}

static uint32_t reward_call_thumb(struct mCore *core, uint32_t function,
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
        if (++steps > REWARD_MAX_CALL_STEPS) {
            fprintf(stderr,
                    "mgba-factory-reward-smoke: instruction limit "
                    "function=%#010" PRIx32 " pc=%#010" PRIx32 "\n",
                    function, (uint32_t)read_register(core, "pc"));
            reward_die("runtime instruction limit exceeded");
        }
        core->step(core);
    }
    uint32_t result = (uint32_t)read_register(core, "r0");
    restore_cpu(core, &original);
    return result;
}

static uint16_t reward_invoke(struct mCore *core, uint32_t entrypoint)
{
    reward_write16(core, SPECIAL_VAR_RESULT, UINT16_C(0xFFFF));
    uint32_t direct = reward_call_thumb(core, entrypoint, 0U, 0U, 0U, 0U);
    uint16_t script = read16(core, SPECIAL_VAR_RESULT);
    if ((direct & UINT32_C(0xFFFF)) != script) {
        fprintf(stderr,
                "mgba-factory-reward-smoke: direct/script result differs "
                "entry=%#010" PRIx32 " direct=%" PRIu32 " script=%u\n",
                entrypoint, direct, script);
        exit(1);
    }
    return script;
}

static void reward_finalize(struct mCore *core, uint32_t finalize)
{
    (void)reward_call_thumb(core, finalize, REWARD_LEDGER, 0U, 0U, 0U);
}

static bool reward_has_item(struct mCore *core, uint16_t item,
                            uint16_t quantity)
{
    return reward_call_thumb(core, REWARD_CHECK_BAG,
                             item, quantity, 0U, 0U) != 0U;
}

static uint32_t reward_item_count(struct mCore *core, uint16_t item)
{
    uint32_t low = 0U;
    uint32_t high = 4097U;
    while (low + 1U < high) {
        uint32_t middle = low + (high - low) / 2U;
        if (reward_has_item(core, item, (uint16_t)middle))
            low = middle;
        else
            high = middle;
    }
    return low;
}

static void reward_empty_item(struct mCore *core, uint16_t item)
{
    uint32_t count = reward_item_count(core, item);
    if (count != 0U
        && reward_call_thumb(core, REWARD_REMOVE_BAG,
                             item, count, 0U, 0U) == 0U)
        reward_die("bag item cleanup failed");
    if (reward_has_item(core, item, 1U))
        reward_die("bag item cleanup left a residual item");
}

static uint32_t reward_fill_item(struct mCore *core, uint16_t item)
{
    uint32_t count = 0U;
    for (uint32_t chunk = 1024U; chunk != 0U; chunk >>= 1U) {
        while (reward_call_thumb(core, REWARD_ADD_BAG,
                                 item, chunk, 0U, 0U) != 0U) {
            count += chunk;
            if (count > 4096U)
                reward_die("bag fill exceeded expected capacity");
        }
    }
    if (count == 0U || reward_item_count(core, item) != count
        || reward_call_thumb(core, REWARD_ADD_BAG,
                             item, 1U, 0U, 0U) != 0U)
        reward_die("bag full fixture is invalid");
    return count;
}

static void reward_require_flash_ledger(struct mCore *core,
                                        const char *label)
{
    for (uint32_t index = 0U; index < REWARD_LEDGER_SIZE; ++index) {
        uint8_t ewram = read8(core, REWARD_LEDGER + index);
        uint8_t flash = read8(core, REWARD_FLASH_LEDGER + index);
        if (ewram != flash) {
            fprintf(stderr,
                    "mgba-factory-reward-smoke: ledger mismatch %s "
                    "offset=%#06" PRIx32 " ewram=%#04x flash=%#04x\n",
                    label, index, ewram, flash);
            reward_die("EWRAM ledger differs from sector 31");
        }
    }
}

static void reward_require_party(struct mCore *core,
                                 const uint8_t original[REWARD_PARTY_CAPACITY
                                                        * REWARD_MON_SIZE],
                                 uint8_t original_count,
                                 const char *label)
{
    uint32_t factory = REWARD_LEDGER + REWARD_FACTORY_OFFSET;
    if (!reward_memory_equals(core, REWARD_PLAYER_PARTY, original,
                              REWARD_PARTY_CAPACITY * REWARD_MON_SIZE)
        || read8(core, REWARD_PLAYER_PARTY_COUNT) != original_count
        || read8(core, factory + REWARD_MARKER_OFFSET) != 0U
        || read8(core, factory + REWARD_SNAPSHOT_VALID_OFFSET) != 0U
        || read8(core, factory + REWARD_PARTY_COUNT_SNAPSHOT_OFFSET) != 0U
        || read8(core, factory + REWARD_PENDING_OFFSET) != 0U) {
        fprintf(stderr,
                "mgba-factory-reward-smoke: party restore failed at %s\n",
                label);
        exit(1);
    }
}

static void reward_prepare_completion(
    struct mCore *core, uint32_t finalize,
    const uint8_t original[REWARD_PARTY_CAPACITY * REWARD_MON_SIZE],
    uint8_t original_count, uint16_t bp, uint16_t streak,
    uint32_t claims, const uint16_t credits[4])
{
    uint32_t factory = REWARD_LEDGER + REWARD_FACTORY_OFFSET;
    uint8_t rental[REWARD_PARTY_CAPACITY * REWARD_MON_SIZE];
    for (size_t index = 0U; index < sizeof(rental); ++index)
        rental[index] = (uint8_t)(UINT32_C(0xA5) ^ (uint32_t)index);

    reward_write16(core, factory + REWARD_BP_OFFSET, bp);
    reward_write16(core, factory + REWARD_CURRENT_STREAK_OFFSET, streak);
    reward_write16(core, factory + REWARD_BEST_STREAK_OFFSET, streak);
    reward_write32(core, factory + REWARD_CLAIM_BITS_OFFSET, claims);
    for (uint32_t index = 0U; index < 4U; ++index)
        reward_write16(core, REWARD_LEDGER + REWARD_CREDITS_OFFSET + index * 2U,
                       credits[index]);
    reward_write_bytes(core, factory + REWARD_PARTY_SNAPSHOT_OFFSET,
                       original, REWARD_PARTY_CAPACITY * REWARD_MON_SIZE);
    reward_write8(core, factory + REWARD_MARKER_OFFSET,
                  REWARD_MARKER_BATTLE_ACTIVE);
    reward_write8(core, factory + REWARD_SNAPSHOT_VALID_OFFSET, 1U);
    reward_write8(core, factory + REWARD_PARTY_COUNT_SNAPSHOT_OFFSET,
                  original_count);
    reward_write8(core, factory + REWARD_PENDING_OFFSET, 3U);
    reward_write_bytes(core, REWARD_PLAYER_PARTY, rental, sizeof(rental));
    reward_write8(core, REWARD_PLAYER_PARTY_COUNT, 3U);
    reward_finalize(core, finalize);
}

static void reward_expect_credits(struct mCore *core,
                                  uint16_t c0, uint16_t c1,
                                  uint16_t c2, uint16_t c3,
                                  const char *label)
{
    const uint16_t expected[4] = {c0, c1, c2, c3};
    for (uint32_t index = 0U; index < 4U; ++index) {
        uint16_t actual = read16(core,
            REWARD_LEDGER + REWARD_CREDITS_OFFSET + index * 2U);
        if (actual != expected[index]) {
            fprintf(stderr,
                    "mgba-factory-reward-smoke: credit mismatch %s "
                    "index=%" PRIu32 " expected=%u actual=%u\n",
                    label, index, expected[index], actual);
            exit(1);
        }
    }
}


int main(int argc, char **argv)
{
    if (argc != 9) {
        fprintf(stderr,
                "usage: %s ROM SAVE PROBE COMPLETE FINALIZE ENSURE "
                "COMPLETE_SCRIPT STAGE28_COMPLETE\n", argv[0]);
        return 2;
    }
    uint32_t probe = parse_u32(argv[3], "probe");
    uint32_t complete = parse_u32(argv[4], "complete");
    uint32_t finalize = parse_u32(argv[5], "finalize");
    uint32_t ensure = parse_u32(argv[6], "ensure");
    uint32_t complete_script = parse_u32(argv[7], "completion script");
    uint32_t stage28_complete = parse_u32(argv[8], "Stage28 completion");
    const uint32_t entrypoints[] = {
        probe, complete, finalize, ensure, stage28_complete,
    };
    for (size_t index = 0U;
         index < sizeof(entrypoints) / sizeof(entrypoints[0]); ++index) {
        if ((entrypoints[index] & 1U) == 0U
            || !rom_pointer(entrypoints[index] & ~1U))
            reward_die("runtime entrypoint contract failed");
    }
    if (!rom_pointer(complete_script) || complete == stage28_complete)
        reward_die("completion script/wrapper contract failed");

    struct mLogger logger = {.log = silent_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mCore *core = mCoreFind(argv[1]);
    if (core == NULL || !core->init(core))
        reward_die("core initialization failed");
    if (!mCoreLoadFile(core, argv[1]))
        reward_die("ROM load failed");
    reward_initialize_save(argv[2]);
    if (!mCoreLoadSaveFile(core, argv[2], false))
        reward_die("temporary save attachment failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    color_t *video = calloc(GBA_WIDTH * GBA_HEIGHT, sizeof(*video));
    if (video == NULL)
        reward_die("video allocation failed");
    core->setVideoBuffer(core, video, GBA_WIDTH);
    core->reset(core);

    reward_phase("natural-new-game");
    uint32_t transitions = run_natural_new_game(core, video);
    reward_phase("binding-probe-init");
    if (read8(core, complete_script) != 0x23U
        || reward_read32_unaligned(core, complete_script + 1U) != complete)
        reward_die("completion callnative Stage29 wrapper is not physically bound");
    reward_write16(core, SPECIAL_VAR_RESULT, 0U);
    if (reward_call_thumb(core, probe, 0U, 0U, 0U, 0U)
            != REWARD_ABI_MARKER
        || read16(core, SPECIAL_VAR_RESULT) != REWARD_ABI_MARKER)
        reward_die("Factory repeat reward ABI probe failed");
    if (reward_invoke(core, ensure) != 1U)
        reward_die("Stage27 save initialization failed");

    uint8_t original[REWARD_PARTY_CAPACITY * REWARD_MON_SIZE];
    reward_read_bytes(core, REWARD_PLAYER_PARTY, original, sizeof(original));
    uint8_t original_count = read8(core, REWARD_PLAYER_PARTY_COUNT);
    if (original_count > REWARD_PARTY_CAPACITY)
        reward_die("natural party count is invalid");
    reward_empty_item(core, REWARD_ITEM_XS);
    reward_empty_item(core, REWARD_ITEM_S);
    reward_empty_item(core, REWARD_ITEM_ORAN);
    reward_empty_item(core, REWARD_ITEM_ULTRA);

    uint32_t factory = REWARD_LEDGER + REWARD_FACTORY_OFFSET;
    const uint16_t zero_credits[4] = {0U, 0U, 0U, 0U};
    const uint16_t first_credits[4] = {1U, 0U, 0U, 0U};

    reward_phase("first-clear-no-repeat");
    reward_write32(core, REWARD_RNG_STATE, 3U);
    reward_prepare_completion(core, finalize, original, original_count,
                              100U, 3U, 0U, zero_credits);
    if (reward_invoke(core, complete) != REWARD_RESULT
        || read16(core, factory + REWARD_BP_OFFSET) != 112U
        || read32(core, factory + REWARD_CLAIM_BITS_OFFSET) != 0x1FU
        || reward_item_count(core, REWARD_ITEM_XS) != 5U
        || reward_item_count(core, REWARD_ITEM_S) != 2U
        || reward_item_count(core, REWARD_ITEM_ORAN) != 0U
        || reward_item_count(core, REWARD_ITEM_ULTRA) != 0U)
        reward_die("first clear incorrectly mixed in a repeat reward");
    reward_expect_credits(core, 1U, 0U, 0U, 0U, "first clear");
    reward_require_party(core, original, original_count, "first clear");
    reward_require_flash_ledger(core, "first clear");

    reward_phase("repeat-oran");
    reward_write32(core, REWARD_RNG_STATE, 0U);
    reward_prepare_completion(core, finalize, original, original_count,
                              112U, 3U, 0x1FU, first_credits);
    if (reward_invoke(core, complete) != REWARD_RESULT
        || read16(core, factory + REWARD_BP_OFFSET) != 122U
        || read32(core, factory + REWARD_CLAIM_BITS_OFFSET) != 0x1FU
        || reward_item_count(core, REWARD_ITEM_ORAN) != 1U
        || reward_item_count(core, REWARD_ITEM_ULTRA) != 0U
        || reward_item_count(core, REWARD_ITEM_XS) != 5U
        || reward_item_count(core, REWARD_ITEM_S) != 2U)
        reward_die("repeat Oran/+1 BP branch differs");
    reward_expect_credits(core, 1U, 0U, 0U, 0U, "repeat Oran");
    reward_require_party(core, original, original_count, "repeat Oran");
    reward_require_flash_ledger(core, "repeat Oran");

    reward_phase("repeat-ultra");
    reward_write32(core, REWARD_RNG_STATE, 3U);
    reward_prepare_completion(core, finalize, original, original_count,
                              122U, 3U, 0x1FU, first_credits);
    if (reward_invoke(core, complete) != REWARD_RESULT
        || read16(core, factory + REWARD_BP_OFFSET) != 133U
        || read32(core, factory + REWARD_CLAIM_BITS_OFFSET) != 0x1FU
        || reward_item_count(core, REWARD_ITEM_ORAN) != 1U
        || reward_item_count(core, REWARD_ITEM_ULTRA) != 1U
        || reward_item_count(core, REWARD_ITEM_XS) != 5U
        || reward_item_count(core, REWARD_ITEM_S) != 2U)
        reward_die("repeat Ultra Ball/+2 BP branch differs");
    reward_expect_credits(core, 1U, 0U, 0U, 0U, "repeat Ultra");
    reward_require_party(core, original, original_count, "repeat Ultra");
    reward_require_flash_ledger(core, "repeat Ultra");

    reward_phase("normal-save-reload");
    if (reward_call_thumb(core, REWARD_REMOVE_BAG,
                          REWARD_ITEM_XS, 5U, 0U, 0U) == 0U
        || reward_call_thumb(core, REWARD_REMOVE_BAG,
                             REWARD_ITEM_S, 2U, 0U, 0U) == 0U
        || reward_call_thumb(core, REWARD_REMOVE_BAG,
                             REWARD_ITEM_ORAN, 1U, 0U, 0U) == 0U
        || reward_call_thumb(core, REWARD_REMOVE_BAG,
                             REWARD_ITEM_ULTRA, 1U, 0U, 0U) == 0U)
        reward_die("normal-save reload fixture could not remove rewards");
    reward_clear_region(core, REWARD_LEDGER, REWARD_LEDGER_SIZE);
    if (reward_call_thumb(core, REWARD_SAVE_LOAD, 0U, 0U, 0U, 0U) != 1U
        || reward_item_count(core, REWARD_ITEM_XS) != 5U
        || reward_item_count(core, REWARD_ITEM_S) != 2U
        || reward_item_count(core, REWARD_ITEM_ORAN) != 1U
        || reward_item_count(core, REWARD_ITEM_ULTRA) != 1U)
        reward_die("normal save did not reload repeat rewards");
    if (reward_invoke(core, ensure) != 1U
        || read16(core, factory + REWARD_BP_OFFSET) != 133U
        || read32(core, factory + REWARD_CLAIM_BITS_OFFSET) != 0x1FU)
        reward_die("sector31 did not reload repeat reward ledger");
    reward_require_flash_ledger(core, "repeat reload");
    reward_require_party(core, original, original_count, "repeat reload");

    reward_phase("streak-credit-coexistence");
    reward_write32(core, REWARD_RNG_STATE, 0U);
    reward_prepare_completion(core, finalize, original, original_count,
                              133U, 21U, 0x1FU, first_credits);
    if (reward_invoke(core, complete) != REWARD_RESULT
        || read16(core, factory + REWARD_BP_OFFSET) != 143U
        || read32(core, factory + REWARD_CLAIM_BITS_OFFSET) != 0xFFU
        || reward_item_count(core, REWARD_ITEM_ORAN) != 2U
        || reward_item_count(core, REWARD_ITEM_ULTRA) != 1U
        || reward_item_count(core, REWARD_ITEM_XS) != 5U
        || reward_item_count(core, REWARD_ITEM_S) != 2U)
        reward_die("streak credits and repeat reward did not coexist");
    reward_expect_credits(core, 1U, 1U, 1U, 1U, "streak coexistence");
    reward_require_party(core, original, original_count, "streak coexistence");
    reward_require_flash_ledger(core, "streak coexistence");

    reward_phase("bag-full-repeat");
    reward_empty_item(core, REWARD_ITEM_ORAN);
    uint32_t full_count = reward_fill_item(core, REWARD_ITEM_ORAN);
    reward_write32(core, REWARD_RNG_STATE, 0U);
    reward_prepare_completion(core, finalize, original, original_count,
                              200U, 3U, 0x1FU, first_credits);
    if (reward_invoke(core, complete) != REWARD_RESULT
        || read16(core, factory + REWARD_BP_OFFSET) != 209U
        || read32(core, factory + REWARD_CLAIM_BITS_OFFSET) != 0x1FU
        || reward_item_count(core, REWARD_ITEM_ORAN) != full_count
        || reward_item_count(core, REWARD_ITEM_ULTRA) != 1U
        || reward_item_count(core, REWARD_ITEM_XS) != 5U
        || reward_item_count(core, REWARD_ITEM_S) != 2U)
        reward_die("bag-full repeat reward altered Stage28 base completion");
    reward_expect_credits(core, 1U, 0U, 0U, 0U, "bag full repeat");
    reward_require_party(core, original, original_count, "bag full repeat");
    reward_require_flash_ledger(core, "bag full repeat");

    printf("{\"schema_version\":1,\"status\":\"PASS\","
           "\"checks\":{\"completion_wrapper_binding\":true,"
           "\"probe_and_save_init\":true,"
           "\"first_clear_excludes_repeat\":true,"
           "\"repeat_oran_branch\":true,"
           "\"repeat_ultra_branch\":true,"
           "\"streak_credit_coexistence\":true,"
           "\"bag_full_base_preserved\":true,"
           "\"normal_save_item_reload\":true,"
           "\"sector31_ledger_match\":true,"
           "\"exact_party_restore\":true},"
           "\"first_clear_bp\":112,\"oran_repeat_bp\":122,"
           "\"ultra_repeat_bp\":133,\"streak_repeat_bp\":143,"
           "\"bag_full_base_bp\":209,"
           "\"bag_full_capacity\":%" PRIu32 ","
           "\"framebuffer_transitions\":%" PRIu32 ","
           "\"artifacts_written\":[]}\n",
           full_count, transitions);

    fflush(stdout);
    /* The process is the isolation boundary.  Skip libmGBA teardown here:
     * the pinned host runtime can intermittently stall in core->deinit after
     * all exact-ROM assertions and output have completed. */
    _Exit(EXIT_SUCCESS);
}
