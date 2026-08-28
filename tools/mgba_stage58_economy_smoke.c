/* Stage58 exact-ROM T19 supply transaction and fresh-process persistence. */
#define BATTLE_CORE_ISOLATE_HOST_CALL_STACK 1
#define BATTLE_CORE_HOST_STACK_BOTTOM_ADDRESS 0x0203DB00U
#define BATTLE_CORE_HOST_STACK_TOP_ADDRESS 0x0203DF80U
#include <mgba/flags.h>
#define QOL_PRODUCTION_EMBEDDED
#include "mgba_qol_production_smoke.c"

enum {
    S58E_LEDGER_SIZE = 0x800U,
    S58E_REMOVE_BAG_ITEM = 0x08099BE1U,
    S58E_SET_BAG_POCKETS_POINTERS = 0x0809984DU,
    S58E_BAG_POCKETS = 0x020397D8U,
    S58E_GET_MONEY = 0x0809FC39U,
    S58E_SET_MONEY = 0x0809FC51U,
    S58E_ADD_MONEY = 0x0809FC81U,
    S58E_FACTORY_ADD_BP = 0x092DD9B1U,
    S58E_BATTLE_MON_MOVES_OFFSET = 0x0CU,
    S58E_BATTLE_MON_PP_OFFSET = 0x24U,
    S58E_PARTY_MAX_HP_OFFSET = 0x58U,
    S58E_BATTLE_MON_MAX_HP_OFFSET = 0x2CU,
    S58E_SPECIAL_VAR_RESULT = 0x02037004U,
    S58E_MAIN_NEW_KEYS = 0x0300315EU,
    S58E_FIELD_LOCK = 0x03000F9CU,
    S58E_CB2_OVERWORLD = 0x08055E75U,
    S58E_SCRIPT_CONTEXT1_SETUP = 0x080693A5U,
    S58E_SCRIPT_CONTEXT1_DISABLE = 0x08069231U,
    S58E_SCRIPT_CONTEXT2_DISABLE = 0x0806920DU,
    S58E_SCRIPT_CONTEXT2_ENABLE = 0x08069201U,
    S58E_WORLD_WARP = 0x09220861U,
    S58E_COLLECTION_HOST0_GROUP = 3U,
    S58E_COLLECTION_HOST0_MAP = 2U,
    S58E_COLLECTION_HOST0_X = 19U,
    S58E_COLLECTION_HOST0_Y = 26U,
    S58E_STARTMENU_SAVE = 4U,
    S58E_STARTMENU_SAVE_CALLBACK = 0x0806EDB9U,
    S58E_SAVE2_KEY_OFFSET = 0x0F20U,
    S58E_SAVE1_MONEY_OFFSET = 0x0290U,
    S58E_BAG_ITEMS_OFFSET = 0x0310U,
    S58E_BAG_ITEMS_CAPACITY = 42U,
    S58E_ITEM_PRICE_OFFSET = 12U,
    S58E_COLLECTION_RESULT_SUCCESS = 0U,
    S58E_COLLECTION_RESULT_INVALID = 5U,
    S58E_COLLECTION_SOURCE_MONEY = 0U,
    S58E_COLLECTION_SOURCE_RESEARCH = 2U,
    S58E_COLLECTION_SOURCE_EXISTING = 8U,
    S58E_COLLECTION_UNLOCK_NONE = 0U,
    S58E_COLLECTION_UNLOCK_PRE_ENTRY = 1U,
    S58E_COLLECTION_UNLOCK_BADGE_1 = 2U,
    S58E_COLLECTION_UNLOCK_KANTO_EARLY = 5U,
    S58E_COLLECTION_TEST_INITIALIZE = 0x09405F15U,
    S58E_COLLECTION_TEST_PURCHASE = 0x09405FA1U,
    S58E_COLLECTION_TEST_BALANCE = 0x094060E1U,
    S58E_COLLECTION_TEST_SET_BALANCES = 0x09406189U,
    S58E_COLLECTION_TEST_SET_BAG = 0x094061BDU,
    S58E_COLLECTION_TEST_BAG_COUNT = 0x094062D5U,
    S58E_COLLECTION_FIELD_HOST = 0x09405B11U,
    S58E_COLLECTION_HOST0_SCRIPT = 0x09411E1CU,
    S58E_COLLECTION_VOLATILE = 0x0203F720U,
    S58E_COLLECTION_OWNER = 0x0203D900U,
    S58E_COLLECTION_OWNER_END = 0x0203DB00U,
    S58E_COLLECTION_OWNER_MAGIC = 0x31565343U,
    S58E_COLLECTION_TEST_MODE_OFFSET = 27U,
    S58E_COLLECTION_PENDING_INDEX_OFFSET = 10U,
    S58E_COLLECTION_HOST_OFFSET = 18U,
    S58E_COLLECTION_MENU_MODE_OFFSET = 19U,
    S58E_COLLECTION_SERVICE_OFFSET = 20U,
    S58E_COLLECTION_PAGE_OFFSET = 21U,
    S58E_COLLECTION_MENU_ROOT = 0U,
    S58E_COLLECTION_MENU_ITEMS = 1U,
    S58E_COLLECTION_SERVICE_MONEY = 0U,
    S58E_COLLECTION_RESULT_BUSY = 9U,
    S58E_COLLECTION_PAGE_SIZE = 5U,
    S58E_VAR_8004 = 0x02036FF4U,
    S58E_QOL_SUPPLY_TABLE = 0x09381412U,
    S58E_QOL_SUPPLY_STRIDE = 8U,
    S58E_QOL_SUPPLY_COUNT = 49U,
    S58E_COLLECTION_REWARD_TABLE = 0x09408486U,
    S58E_COLLECTION_REWARD_STRIDE = 10U,
    S58E_COLLECTION_REWARD_COUNT = 217U,
    S58E_COLLECTION_ITEM_TABLE = 0x0940B088U,
    S58E_COLLECTION_ITEM_STRIDE = 12U,
    S58E_COLLECTION_ITEM_COUNT = 999U,
    S58E_COLLECTION_ITEM_PRICE_OFFSET = 2U,
    S58E_COLLECTION_ITEM_QUANTITY_OFFSET = 4U,
    S58E_COLLECTION_ITEM_SOURCE_OFFSET = 5U,
    S58E_COLLECTION_ITEM_UNLOCK_OFFSET = 6U,
    S58E_EXP_CANDY_XS_ITEM = 988U,
    S58E_HONEY_ITEM = 410U,
    S58E_HONEY_BUY_PRICE = 900U,
    S58E_HONEY_SELL_PRICE = 450U,
    S58E_ABILITY_PATCH_INDEX = 35U,
    S58E_ABILITY_PATCH_FEATURE = 23U,
    S58E_ABILITY_PATCH_ITEM = 943U,
    S58E_ABILITY_PATCH_PRICE = 64U,
    S58E_BP_SHOP_PURCHASE_BY_INDEX = 0x09377181U,
    S58E_TRAINER_PRIZE_EXPECTED = 128U,
    S58E_TRAINER_MONEY_AFTER = 3128U,
    S58E_NORMAL_TRAINER_SOURCE = 0x09376713U,
    S58E_NORMAL_TRAINER_ID = 89U,
    S58E_CLEAR_TRAINER_FLAG = 0x09302DCDU,
    S58E_APPROACHING_TRAINER_ID = 0x03000F29U,
    S58E_TRAINER_MONEY_BEFORE = 3000U,
    S58E_TRAINER_MONEY_AFTER_HONEY = 2228U,
    S58E_FACILITY_ENTER = 0x092CE491U,
    S58E_FACILITY_COMMIT = 0x092CE611U,
    S58E_FACILITY_PREPARE = 0x092CE715U,
    S58E_FACILITY_AFTER = 0x092CE7B9U,
    S58E_FACILITY_SKIP_EXCHANGE = 0x092CE8DDU,
    S58E_FACILITY_COMPLETE = 0x092CEA09U,
    S58E_FACILITY_OFFSET = 0x392U,
    S58E_FACILITY_BP_OFFSET = 0U,
    S58E_FACILITY_MARKER_OFFSET = 110U,
    S58E_FACILITY_SNAPSHOT_VALID_OFFSET = 111U,
    S58E_FACILITY_REWARD_PENDING_OFFSET = 113U,
    S58E_FACILITY_MARKER_SNAPSHOT = 1U,
    S58E_FACILITY_MARKER_BATTLE = 2U,
    S58E_FACILITY_SELECTED_ORDER = 0x0203C6C8U,
    S58E_SCHEDULER_STUB = 0x0203DF80U,
    S58E_BATTLE_SCRIPT = 0x0203DF80U,
    S58E_SCHEDULER_SCRATCH_END = 0x0203DFA0U,
    S58E_FACILITY_REWARD_BP = 9U,
    S58E_FACILITY_STATUS_COMPLETE = 9U,
    /* Scratch is Normal and can stall against a Ghost rental.  Struggle is
     * typeless in the production battle engine, so the 1-HP fixture remains
     * deterministic without writing an outcome, faint flag, or reward. */
    S58E_FACTORY_FIXTURE_MOVE = 165U,
    S58E_FACILITY_BP_BEFORE =
        S58E_ABILITY_PATCH_PRICE - S58E_FACILITY_REWARD_BP,
    S58E_BP_START = 1000U,
    S58E_BAG_STACK_MAX = 999U,
    S58E_MONEY_START = 10000U,
    S58E_MONEY_AFTER_HONEY = 9100U,
    S58E_RESULT_MENU_CANCELLED = 2U,
};

struct S58eResearchReprice {
    uint16_t item;
    uint16_t research_price;
    uint16_t sell_money;
};

/* This is the complete Stage58 correction set, not a sample.  The runner
 * re-reads every price and sell yield from the exact ROM before PASS. */
static const struct S58eResearchReprice S58E_RESEARCH_REPRICES[] = {
    {34U, 5U, 600U}, {35U, 8U, 1000U}, {36U, 12U, 1500U},
    {37U, 18U, 2250U}, {93U, 9U, 1050U}, {94U, 9U, 1050U},
    {95U, 9U, 1050U}, {96U, 9U, 1050U}, {97U, 9U, 1050U},
    {98U, 9U, 1050U}, {201U, 9U, 1050U}, {377U, 4U, 500U},
    {378U, 4U, 500U}, {379U, 4U, 500U}, {380U, 4U, 500U},
    {395U, 12U, 1500U}, {396U, 12U, 1500U},
    {397U, 12U, 1500U}, {398U, 12U, 1500U},
    {399U, 12U, 1500U}, {400U, 12U, 1500U},
    {401U, 12U, 1500U}, {402U, 12U, 1500U},
    {403U, 12U, 1500U}, {404U, 12U, 1500U}, {441U, 2U, 250U},
    {442U, 2U, 250U}, {443U, 2U, 250U}, {444U, 2U, 250U},
    {445U, 2U, 250U}, {452U, 2U, 250U}, {453U, 2U, 250U},
    {454U, 2U, 250U}, {455U, 2U, 250U}, {456U, 2U, 250U},
    {457U, 2U, 250U}, {458U, 2U, 250U}, {459U, 2U, 250U},
    {460U, 2U, 250U}, {469U, 12U, 1500U},
    {470U, 12U, 1500U}, {471U, 12U, 1500U},
    {473U, 20U, 2500U}, {475U, 12U, 1500U},
    {476U, 12U, 1500U}, {477U, 12U, 1500U},
    {478U, 12U, 1500U}, {479U, 12U, 1500U},
    {483U, 12U, 1500U}, {484U, 12U, 1500U},
    {485U, 12U, 1500U}, {486U, 12U, 1500U},
    {487U, 12U, 1500U}, {488U, 12U, 1500U},
    {489U, 12U, 1500U}, {490U, 12U, 1500U},
    {491U, 12U, 1500U}, {492U, 12U, 1500U},
    {493U, 12U, 1500U}, {494U, 12U, 1500U},
    {495U, 12U, 1500U}, {852U, 9U, 1050U},
    {944U, 12U, 1500U}, {945U, 12U, 1500U},
    {946U, 12U, 1500U}, {947U, 12U, 1500U},
    {948U, 12U, 1500U}, {949U, 12U, 1500U},
    {950U, 12U, 1500U}, {951U, 12U, 1500U},
    {962U, 76U, 9500U},
};

struct S58eEvidence {
    bool normal_menu_cancel_no_mutation;
    bool bag_full_no_debit;
    bool insufficient_no_mutation;
    bool cross_store_fault_rollback;
    bool limited_repeatable_reopen;
    bool currency_owner_api_integration;
    bool low_raid_xs;
    bool collection_owner_47;
    bool honey_no_profit;
    bool research_rate_71;
    bool currency_owner_api_saved;
    bool trainer_earned_purchased_saved;
    bool factory_earned_purchased_saved;
    bool trainer_fresh_reload;
    bool factory_fresh_reload;
    bool trainer_enemy_fainted;
    bool trainer_runtime_cleaned;
    uint32_t trainer_money_before;
    uint32_t trainer_money_after;
    uint32_t trainer_money_delta;
    uint32_t trainer_money_after_purchase;
    uint64_t trainer_save_hash;
    uint64_t factory_save_hash;
    uint32_t factory_purchase_raw_result;
    uint16_t factory_purchase_special_result;
    uint16_t factory_bp_before;
    uint16_t factory_bp_after;
    uint16_t factory_bp_delta;
    uint16_t factory_bp_after_purchase;
    uint8_t factory_outcomes[3];
    uint8_t trainer_outcome;
    uint8_t trainer_battlers_after;
    uint8_t factory_payload_starts;
    uint32_t reload_money;
    uint16_t reload_honey;
    uint16_t reload_bp;
    uint16_t reload_patch;
    uint32_t low_pre_hits;
    uint32_t low_post_hits;
    uint16_t collection_owner_count;
    uint16_t research_count;
};

_Static_assert(sizeof(S58E_RESEARCH_REPRICES)
                   / sizeof(S58E_RESEARCH_REPRICES[0]) == 71U,
               "Stage58 Research correction set must stay complete");
_Static_assert(BATTLE_CORE_HOST_STACK_BOTTOM == 0x0203DB00U
                   && BATTLE_CORE_HOST_STACK_TOP == 0x0203DF80U,
               "Stage58 economy host-call stack contract drifted");
_Static_assert(BATTLE_CORE_HOST_STACK_BOTTOM >= 0x0203DB00U
                   && BATTLE_CORE_HOST_STACK_TOP <= 0x0203DFA0U,
               "Stage58 economy host-call stack overlaps a live RAM owner");
_Static_assert((uint32_t)BATTLE_CORE_HOST_STACK_TOP
                   <= (uint32_t)S58E_SCHEDULER_STUB
                   && S58E_SCHEDULER_SCRATCH_END <= 0x0203DFA0U,
               "Stage58 economy scheduler trampoline overlaps host stack/terrain");

static void s58e_die(const char *message)
{
    fprintf(stderr, "mgba-stage58-economy: %s\n", message);
    exit(1);
}

static bool s58e_collection_test_initialize(struct mCore *core);
static void s58e_disable_script_contexts(struct mCore *core);

static void s58e_trace(const char *step)
{
    if (getenv("MGBA_STAGE58_ECONOMY_TRACE") != NULL)
        fprintf(stderr, "mgba-stage58-economy: step=%s\n", step);
}

static uint32_t s58e_call_exact(struct mCore *core, uint32_t function,
                                uint32_t r0, uint32_t r1,
                                uint32_t r2, uint32_t r3)
{
    uint32_t resume_pc = (uint32_t)read_register(core, "pc");
    uint32_t resume_cpsr = (uint32_t)read_register(core, "cpsr");
    uint32_t pipeline = (resume_cpsr & 0x20U) != 0U ? 2U : 4U;
    uint32_t result = call_bounded(core, function, r0, r1, r2, r3).result;
    if ((uint32_t)read_register(core, "pc") != resume_pc) {
        write_register(core, "pc", resume_pc - pipeline);
        if ((uint32_t)read_register(core, "pc") != resume_pc)
            s58e_die("host call scheduler PC restore failed");
    }
    return result;
}

static void s58e_repair_wait_pc(struct mCore *core)
{
    uint32_t pc = (uint32_t)read_register(core, "pc");
    if (pc >= 0x080008B8U && pc <= 0x080008C0U) {
        write_register(core, "pc", 0x080008AAU);
        if ((uint32_t)read_register(core, "pc") != 0x080008ACU)
            s58e_die("wait-loop scheduler PC repair failed");
    }
}

static bool s58e_sync_host_call_pc(struct mCore *core)
{
    for (unsigned frame = 0U; frame < 120U; ++frame) {
        uint32_t pc = (uint32_t)read_register(core, "pc");
        if (pc >= 0x08000000U && pc < 0x0A000000U)
            return true;
        run_key_frames(core, 0U, 1U);
    }
    return false;
}

static uint32_t s58e_call_synced(struct mCore *core, uint32_t function,
                                 uint32_t r0, uint32_t r1,
                                 uint32_t r2, uint32_t r3)
{
    if (read8(core, S58E_FIELD_LOCK) != 0U
        || !s58e_sync_host_call_pc(core))
        return UINT32_MAX;
    uint32_t result = call_preserving(core, function, r0, r1, r2, r3);
    run_key_frames(core, 0U, 1U);
    return result;
}

static uint64_t s58e_hash(struct mCore *core, uint32_t address, size_t size)
{
    uint64_t hash = UINT64_C(14695981039346656037);
    for (size_t index = 0; index < size; ++index) {
        hash ^= read8(core, address + (uint32_t)index);
        hash *= UINT64_C(1099511628211);
    }
    return hash;
}

static bool s58e_savedata_hash(struct mCore *core, uint64_t *hash_out)
{
    void *sram = NULL;
    size_t size = core->savedataClone(core, &sram);
    if (sram == NULL || size != QOL_SAVE_SIZE) {
        free(sram);
        return false;
    }
    uint64_t hash = UINT64_C(14695981039346656037);
    const uint8_t *bytes = sram;
    for (size_t index = 0U; index < size; ++index) {
        hash ^= bytes[index];
        hash *= UINT64_C(1099511628211);
    }
    free(sram);
    *hash_out = hash;
    return true;
}

static bool s58e_bind_bag_pockets(struct mCore *core)
{
    static const uint8_t capacities[5] = {42U, 30U, 13U, 58U, 43U};
    (void)call_preserving(
        core, S58E_SET_BAG_POCKETS_POINTERS, 0U, 0U, 0U, 0U);
    for (unsigned pocket = 0U; pocket < ARRAY_LEN(capacities); ++pocket) {
        uint32_t descriptor = S58E_BAG_POCKETS + pocket * 8U;
        uint32_t slots = read32(core, descriptor);
        if (slots < 0x02000000U || slots >= 0x02040000U
            || (slots & 1U) != 0U
            || read8(core, descriptor + 4U) != capacities[pocket])
            return false;
    }
    return true;
}

static bool s58e_normal_menu_save(struct mCore *core, uint64_t *hash_after)
{
    s58e_repair_wait_pc(core);
    run_key_frames(core, 0U, 1U);
    if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58E_CB2_OVERWORLD
        || read8(core, S58E_FIELD_LOCK) != 0U
        || !s58e_bind_bag_pockets(core)) {
        fprintf(stderr, "normal save pre cb=%08" PRIx32 " lock=%u\n",
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read8(core, S58E_FIELD_LOCK));
        return false;
    }
    run_key_frames(core, 0U, 1U);
    uint64_t before = 0U;
    if (!s58e_savedata_hash(core, &before))
        return false;
    qol_press(core, QOL_KEY_START, 120U);
    if (read32(core, QOL_START_MENU_CALLBACK) != QOL_START_MENU_INPUT) {
        fprintf(stderr, "normal save start callback=%08" PRIx32 " cb=%08" PRIx32 "\n",
                read32(core, QOL_START_MENU_CALLBACK),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2));
        return false;
    }
    uint8_t count = read8(core, QOL_START_MENU_COUNT);
    uint8_t cursor = read8(core, QOL_START_MENU_CURSOR);
    if (count == 0U || count > 9U || cursor >= count)
        return false;
    uint8_t target = count;
    for (uint8_t index = 0U; index < count; ++index) {
        if (read8(core, QOL_START_MENU_ORDER + index) == S58E_STARTMENU_SAVE) {
            target = index;
            break;
        }
    }
    if (target >= count)
        return false;
    unsigned down = (unsigned)(target + count - cursor) % count;
    unsigned up = (unsigned)(cursor + count - target) % count;
    uint16_t key = down <= up ? QOL_KEY_DOWN : QOL_KEY_UP;
    unsigned steps = down <= up ? down : up;
    for (unsigned step = 0U; step < steps; ++step)
        qol_press(core, key, 30U);
    if (read8(core, QOL_START_MENU_CURSOR) != target)
        return false;
    qol_press(core, QOL_KEY_A, 120U);
    bool callback_seen = false;
    for (unsigned prompt = 0U; prompt < 32U; ++prompt) {
        s58e_repair_wait_pc(core);
        if (read32(core, QOL_START_MENU_CALLBACK)
                == S58E_STARTMENU_SAVE_CALLBACK)
            callback_seen = true;
        uint64_t current = 0U;
        if (callback_seen && s58e_savedata_hash(core, &current)
            && current != before
            && read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S58E_CB2_OVERWORLD
            && read8(core, S58E_FIELD_LOCK) == 0U) {
            run_key_frames(core, 0U, 180U);
            return s58e_savedata_hash(core, hash_after)
                && *hash_after != before
                && read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                    == S58E_CB2_OVERWORLD
                && read8(core, S58E_FIELD_LOCK) == 0U;
        }
        /* JP same-file Save is DefaultYes: ordinary A advances both prompts. */
        qol_press(core, QOL_KEY_A, 180U);
    }
    fprintf(stderr, "normal save timeout callback_seen=%u menu=%08" PRIx32
            " cb=%08" PRIx32 " lock=%u\n", callback_seen ? 1U : 0U,
            read32(core, QOL_START_MENU_CALLBACK),
            read32(core, BATTLE_CORE_MAIN_CALLBACK2),
            read8(core, S58E_FIELD_LOCK));
    return false;
}

static uint16_t s58e_item_count(struct mCore *core, uint16_t item)
{
    uint16_t count = 0U;
    while (count < 999U
           && call_preserving(core, QOL_CHECK_BAG_ITEM,
                              item, (uint16_t)(count + 1U), 0, 0))
        ++count;
    return count;
}

static uint16_t s58e_saved_item_count(struct mCore *core, uint16_t item)
{
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    if (save1 < 0x02000000U || save1 >= 0x02040000U
        || save2 < 0x02000000U || save2 >= 0x02040000U)
        return 0U;
    uint16_t key = read16(core, save2 + S58E_SAVE2_KEY_OFFSET);
    for (uint32_t slot = 0U; slot < S58E_BAG_ITEMS_CAPACITY; ++slot) {
        uint32_t row = save1 + S58E_BAG_ITEMS_OFFSET + slot * 4U;
        if (read16(core, row) == item)
            return read16(core, row + 2U) ^ key;
    }
    return 0U;
}

static void s58e_remove_all(struct mCore *core, uint16_t item)
{
    uint16_t count = s58e_item_count(core, item);
    if (count != 0U
        && call_preserving(core, S58E_REMOVE_BAG_ITEM,
                           item, count, 0, 0) == 0U)
        s58e_die("bag cleanup failed");
    if (s58e_item_count(core, item) != 0U)
        s58e_die("bag cleanup left items");
}

static uint16_t s58e_fill_stack(struct mCore *core, uint16_t item)
{
    uint16_t before = s58e_item_count(core, item);
    uint32_t added = 0U;
    for (uint16_t chunk = 512U; chunk != 0U; chunk >>= 1U) {
        while (call_preserving(core, QOL_ADD_BAG_ITEM,
                               item, chunk, 0, 0) != 0U) {
            added += chunk;
            if (added > 999U)
                s58e_die("bag stack exceeded engine limit");
        }
    }
    uint16_t after = s58e_item_count(core, item);
    uint32_t overflow = call_preserving(
        core, QOL_ADD_BAG_ITEM, item, 1U, 0, 0);
    if (after <= before || overflow != 0U) {
        fprintf(stderr, "bag fill before=%u after=%u added=%" PRIu32
                " overflow=%" PRIu32 "\n",
                before, after, added, overflow);
        s58e_die("bag stack did not reach capacity");
    }
    return after;
}

static void s58e_set_bp(struct mCore *core, uint16_t value)
{
    write16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP, value);
    (void)call_preserving(core, QOL_SAVE_FINALIZE, QOL_LEDGER, 0, 0, 0);
}

static uint32_t s58e_money_pointer(struct mCore *core)
{
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    if (save1 < 0x02000000U
        || save1 + S58E_SAVE1_MONEY_OFFSET + 4U > 0x02040000U)
        return 0U;
    return save1 + S58E_SAVE1_MONEY_OFFSET;
}

static uint32_t s58e_money(struct mCore *core)
{
    uint32_t pointer = s58e_money_pointer(core);
    return pointer == 0U ? UINT32_MAX
                         : s58e_call_exact(core, S58E_GET_MONEY,
                                           pointer, 0U, 0U, 0U);
}

static uint32_t s58e_money_read_only(struct mCore *core)
{
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    uint32_t save2 = read32(core, QOL_SAVE_BLOCK2_SLOT);
    if (save1 < 0x02000000U || save1 >= 0x02040000U
        || save2 < 0x02000000U || save2 >= 0x02040000U)
        return UINT32_MAX;
    return read32(core, save1 + S58E_SAVE1_MONEY_OFFSET)
        ^ read32(core, save2 + S58E_SAVE2_KEY_OFFSET);
}

static bool s58e_currency_owner_api_add(struct mCore *core)
{
    uint32_t money = s58e_money_pointer(core);
    if (money == 0U)
        return false;
    /* This deliberately verifies the two production currency-owner APIs,
     * not an in-field trainer or Factory battle reward. */
    (void)call_preserving(core, S58E_SET_MONEY, money, 0U, 0, 0);
    (void)call_preserving(core, S58E_ADD_MONEY,
                          money, S58E_MONEY_START, 0, 0);
    s58e_set_bp(core, 0U);
    uint32_t bp_status = call_preserving(
        core, S58E_FACTORY_ADD_BP, QOL_LEDGER, S58E_BP_START, 0, 0);
    return s58e_money(core) == S58E_MONEY_START
        && bp_status == 0U
        && read16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP) == S58E_BP_START;
}

static bool s58e_scheduler_call_r0_internal(
    struct mCore *core, uint32_t target, uint32_t argument,
    uint8_t expected_lock, uint32_t *result_out)
{
    s58e_repair_wait_pc(core);
    if ((target & 1U) == 0U || (target & ~1U) < 0x08000000U
        || (target & ~1U) >= 0x0A000000U
        || read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58E_CB2_OVERWORLD
        || read8(core, S58E_FIELD_LOCK) != 0U || argument != 0U) {
        fprintf(stderr, "scheduler precondition target=%08" PRIx32
                " cb=%08" PRIx32 " lock=%u magic=%08" PRIx32 "\n",
                target, read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read8(core, S58E_FIELD_LOCK),
                read32(core, S58E_COLLECTION_OWNER));
        return false;
    }
    uint8_t saved[S58E_SCHEDULER_SCRATCH_END - S58E_SCHEDULER_STUB];
    for (size_t byte = 0U; byte < sizeof(saved); ++byte)
        saved[byte] = read8(core, S58E_SCHEDULER_STUB + (uint32_t)byte);
    /* Data-only field bytecode.  The target owns gSpecialVar_Result; no CPU
     * instruction is ever executed from EWRAM (mGBA dynarec-safe). */
    write8(core, S58E_SCHEDULER_STUB + 0U, 0x23U);
    write32_bytes(core, S58E_SCHEDULER_STUB + 1U, target);
    write8(core, S58E_SCHEDULER_STUB + 5U, 0x02U);
    write16(core, S58E_SPECIAL_VAR_RESULT, UINT16_MAX);
    (void)call_preserving(core, S58E_SCRIPT_CONTEXT1_SETUP,
                          S58E_SCHEDULER_STUB, 0U, 0U, 0U);
    uint32_t result = UINT16_MAX;
    unsigned stable = 0U;
    for (unsigned frame = 0U; frame < 3600U && stable < 30U; ++frame) {
        s58e_repair_wait_pc(core);
        run_key_frames(core, 0U, 1U);
        result = read16(core, S58E_SPECIAL_VAR_RESULT);
        if (result != UINT16_MAX
            && read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                == S58E_CB2_OVERWORLD
            && read8(core, S58E_FIELD_LOCK) == expected_lock)
            ++stable;
        else
            stable = 0U;
    }
    bool completed = stable == 30U;
    for (size_t byte = 0U; byte < sizeof(saved); ++byte)
        write8(core, S58E_SCHEDULER_STUB + (uint32_t)byte, saved[byte]);
    if (!completed)
        fprintf(stderr, "scheduler incomplete target=%08" PRIx32
                " result=%08" PRIx32 " cb=%08" PRIx32
                " lock=%u pc=%08" PRIx32 " magic=%08" PRIx32 "\n",
                target, result,
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read8(core, S58E_FIELD_LOCK),
                (uint32_t)read_register(core, "pc"),
                read32(core, S58E_COLLECTION_OWNER));
    if (completed && result_out != NULL)
        *result_out = result;
    return completed;
}

static bool s58e_scheduler_call_r0(struct mCore *core, uint32_t target,
                                   uint32_t argument, uint32_t *result_out)
{
    return s58e_scheduler_call_r0_internal(
        core, target, argument, 0U, result_out);
}

static bool s58e_scheduler_expect_r0(struct mCore *core, uint32_t target,
                                     uint32_t argument, uint32_t expected)
{
    uint32_t actual = UINT32_MAX;
    return s58e_scheduler_call_r0(core, target, argument, &actual)
        && actual == expected;
}

static bool s58e_facility_direct_expect(struct mCore *core, uint32_t target,
                                        uint32_t expected)
{
    if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58E_CB2_OVERWORLD
        || read8(core, S58E_FIELD_LOCK) != 0U
        || !s58e_sync_host_call_pc(core))
        return false;
    write16(core, S58E_SPECIAL_VAR_RESULT, UINT16_MAX);
    uint32_t actual = call_preserving(core, target, 0U, 0U, 0U, 0U);
    /* Facility callnative entrypoints publish their semantic return through
     * gSpecialVar_Result and leave r0 as the host-call LR sentinel. */
    bool passed = actual == 0x08000001U
        && read16(core, S58E_SPECIAL_VAR_RESULT) == expected
        && read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S58E_CB2_OVERWORLD
        && read8(core, S58E_FIELD_LOCK) == 0U;
    if (!passed)
        fprintf(stderr, "facility direct target=%08" PRIx32
                " actual=%" PRIu32 " special=%u expected=%" PRIu32
                " cb=%08" PRIx32 " lock=%u\n", target, actual,
                read16(core, S58E_SPECIAL_VAR_RESULT), expected,
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read8(core, S58E_FIELD_LOCK));
    return passed;
}

static bool s58e_warp_to_collection_host0(struct mCore *core)
{
    uint16_t stand_y = S58E_COLLECTION_HOST0_Y + 1U;
    run_key_frames(core, 0U, 2U);
    if (s58e_call_synced(core, S58E_WORLD_WARP,
                         S58E_COLLECTION_HOST0_GROUP,
                         S58E_COLLECTION_HOST0_MAP,
                         S58E_COLLECTION_HOST0_X, stand_y) == UINT32_MAX)
        return false;
    run_key_frames(core, 0U, 1800U);
    if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58E_CB2_OVERWORLD)
        run_key_frames(core, 0U, 1800U);
    if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58E_CB2_OVERWORLD) {
        qol_press(core, QOL_KEY_B, 180U);
        run_key_frames(core, 0U, 1800U);
    }
    uint32_t save1 = read32(core, QOL_SAVE_BLOCK1_SLOT);
    if (save1 < 0x02000000U || save1 >= 0x02040000U
        || read8(core, save1 + 4U) != S58E_COLLECTION_HOST0_GROUP
        || read8(core, save1 + 5U) != S58E_COLLECTION_HOST0_MAP
        || read16(core, save1) != S58E_COLLECTION_HOST0_X
        || read16(core, save1 + 2U) != stand_y
        || read8(core, S58E_FIELD_LOCK) != 0U) {
        fprintf(stderr, "collection warp save=%08" PRIx32
                " got=%u/%u %u,%u cb=%08" PRIx32 " lock=%u\n",
                save1,
                save1 < 0x02000000U || save1 >= 0x02040000U
                    ? 0U : read8(core, save1 + 4U),
                save1 < 0x02000000U || save1 >= 0x02040000U
                    ? 0U : read8(core, save1 + 5U),
                save1 < 0x02000000U || save1 >= 0x02040000U
                    ? 0U : read16(core, save1),
                save1 < 0x02000000U || save1 >= 0x02040000U
                    ? 0U : read16(core, save1 + 2U),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read8(core, S58E_FIELD_LOCK));
        return false;
    }
    /* A one-frame tap turns toward the north event without sustained walking;
     * the following ordinary A owns the event lookup and script launch. */
    run_key_frames(core, QOL_KEY_UP, 1U);
    run_key_frames(core, 0U, 30U);
    if (getenv("MGBA_STAGE58_ECONOMY_TRACE") != NULL) {
        uint8_t object_id = read8(core, 0x02036FACU + 5U);
        uint32_t object = 0x02036D6CU + object_id * 0x24U;
        fprintf(stderr, "collection face object=%u active=%02x facing=%u"
                " avatar=%u/%u cb=%08" PRIx32 " pos=%u,%u\n",
                object_id, object_id < 16U ? read8(core, object) : 0U,
                object_id < 16U ? read8(core, object + 0x18U) & 0xFU : 0U,
                read8(core, 0x02036FACU + 2U),
                read8(core, 0x02036FACU + 3U),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read16(core, save1), read16(core, save1 + 2U));
    }
    bool faced = read16(core, save1) == S58E_COLLECTION_HOST0_X
        && read16(core, save1 + 2U) == stand_y;
    if (!faced)
        fprintf(stderr, "collection face moved=%u,%u wanted=%u,%u\n",
                read16(core, save1), read16(core, save1 + 2U),
                S58E_COLLECTION_HOST0_X, stand_y);
    return faced;
}

static bool s58e_collection_honey_ui_purchase(struct mCore *core,
                                               uint32_t expected_before,
                                               uint32_t expected_after,
                                               unsigned honey_ordinal)
{
    s58e_remove_all(core, S58E_HONEY_ITEM);
    if (read8(core, S58E_COLLECTION_HOST0_SCRIPT) != 0x6AU)
        return false;
    if (!s58e_warp_to_collection_host0(core))
        return false;
    run_key_frames(core, QOL_KEY_A, 2U);
    run_key_frames(core, 0U, 30U);
    bool opened = false;
    for (unsigned frame = 0U; frame < 600U; ++frame) {
        s58e_repair_wait_pc(core);
        run_key_frames(core, 0U, 1U);
        if (read16(core, S58E_SPECIAL_VAR_RESULT)
                == S58E_COLLECTION_RESULT_BUSY
            && read8(core, S58E_FIELD_LOCK) == 1U) {
            opened = true;
            break;
        }
    }
    if (!opened
        || read8(core, S58E_COLLECTION_VOLATILE
                         + S58E_COLLECTION_HOST_OFFSET) != 0U
        || read8(core, S58E_COLLECTION_VOLATILE
                         + S58E_COLLECTION_MENU_MODE_OFFSET)
            != S58E_COLLECTION_MENU_ROOT
        || read8(core, S58E_COLLECTION_VOLATILE
                         + S58E_COLLECTION_SERVICE_OFFSET)
            != S58E_COLLECTION_SERVICE_MONEY)
        return false;

    /* Root row 1 opens the money-item service.  The exact-ROM catalog scan
     * supplies Honey's live ordinal; all transitions are ordinary input. */
    qol_press(core, QOL_KEY_DOWN, 30U);
    qol_press(core, QOL_KEY_A, 90U);
    if (read8(core, S58E_COLLECTION_VOLATILE
                      + S58E_COLLECTION_MENU_MODE_OFFSET)
            != S58E_COLLECTION_MENU_ITEMS
        || read8(core, S58E_COLLECTION_VOLATILE
                         + S58E_COLLECTION_PAGE_OFFSET) != 0U)
        return false;
    unsigned target_page = honey_ordinal / S58E_COLLECTION_PAGE_SIZE;
    unsigned target_row = honey_ordinal % S58E_COLLECTION_PAGE_SIZE;
    for (unsigned page = 0U; page < target_page; ++page) {
        for (unsigned row = 0U; row < S58E_COLLECTION_PAGE_SIZE; ++row)
            qol_press(core, QOL_KEY_DOWN, 20U);
        qol_press(core, QOL_KEY_A, 90U);
        if (read8(core, S58E_COLLECTION_VOLATILE
                          + S58E_COLLECTION_PAGE_OFFSET) != page + 1U)
            return false;
    }
    for (unsigned row = 0U; row < target_row; ++row)
        qol_press(core, QOL_KEY_DOWN, 20U);
    uint32_t before_money = s58e_money_read_only(core);
    uint16_t before_honey = s58e_saved_item_count(core, S58E_HONEY_ITEM);
    qol_press(core, QOL_KEY_A, 0U);
    s58e_repair_wait_pc(core);
    bool committed = before_money == expected_before
        && before_honey == 0U
        && read16(core, S58E_COLLECTION_VOLATILE
                          + S58E_COLLECTION_PENDING_INDEX_OFFSET)
            == S58E_HONEY_ITEM;
    /* The transaction persists both stores before finish_menu publishes its
     * result.  Keep released input while that production owner completes,
     * then require 30 consecutive field-return frames. */
    unsigned stable = 0U;
    for (unsigned frame = 0U; frame < 3600U && stable < 30U; ++frame) {
        s58e_repair_wait_pc(core);
        run_key_frames(core, 0U, 1U);
        if (read16(core, S58E_SPECIAL_VAR_RESULT)
                    == S58E_COLLECTION_RESULT_SUCCESS
            && read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S58E_CB2_OVERWORLD
            && read8(core, S58E_FIELD_LOCK) == 0U)
            ++stable;
        else
            stable = 0U;
    }
    bool returned = committed
        && stable == 30U
        && read16(core, S58E_SPECIAL_VAR_RESULT)
            == S58E_COLLECTION_RESULT_SUCCESS
        && s58e_money_read_only(core) == expected_after
        && s58e_saved_item_count(core, S58E_HONEY_ITEM) == 1U
        && read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S58E_CB2_OVERWORLD
        && read8(core, S58E_FIELD_LOCK) == 0U;
    if (!returned)
        fprintf(stderr, "collection return committed=%u result=%u pending=%u"
                " lock=%u ctx1mode=%u ctx1ptr=%08" PRIx32
                " cb=%08" PRIx32 " money=%" PRIu32 " honey=%u\n",
                committed ? 1U : 0U,
                read16(core, S58E_SPECIAL_VAR_RESULT),
                read16(core, S58E_COLLECTION_VOLATILE
                             + S58E_COLLECTION_PENDING_INDEX_OFFSET),
                read8(core, S58E_FIELD_LOCK), read8(core, 0x03000EA8U),
                read32(core, 0x03000EB8U),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                s58e_money_read_only(core),
                s58e_saved_item_count(core, S58E_HONEY_ITEM));
    return returned;
}

static bool s58e_honey_ordinal(struct mCore *core, unsigned *ordinal_out)
{
    unsigned ordinal = 0U;
    for (uint32_t item = 0U; item <= S58E_HONEY_ITEM; ++item) {
        uint32_t row = S58E_COLLECTION_ITEM_TABLE
            + item * S58E_COLLECTION_ITEM_STRIDE;
        if (read16(core, row) != item)
            return false;
        uint8_t unlock = read8(
            core, row + S58E_COLLECTION_ITEM_UNLOCK_OFFSET);
        bool eligible = read8(core, row + S58E_COLLECTION_ITEM_SOURCE_OFFSET)
                == S58E_COLLECTION_SOURCE_MONEY
            && (unlock == S58E_COLLECTION_UNLOCK_NONE
                || unlock == S58E_COLLECTION_UNLOCK_PRE_ENTRY
                || unlock == S58E_COLLECTION_UNLOCK_BADGE_1);
        if (item == S58E_HONEY_ITEM) {
            if (!eligible)
                return false;
            *ordinal_out = ordinal;
            break;
        }
        if (eligible)
            ++ordinal;
    }
    return true;
}

static bool s58e_actual_honey_purchase(struct mCore *core)
{
    unsigned ordinal = 0U;
    return s58e_honey_ordinal(core, &ordinal)
        && s58e_collection_honey_ui_purchase(
        core, S58E_TRAINER_MONEY_AFTER,
        S58E_TRAINER_MONEY_AFTER_HONEY, ordinal);
}

struct S58eBattleScript {
    uint8_t saved[15];
    bool armed;
};

static void s58e_restore_battle_script(struct mCore *core,
                                       struct S58eBattleScript *script);

static bool s58e_start_trainer_script(struct mCore *core,
                                      struct S58eBattleScript *script,
                                      bool authored_trainerbattle,
                                      uint16_t trainer_id,
                                      uint16_t local_id)
{
    if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58E_CB2_OVERWORLD
        || read8(core, S58E_FIELD_LOCK) != 0U)
        return false;
    uint32_t script_address = S58E_BATTLE_SCRIPT;
    if (authored_trainerbattle) {
        static const uint8_t expected[14] = {
            0x5CU, 0x00U, 0x59U, 0x00U, 0x00U, 0x00U, 0x90U,
            0x3DU, 0x36U, 0x09U, 0x97U, 0x45U, 0x36U, 0x09U,
        };
        if (trainer_id != S58E_NORMAL_TRAINER_ID || local_id != 0U)
            return false;
        for (size_t byte = 0U; byte < sizeof(expected); ++byte) {
            if (read8(core, S58E_NORMAL_TRAINER_SOURCE + (uint32_t)byte)
                    != expected[byte])
                return false;
        }
        for (size_t byte = 0U; byte < sizeof(script->saved); ++byte)
            script->saved[byte] = read8(
                core, S58E_BATTLE_SCRIPT + (uint32_t)byte);
        script->armed = true;
        for (size_t byte = 0U; byte < sizeof(expected); ++byte)
            write8(core, S58E_BATTLE_SCRIPT + (uint32_t)byte,
                   expected[byte]);
        write8(core, S58E_BATTLE_SCRIPT + 14U, 0x02U);
    } else {
        static const uint8_t factory_launch[] = {
            0x25U, 0x29U, 0x00U, 0x27U, 0x5DU, 0x02U,
        };
        /* Factory Prepare owns flags/parties.  The production launch boundary
         * is special 0x29; waitstate; battlebegin; end, not bare battlebegin. */
        for (size_t byte = 0U; byte < sizeof(script->saved); ++byte)
            script->saved[byte] = read8(
                core, S58E_BATTLE_SCRIPT + (uint32_t)byte);
        script->armed = true;
        for (size_t byte = 0U; byte < sizeof(factory_launch); ++byte)
            write8(core, S58E_BATTLE_SCRIPT + (uint32_t)byte,
                   factory_launch[byte]);
    }
    s58e_repair_wait_pc(core);
    if (!s58e_sync_host_call_pc(core)) {
        s58e_restore_battle_script(core, script);
        return false;
    }
    (void)call_preserving(core, S58E_SCRIPT_CONTEXT1_SETUP,
                          script_address, 0U, 0U, 0U);
    /* Stock single-trainer commands are driven by ScriptContext1 alone.
     * Factory's bare battlebegin is an event-owned blocking command and
     * therefore additionally owns Context2. */
    if (!authored_trainerbattle)
        (void)call_preserving(core, S58E_SCRIPT_CONTEXT2_ENABLE,
                              0U, 0U, 0U, 0U);
    if (getenv("MGBA_STAGE58_ECONOMY_BATTLE_TRACE") != NULL)
        fprintf(stderr, "battle-pref=%08" PRIx32 " cb=%08" PRIx32
                " lock=%u bytes=%02x/%02x/%02x enabled=%" PRIu32
                " keys=%04x/%04x/%04x/%04x\n",
                (uint32_t)read_register(core, "pc"),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read8(core, S58E_FIELD_LOCK),
                read8(core, S58E_BATTLE_SCRIPT),
                read8(core, S58E_BATTLE_SCRIPT + 1U),
                read8(core, S58E_BATTLE_SCRIPT + 10U),
                call_preserving(core, QOL_SCRIPT_CONTEXT_ENABLED,
                                0U, 0U, 0U, 0U),
                read16(core, 0x0300315CU), read16(core, 0x0300315EU),
                read16(core, 0x03003160U), read16(core, 0x03003168U));
    for (unsigned frame = 0U; frame < 3600U; ++frame) {
        s58e_repair_wait_pc(core);
        uint16_t key = authored_trainerbattle || frame % 3U != 2U
            ? QOL_KEY_A : QOL_KEY_DOWN;
        run_key_frames(core, key, 2U);
        run_key_frames(core, 0U, 30U);
        if (getenv("MGBA_STAGE58_ECONOMY_BATTLE_TRACE") != NULL
            && frame < 40U)
            fprintf(stderr, "battle-frame=%u pc=%08" PRIx32
                    " cb=%08" PRIx32 " lock=%u battlers=%u"
                    " newbs=%08" PRIx32 " flags=%08" PRIx32
                    " bytes=%02x/%02x\n", frame,
                    (uint32_t)read_register(core, "pc"),
                    read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                    read8(core, S58E_FIELD_LOCK),
                    read8(core, ADDR_BATTLERS_COUNT),
                    read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER),
                    read32(core, ADDR_BATTLE_TYPE_FLAGS),
                    read8(core, S58E_BATTLE_SCRIPT),
                    read8(core, S58E_BATTLE_SCRIPT + 1U));
        if (read8(core, ADDR_BATTLERS_COUNT) == 2U
            && read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0U) {
            return true;
        }
    }
    (void)call_preserving(core, S58E_SCRIPT_CONTEXT1_DISABLE,
                          0U, 0U, 0U, 0U);
    (void)call_preserving(core, S58E_SCRIPT_CONTEXT2_DISABLE,
                          0U, 0U, 0U, 0U);
    s58e_restore_battle_script(core, script);
    fprintf(stderr, "battle script start timeout trainer=%u cb=%08" PRIx32
            " battlers=%u newbs=%08" PRIx32 " flags=%08" PRIx32
            " bytes=%02x/%02x pc=%08" PRIx32 "\n",
            authored_trainerbattle ? 1U : 0U,
            read32(core, BATTLE_CORE_MAIN_CALLBACK2),
            read8(core, ADDR_BATTLERS_COUNT),
            read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER),
            read32(core, ADDR_BATTLE_TYPE_FLAGS),
            read8(core, S58E_BATTLE_SCRIPT),
            read8(core, S58E_BATTLE_SCRIPT + 1U),
            (uint32_t)read_register(core, "pc"));
    return false;
}

static void s58e_restore_battle_script(struct mCore *core,
                                        struct S58eBattleScript *script)
{
    if (!script->armed)
        return;
    for (size_t byte = 0U; byte < sizeof(script->saved); ++byte)
        write8(core, S58E_BATTLE_SCRIPT + (uint32_t)byte,
               script->saved[byte]);
    script->armed = false;
}

static bool s58e_finish_current_trainer_battle(
    struct mCore *core, struct S58eBattleScript *script,
    struct EndObservation *result)
{
    result->trainer = true;
    result->battle_runtime_initialized =
        read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0U;
    if (!result->battle_runtime_initialized
        || read8(core, ADDR_BATTLERS_COUNT) != 2U
        || (read32(core, ADDR_BATTLE_TYPE_FLAGS) & BATTLE_TYPE_TRAINER)
            == 0U) {
        s58e_restore_battle_script(core, script);
        return false;
    }
    for (unsigned slot = 0U; slot < 3U; ++slot)
        write16(core, ADDR_ENEMY_PARTY + slot * POKEMON_SIZE
                          + POKEMON_CURRENT_HP_OFFSET, 1U);
    write16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                      + BATTLE_CORE_MON_HP, 1U);
    for (unsigned press = 0U; press < BATTLE_CORE_TURN_INPUT_PRESSES;
         ++press) {
        write8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR, 0U);
        run_end_frames(core, result, QOL_KEY_A, 2U);
        run_end_frames(core, result, 0U, BATTLE_CORE_TURN_INPUT_WAIT);
    }
    for (unsigned pulse = 0U;
         pulse < BATTLE_CORE_END_INPUT_PULSES
             && !result->battle_runtime_cleaned;
         ++pulse) {
        run_end_frames(core, result, QOL_KEY_A, 2U);
        run_end_frames(core, result, 0U, BATTLE_CORE_END_INPUT_WAIT);
    }
    run_end_frames(core, result, 0U, 180U);
    for (unsigned pulse = 0U; pulse < 120U
        && (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58E_CB2_OVERWORLD
             || read8(core, S58E_FIELD_LOCK) != 0U
             || read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0U); ++pulse) {
        run_end_frames(core, result, QOL_KEY_A, 2U);
        run_end_frames(core, result, 0U, 30U);
    }
    bool passed = result->outcome_seen == BATTLE_CORE_OUTCOME_WON
        && result->battle_runtime_cleaned
        && read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) == 0U
        && read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S58E_CB2_OVERWORLD
        && read8(core, S58E_FIELD_LOCK) == 0U;
    s58e_restore_battle_script(core, script);
    return passed;
}

static bool s58e_normal_trainer_win(struct mCore *core,
                                     struct EndObservation *result)
{
    /* Keep the bootstrapped production party intact.  A synthetic party is
     * valid only for a direct unit call and must not be exposed to a field
     * frame before the normal trainerbattle script takes ownership. */
    if (read8(core, ADDR_PLAYER_PARTY_COUNT) == 0U)
        return false;
    if (getenv("MGBA_STAGE58_ECONOMY_BATTLE_TRACE") != NULL)
        fprintf(stderr, "trainer-party count=%u species=%" PRIu32
                " hp=%" PRIu32 " max=%" PRIu32 "\n",
                read8(core, ADDR_PLAYER_PARTY_COUNT),
                call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                                ADDR_PLAYER_PARTY, QOL_MON_DATA_SPECIES,
                                0U, 0U),
                call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                                ADDR_PLAYER_PARTY, QOL_MON_DATA_HP,
                                0U, 0U),
                call_preserving(core, BATTLE_CORE_GET_MON_DATA,
                                ADDR_PLAYER_PARTY, QOL_MON_DATA_MAX_HP,
                                0U, 0U));
    struct S58eBattleScript script = {0};
    return s58e_start_trainer_script(
               core, &script, true, S58E_NORMAL_TRAINER_ID, 0U)
        && s58e_finish_current_trainer_battle(core, &script, result);
}

static bool s58e_actual_trainer_chain(
    struct mCore *core, const struct QolSymbols *symbols,
    struct S58eEvidence *evidence)
{
    (void)symbols;
    uint32_t money = s58e_money_pointer(core);
    if (money == 0U)
        return false;
    (void)s58e_call_exact(
        core, S58E_SET_MONEY, money, S58E_TRAINER_MONEY_BEFORE, 0U, 0U);
    evidence->trainer_money_before = s58e_money(core);
    struct EndObservation battle = {0};
    bool battle_passed = s58e_normal_trainer_win(core, &battle);
    evidence->trainer_outcome = battle.outcome_seen;
    evidence->trainer_enemy_fainted = battle.enemy_fainted_seen;
    evidence->trainer_runtime_cleaned = battle.battle_runtime_cleaned;
    evidence->trainer_battlers_after = read8(core, ADDR_BATTLERS_COUNT);
    evidence->trainer_money_after = s58e_money(core);
    evidence->trainer_money_delta = evidence->trainer_money_after
        - evidence->trainer_money_before;
    bool earned = battle_passed
        && evidence->trainer_money_before == S58E_TRAINER_MONEY_BEFORE
        && battle.outcome_seen == BATTLE_CORE_OUTCOME_WON
        && battle.battle_runtime_cleaned
        && read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S58E_CB2_OVERWORLD
        && evidence->trainer_money_after == S58E_TRAINER_MONEY_AFTER
        && evidence->trainer_money_delta == S58E_TRAINER_PRIZE_EXPECTED;
    if (earned) {
        qol_set_badges_through(core, 1U);
        s58e_repair_wait_pc(core);
        run_key_frames(core, 0U, 4U);
    }
    bool progression = earned
        && read32(core, BATTLE_CORE_MAIN_CALLBACK2) == S58E_CB2_OVERWORLD
        && read8(core, S58E_FIELD_LOCK) == 0U;
    bool purchased = progression && s58e_actual_honey_purchase(core);
    evidence->trainer_money_after_purchase = s58e_money(core);
    uint64_t save_hash = 0U;
    evidence->trainer_earned_purchased_saved = purchased
        && evidence->trainer_money_after_purchase
            == S58E_TRAINER_MONEY_AFTER_HONEY
        && s58e_normal_menu_save(core, &save_hash)
        && save_hash != 0U;
    evidence->trainer_save_hash = save_hash;
    if (!evidence->trainer_earned_purchased_saved)
        fprintf(stderr, "trainer chain battle=%u outcome=%u clean=%u faint=%u"
                " money=%" PRIu32 "/%" PRIu32 "/%" PRIu32
                " progression=%u purchased=%u cb=%08" PRIx32
                " lock=%u battlers=%u honey=%u\n",
                battle_passed ? 1U : 0U, battle.outcome_seen,
                battle.battle_runtime_cleaned ? 1U : 0U,
                battle.enemy_fainted_seen ? 1U : 0U,
                evidence->trainer_money_before,
                evidence->trainer_money_after,
                evidence->trainer_money_after_purchase,
                progression ? 1U : 0U, purchased ? 1U : 0U,
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read8(core, S58E_FIELD_LOCK),
                read8(core, ADDR_BATTLERS_COUNT),
                s58e_item_count(core, S58E_HONEY_ITEM));
    return evidence->trainer_earned_purchased_saved;
}

static void s58e_disable_script_contexts(struct mCore *core)
{
    (void)call_preserving(
        core, S58E_SCRIPT_CONTEXT1_DISABLE, 0U, 0U, 0U, 0U);
}

static bool s58e_factory_battle_once(struct mCore *core,
                                     uint8_t *outcome_out,
                                     struct S58eEvidence *evidence)
{
    uint32_t factory = QOL_LEDGER + S58E_FACILITY_OFFSET;
    if (!s58e_scheduler_expect_r0(core, S58E_FACILITY_PREPARE, 0U, 1U)
        || read8(core, factory + S58E_FACILITY_MARKER_OFFSET)
            != S58E_FACILITY_MARKER_BATTLE
        || read16(core, BATTLE_CORE_TRAINER_OPPONENT_A) == 0U)
        return false;
    s58e_repair_wait_pc(core);
    struct CallObservation launch = call_bounded(
        core, BATTLE_CORE_START_TRAINER, 0U, 0U, 0U, 0U);
    bool started = false;
    for (unsigned frame = 0U; frame < 3600U; ++frame) {
        s58e_repair_wait_pc(core);
        run_key_frames(core, 0U, 1U);
        if (read8(core, ADDR_BATTLERS_COUNT) == 2U
            && read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0U) {
            started = true;
            break;
        }
    }
    if (!started || read8(core, ADDR_BATTLERS_COUNT) != 2U
        || read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) == 0U
        || (read32(core, ADDR_BATTLE_TYPE_FLAGS) & 0x0600010CU)
            != 0x06000108U
        || launch.instructions == 0U || !launch.payload_pc_seen) {
        fprintf(stderr, "factory battle start=%u payload=%u/%" PRIu32
                " battlers=%u newbs=%08" PRIx32
                " flags=%08" PRIx32 " cb=%08" PRIx32 " lock=%u\n",
                started ? 1U : 0U, launch.payload_pc_seen ? 1U : 0U,
                launch.instructions, read8(core, ADDR_BATTLERS_COUNT),
                read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER),
                read32(core, ADDR_BATTLE_TYPE_FLAGS),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read8(core, S58E_FIELD_LOCK));
        return false;
    }
    ++evidence->factory_payload_starts;
    /* Deterministic battle fixture only: the scheduler, move selection,
     * faint, outcome and teardown remain entirely owned by the ROM.  Battle
     * initialization can still copy the generated parties after newBS first
     * becomes non-NULL, so reassert only HP/speed before each ordinary input
     * pulse; no controller, outcome or reward field is host-authored. */
    for (unsigned slot = 0U; slot < 3U; ++slot) {
        write16(core, ADDR_ENEMY_PARTY + slot * POKEMON_SIZE
                          + POKEMON_CURRENT_HP_OFFSET, 1U);
        write16(core, ADDR_PLAYER_PARTY + slot * POKEMON_SIZE
                          + POKEMON_CURRENT_HP_OFFSET, 999U);
        write16(core, ADDR_PLAYER_PARTY + slot * POKEMON_SIZE
                          + S58E_PARTY_MAX_HP_OFFSET, 999U);
    }
    write16(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_HP, 999U);
    write16(core, ADDR_BATTLE_MONS + S58E_BATTLE_MON_MAX_HP_OFFSET, 999U);
    write16(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_SPEED, 999U);
    write16(core, ADDR_BATTLE_MONS + S58E_BATTLE_MON_MOVES_OFFSET,
            S58E_FACTORY_FIXTURE_MOVE);
    write8(core, ADDR_BATTLE_MONS + S58E_BATTLE_MON_PP_OFFSET, 35U);
    write16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                      + BATTLE_CORE_MON_HP, 1U);
    uint8_t outcome = 0U;
    bool initialized = true;
    for (unsigned pulse = 0U; pulse < 300U; ++pulse) {
        for (unsigned slot = 0U; slot < 3U; ++slot) {
            uint32_t enemy = ADDR_ENEMY_PARTY + slot * POKEMON_SIZE;
            uint32_t player = ADDR_PLAYER_PARTY + slot * POKEMON_SIZE;
            if (read16(core, enemy + POKEMON_CURRENT_HP_OFFSET) != 0U)
                write16(core, enemy + POKEMON_CURRENT_HP_OFFSET, 1U);
            if (read16(core, player + POKEMON_CURRENT_HP_OFFSET) != 0U)
                write16(core, player + POKEMON_CURRENT_HP_OFFSET, 999U);
            write16(core, ADDR_PLAYER_PARTY + slot * POKEMON_SIZE
                              + S58E_PARTY_MAX_HP_OFFSET, 999U);
        }
        if (read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) != 0U) {
            if (read16(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_HP) != 0U)
                write16(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_HP, 999U);
            write16(core, ADDR_BATTLE_MONS
                              + S58E_BATTLE_MON_MAX_HP_OFFSET, 999U);
            write16(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_SPEED, 999U);
            write16(core, ADDR_BATTLE_MONS
                              + S58E_BATTLE_MON_MOVES_OFFSET,
                    S58E_FACTORY_FIXTURE_MOVE);
            write8(core, ADDR_BATTLE_MONS + S58E_BATTLE_MON_PP_OFFSET, 35U);
            if (read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                                 + BATTLE_CORE_MON_HP) != 0U)
                write16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                                  + BATTLE_CORE_MON_HP, 1U);
        }
        write8(core, BATTLE_CORE_ACTION_SELECTION_CURSOR, 0U);
        write8(core, BATTLE_CORE_MOVE_SELECTION_CURSOR, 0U);
        if (read8(core, BATTLE_CORE_BATTLE_OUTCOME) != 0U)
            outcome = read8(core, BATTLE_CORE_BATTLE_OUTCOME);
        if (initialized
            && read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) == 0U
            && read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                == S58E_CB2_OVERWORLD) {
            run_key_frames(core, 0U, 180U);
            *outcome_out = outcome;
            return outcome == BATTLE_CORE_OUTCOME_WON
                && read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER) == 0U
                && read32(core, BATTLE_CORE_MAIN_CALLBACK2)
                    == S58E_CB2_OVERWORLD;
        }
        /* Decline only the optional SHIFT prompt for a living active mon. */
        if (read8(core, 0x02022B24U) == 22U
            && read16(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_HP) != 0U) {
            run_key_frames(core, QOL_KEY_B, 2U);
            run_key_frames(core, 0U, 30U);
        }
        run_key_frames(core, QOL_KEY_A, 2U);
        run_key_frames(core, 0U, BATTLE_CORE_MENU_INPUT_WAIT);
    }
    fprintf(stderr, "factory battle timeout outcome=%u live=%08" PRIx32
            " battlers=%u cb=%08" PRIx32 " lock=%u cmd=%u hp=%u/%u\n",
            outcome, read32(core, ADDR_NEW_BATTLE_STRUCT_POINTER),
            read8(core, ADDR_BATTLERS_COUNT),
            read32(core, BATTLE_CORE_MAIN_CALLBACK2),
            read8(core, S58E_FIELD_LOCK), read8(core, 0x02022B24U),
            read16(core, ADDR_BATTLE_MONS + BATTLE_CORE_MON_HP),
            read16(core, ADDR_BATTLE_MONS + BATTLE_MON_SIZE
                             + BATTLE_CORE_MON_HP));
    return false;
}

static bool s58e_actual_factory_chain(
    struct mCore *core, const struct QolSymbols *symbols,
    struct S58eEvidence *evidence)
{
    qol_set_badges_through(core, 7U);
    (void)call_preserving(core, QOL_FLAG_SET,
                          QOL_FLAG_DH_CLEAR, 0U, 0U, 0U);
    if (call_preserving(core, symbols->feature_unlocked,
                        S58E_ABILITY_PATCH_FEATURE,
                        0U, 0U, 0U) == 0U)
        return false;
    s58e_repair_wait_pc(core);
    run_key_frames(core, 0U, 4U);
    if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58E_CB2_OVERWORLD
        || read8(core, S58E_FIELD_LOCK) != 0U)
        return false;
    uint32_t factory = QOL_LEDGER + S58E_FACILITY_OFFSET;
    s58e_remove_all(core, S58E_ABILITY_PATCH_ITEM);
    s58e_set_bp(core, S58E_FACILITY_BP_BEFORE);
    evidence->factory_bp_before = read16(
        core, factory + S58E_FACILITY_BP_OFFSET);
    if (evidence->factory_bp_before != S58E_FACILITY_BP_BEFORE
        || !s58e_scheduler_expect_r0(core, S58E_FACILITY_ENTER, 0U, 1U)) {
        fprintf(stderr, "factory enter bp=%u\n", evidence->factory_bp_before);
        return false;
    }
    write8(core, S58E_FACILITY_SELECTED_ORDER + 0U, 1U);
    write8(core, S58E_FACILITY_SELECTED_ORDER + 1U, 2U);
    write8(core, S58E_FACILITY_SELECTED_ORDER + 2U, 3U);
    for (unsigned slot = 3U; slot < 6U; ++slot)
        write8(core, S58E_FACILITY_SELECTED_ORDER + slot, 0U);
    if (!s58e_scheduler_expect_r0(core, S58E_FACILITY_COMMIT, 0U, 1U)
        || read8(core, factory + S58E_FACILITY_MARKER_OFFSET)
            != S58E_FACILITY_MARKER_BATTLE
        || read8(core, ADDR_PLAYER_PARTY_COUNT) != 3U) {
        fprintf(stderr, "factory commit marker=%u party=%u\n",
                read8(core, factory + S58E_FACILITY_MARKER_OFFSET),
                read8(core, ADDR_PLAYER_PARTY_COUNT));
        return false;
    }
    for (unsigned round = 0U; round < 3U; ++round) {
        bool battle_ok = s58e_factory_battle_once(
            core, &evidence->factory_outcomes[round], evidence);
        bool after_ok = battle_ok && s58e_facility_direct_expect(
            core, S58E_FACILITY_AFTER, round == 2U ? 2U : 1U);
        uint8_t pending = read8(
            core, factory + S58E_FACILITY_REWARD_PENDING_OFFSET);
        if (!battle_ok || !after_ok || pending != round + 1U) {
            fprintf(stderr, "factory round=%u battle=%u after=%u outcome=%u"
                    " pending=%u cb=%08" PRIx32 " lock=%u\n",
                    round, battle_ok ? 1U : 0U, after_ok ? 1U : 0U,
                    evidence->factory_outcomes[round], pending,
                    read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                    read8(core, S58E_FIELD_LOCK));
            return false;
        }
        if (round != 2U
            && !s58e_facility_direct_expect(
                core, S58E_FACILITY_SKIP_EXCHANGE, 1U)) {
            fprintf(stderr, "factory skip round=%u result=%u pc=%08" PRIx32
                    " cb=%08" PRIx32 " lock=%u\n", round,
                    read16(core, S58E_SPECIAL_VAR_RESULT),
                    (uint32_t)read_register(core, "pc"),
                    read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                    read8(core, S58E_FIELD_LOCK));
            return false;
        }
    }
    if (!s58e_facility_direct_expect(
            core, S58E_FACILITY_COMPLETE,
            S58E_FACILITY_STATUS_COMPLETE))
        return false;
    evidence->factory_bp_after = read16(
        core, factory + S58E_FACILITY_BP_OFFSET);
    evidence->factory_bp_delta = evidence->factory_bp_after
        - evidence->factory_bp_before;
    bool earned = evidence->factory_outcomes[0] == BATTLE_CORE_OUTCOME_WON
        && evidence->factory_outcomes[1] == BATTLE_CORE_OUTCOME_WON
        && evidence->factory_outcomes[2] == BATTLE_CORE_OUTCOME_WON
        && evidence->factory_bp_delta == S58E_FACILITY_REWARD_BP
        && evidence->factory_bp_after == S58E_ABILITY_PATCH_PRICE;
    write16(core, S58E_SPECIAL_VAR_RESULT, UINT16_MAX);
    uint32_t purchase_result = earned
        ? call_preserving(core, S58E_BP_SHOP_PURCHASE_BY_INDEX,
                          S58E_ABILITY_PATCH_INDEX, 0U, 0U, 0U)
        : UINT32_MAX;
    bool purchased = earned && purchase_result == 0U
        && read16(core, S58E_SPECIAL_VAR_RESULT) == 0U;
    evidence->factory_purchase_raw_result = purchase_result;
    evidence->factory_purchase_special_result = read16(
        core, S58E_SPECIAL_VAR_RESULT);
    evidence->factory_bp_after_purchase = read16(
        core, factory + S58E_FACILITY_BP_OFFSET);
    uint64_t save_hash = 0U;
    evidence->factory_earned_purchased_saved = purchased
        && evidence->factory_bp_after_purchase == 0U
        && s58e_item_count(core, S58E_ABILITY_PATCH_ITEM) == 1U
        && s58e_normal_menu_save(core, &save_hash)
        && save_hash != 0U;
    evidence->factory_save_hash = save_hash;
    if (!evidence->factory_earned_purchased_saved)
        fprintf(stderr, "factory final earned=%u purchased=%u result=%" PRIu32
                " outcomes=%u/%u/%u bp=%u/%u/d%u/p%u patch=%u"
                " marker=%u pending=%u cb=%08" PRIx32 " lock=%u\n",
                earned ? 1U : 0U, purchased ? 1U : 0U, purchase_result,
                evidence->factory_outcomes[0], evidence->factory_outcomes[1],
                evidence->factory_outcomes[2], evidence->factory_bp_before,
                evidence->factory_bp_after, evidence->factory_bp_delta,
                evidence->factory_bp_after_purchase,
                s58e_item_count(core, S58E_ABILITY_PATCH_ITEM),
                read8(core, factory + S58E_FACILITY_MARKER_OFFSET),
                read8(core, factory + S58E_FACILITY_REWARD_PENDING_OFFSET),
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read8(core, S58E_FIELD_LOCK));
    return evidence->factory_earned_purchased_saved;
}

static bool s58e_reward_unlock_allowed(uint8_t unlock, bool post_kanto)
{
    return unlock == S58E_COLLECTION_UNLOCK_NONE
        || unlock == S58E_COLLECTION_UNLOCK_PRE_ENTRY
        || (post_kanto && unlock == S58E_COLLECTION_UNLOCK_KANTO_EARLY);
}

static uint16_t s58e_pick_low_reward(struct mCore *core, bool post_kanto,
                                     uint16_t random, uint32_t *total_out)
{
    uint32_t total = 0U;
    for (uint32_t index = 0U; index < S58E_COLLECTION_REWARD_COUNT; ++index) {
        uint32_t row = S58E_COLLECTION_REWARD_TABLE
            + index * S58E_COLLECTION_REWARD_STRIDE;
        if (read8(core, row + 4U) == 0U
            && s58e_reward_unlock_allowed(read8(core, row + 8U), post_kanto))
            total += read16(core, row + 2U);
    }
    *total_out = total;
    if (total == 0U)
        return UINT16_MAX;
    uint32_t pick = (uint32_t)random % total;
    for (uint32_t index = 0U; index < S58E_COLLECTION_REWARD_COUNT; ++index) {
        uint32_t row = S58E_COLLECTION_REWARD_TABLE
            + index * S58E_COLLECTION_REWARD_STRIDE;
        if (read8(core, row + 4U) != 0U
            || !s58e_reward_unlock_allowed(read8(core, row + 8U), post_kanto))
            continue;
        uint16_t weight = read16(core, row + 2U);
        if (pick < weight)
            return read16(core, row);
        pick -= weight;
    }
    return UINT16_MAX;
}

static bool s58e_low_raid_xs_rng(struct mCore *core,
                                 uint32_t *pre_hits, uint32_t *post_hits)
{
    uint32_t low_rows = 0U;
    uint32_t xs_rows = 0U;
    for (uint32_t index = 0U; index < S58E_COLLECTION_REWARD_COUNT; ++index) {
        uint32_t row = S58E_COLLECTION_REWARD_TABLE
            + index * S58E_COLLECTION_REWARD_STRIDE;
        if (read8(core, row + 4U) != 0U)
            continue;
        if (read8(core, row + 7U) != 0U)
            return false;
        ++low_rows;
        if (read16(core, row) == S58E_EXP_CANDY_XS_ITEM) {
            ++xs_rows;
            if (read16(core, row + 2U) != 90U
                || read8(core, row + 5U) != 1U
                || read8(core, row + 6U) != 2U
                || read8(core, row + 8U)
                    != S58E_COLLECTION_UNLOCK_KANTO_EARLY)
                return false;
        }
    }
    if (low_rows != 4U || xs_rows != 1U)
        return false;

    *pre_hits = 0U;
    *post_hits = 0U;
    uint32_t pre_total = 0U;
    uint32_t post_total = 0U;
    /* Exhaust the complete 16-bit output domain consumed by select_reward's
     * random16() % total ABI.  This is exact-table/RNG-output proof, not a
     * simulated field battle or a probabilistic sample. */
    for (uint32_t sample = 0U; sample < 65536U; ++sample) {
        uint16_t random = (uint16_t)sample;
        if (s58e_pick_low_reward(core, false, random, &pre_total)
                == S58E_EXP_CANDY_XS_ITEM)
            ++*pre_hits;
        if (s58e_pick_low_reward(core, true, random, &post_total)
                == S58E_EXP_CANDY_XS_ITEM)
            ++*post_hits;
    }
    return pre_total == 460U && post_total == 550U
        && *pre_hits == 0U && *post_hits != 0U;
}

static bool s58e_research_rate_71(struct mCore *core, uint16_t *count_out)
{
    *count_out = 0U;
    for (size_t index = 0U;
         index < sizeof(S58E_RESEARCH_REPRICES)
                     / sizeof(S58E_RESEARCH_REPRICES[0]);
         ++index) {
        const struct S58eResearchReprice *expected
            = &S58E_RESEARCH_REPRICES[index];
        uint32_t collection = S58E_COLLECTION_ITEM_TABLE
            + (uint32_t)expected->item * S58E_COLLECTION_ITEM_STRIDE;
        uint16_t item_price = read16(core, QOL_ITEM_TABLE
            + (uint32_t)expected->item * QOL_ITEM_ROW_SIZE
            + S58E_ITEM_PRICE_OFFSET);
        uint16_t sell = (uint16_t)((item_price / 2U)
            * read8(core, collection + S58E_COLLECTION_ITEM_QUANTITY_OFFSET));
        if (read16(core, collection) != expected->item
            || read8(core, collection + S58E_COLLECTION_ITEM_SOURCE_OFFSET)
                != S58E_COLLECTION_SOURCE_RESEARCH
            || read16(core, collection + S58E_COLLECTION_ITEM_PRICE_OFFSET)
                != expected->research_price
            || sell != expected->sell_money
            || (uint32_t)sell
                > (uint32_t)expected->research_price * 125U)
            return false;
        ++*count_out;
    }
    /* Also scan the whole ID-complete Collection table so an unlisted
     * Research row cannot retain a rate above the same ceiling. */
    for (uint32_t item = 0U; item < S58E_COLLECTION_ITEM_COUNT; ++item) {
        uint32_t collection = S58E_COLLECTION_ITEM_TABLE
            + item * S58E_COLLECTION_ITEM_STRIDE;
        if (read8(core, collection + S58E_COLLECTION_ITEM_SOURCE_OFFSET)
                != S58E_COLLECTION_SOURCE_RESEARCH)
            continue;
        uint16_t research = read16(
            core, collection + S58E_COLLECTION_ITEM_PRICE_OFFSET);
        uint32_t sell = (uint32_t)(read16(core, QOL_ITEM_TABLE
            + item * QOL_ITEM_ROW_SIZE + S58E_ITEM_PRICE_OFFSET) / 2U)
            * read8(core, collection + S58E_COLLECTION_ITEM_QUANTITY_OFFSET);
        if (research == 0U || sell > (uint32_t)research * 125U)
            return false;
    }
    return *count_out == 71U;
}

static bool s58e_collection_test_initialize(struct mCore *core)
{
    return call_preserving(core, S58E_COLLECTION_TEST_INITIALIZE,
                           0, 0, 0, 0) == S58E_COLLECTION_RESULT_SUCCESS;
}

static bool s58e_honey_no_profit(struct mCore *core)
{
    uint32_t collection = S58E_COLLECTION_ITEM_TABLE
        + S58E_HONEY_ITEM * S58E_COLLECTION_ITEM_STRIDE;
    uint16_t standard_price = read16(core, QOL_ITEM_TABLE
        + S58E_HONEY_ITEM * QOL_ITEM_ROW_SIZE + S58E_ITEM_PRICE_OFFSET);
    if (read16(core, collection) != S58E_HONEY_ITEM
        || read16(core, collection + S58E_COLLECTION_ITEM_PRICE_OFFSET)
            != S58E_HONEY_BUY_PRICE
        || read8(core, collection + S58E_COLLECTION_ITEM_QUANTITY_OFFSET)
            != 1U
        || read8(core, collection + S58E_COLLECTION_ITEM_SOURCE_OFFSET)
            != S58E_COLLECTION_SOURCE_MONEY
        || standard_price / 2U != S58E_HONEY_SELL_PRICE)
        return false;
    return S58E_HONEY_SELL_PRICE < S58E_HONEY_BUY_PRICE;
}

static bool s58e_purchase_honey_with_owner_api_money(struct mCore *core)
{
    unsigned ordinal = 0U;
    return s58e_honey_ordinal(core, &ordinal)
        && s58e_collection_honey_ui_purchase(
        core, S58E_MONEY_START, S58E_MONEY_AFTER_HONEY, ordinal);
}

static bool s58e_cancel_menu(struct mCore *core,
                             const struct QolSymbols *symbols)
{
    uint16_t before_bp = read16(
        core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP);
    uint16_t before_items = s58e_item_count(core, S58E_ABILITY_PATCH_ITEM);
    uint64_t before_ledger = s58e_hash(core, QOL_LEDGER, S58E_LEDGER_SIZE);
    uint16_t active_before = 0U;
    for (uint32_t index = 0U; index < 16U; ++index) {
        if (read8(core, QOL_TASKS + index * QOL_TASK_SIZE + 4U) != 0U)
            active_before |= (uint16_t)(1U << index);
    }
    if (call_preserving(core, symbols->open_supply_shop, 0, 0, 0, 0)
            != QOL_SUPPLY_RESULT_BUSY)
        return false;
    uint32_t task_id = 16U;
    uint32_t handler = 0U;
    for (uint32_t index = 0U; index < 16U; ++index) {
        uint32_t task = QOL_TASKS + index * QOL_TASK_SIZE;
        if ((active_before & (uint16_t)(1U << index)) == 0U
            && read8(core, task + 4U) != 0U
            && read8(core, task + 7U) == 0x50U) {
            task_id = index;
            handler = read32(core, task);
            break;
        }
    }
    if (task_id >= 16U || (handler & 1U) == 0U)
        return false;
    /* Execute the production task's real B/cancel branch without advancing a
     * field frame between host-side ABI calls.  Physical shop input is
     * covered independently by the Codex money-mart user-path smoke. */
    write16(core, S58E_MAIN_NEW_KEYS, QOL_KEY_B);
    (void)call_preserving(core, handler, task_id, 0, 0, 0);
    write16(core, S58E_MAIN_NEW_KEYS, 0U);
    return read16(core, S58E_SPECIAL_VAR_RESULT)
            == S58E_RESULT_MENU_CANCELLED
        && read16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP) == before_bp
        && s58e_item_count(core, S58E_ABILITY_PATCH_ITEM) == before_items
        && s58e_hash(core, QOL_LEDGER, S58E_LEDGER_SIZE) == before_ledger;
}

static bool s58e_transaction_boundaries(
    struct mCore *core, const struct QolSymbols *symbols,
    uint16_t *bag_capacity, struct S58eEvidence *evidence)
{
    struct Snapshot base = take_snapshot(core);

    evidence->normal_menu_cancel_no_mutation =
        s58e_cancel_menu(core, symbols);
    restore_snapshot(core, &base);

    s58e_remove_all(core, S58E_ABILITY_PATCH_ITEM);
    s58e_set_bp(core, S58E_BP_START);
    *bag_capacity = s58e_fill_stack(core, S58E_ABILITY_PATCH_ITEM);
    uint64_t full_ledger = s58e_hash(core, QOL_LEDGER, S58E_LEDGER_SIZE);
    uint16_t full_bp = read16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP);
    uint16_t full_count = s58e_item_count(core, S58E_ABILITY_PATCH_ITEM);
    evidence->bag_full_no_debit = call_preserving(
            core, symbols->purchase_supply,
            S58E_ABILITY_PATCH_INDEX, 0U, 0U, 0U) == QOL_STATUS_CAPACITY
        && full_count == *bag_capacity
        && read16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP) == full_bp
        && s58e_item_count(core, S58E_ABILITY_PATCH_ITEM) == full_count
        && s58e_hash(core, QOL_LEDGER, S58E_LEDGER_SIZE) == full_ledger;
    restore_snapshot(core, &base);

    s58e_remove_all(core, S58E_ABILITY_PATCH_ITEM);
    s58e_set_bp(core, S58E_ABILITY_PATCH_PRICE - 1U);
    uint64_t insufficient_ledger = s58e_hash(
        core, QOL_LEDGER, S58E_LEDGER_SIZE);
    evidence->insufficient_no_mutation = call_preserving(
            core, symbols->purchase_supply,
            S58E_ABILITY_PATCH_INDEX, 0U, 0U, 0U)
            == QOL_STATUS_INSUFFICIENT_CURRENCY
        && read16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP)
            == S58E_ABILITY_PATCH_PRICE - 1U
        && s58e_item_count(core, S58E_ABILITY_PATCH_ITEM) == 0U
        && s58e_hash(core, QOL_LEDGER, S58E_LEDGER_SIZE)
            == insufficient_ledger;
    restore_snapshot(core, &base);

    evidence->cross_store_fault_rollback = true;
    for (uint32_t mode = 1U; mode <= 2U; ++mode) {
        restore_snapshot(core, &base);
        s58e_remove_all(core, S58E_ABILITY_PATCH_ITEM);
        s58e_set_bp(core, S58E_BP_START);
        bool saved = s58e_bind_bag_pockets(core)
            && call_preserving(core, QOL_TRY_SAVING_DATA,
                               0U, 0U, 0U, 0U) == 1U;
        uint64_t before = s58e_hash(core, QOL_LEDGER, S58E_LEDGER_SIZE);
        bool mode_ok = saved
            && call_preserving(core, symbols->inject_persist_fault,
                               mode, 0U, 0U, 0U) == 1U
            && call_preserving(core, symbols->purchase_supply,
                               S58E_ABILITY_PATCH_INDEX, 0U, 0U, 0U)
                == QOL_STATUS_PERSIST_FAILED
            && read16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP)
                == S58E_BP_START
            && s58e_item_count(core, S58E_ABILITY_PATCH_ITEM) == 0U
            && s58e_hash(core, QOL_LEDGER, S58E_LEDGER_SIZE) == before;
        bool flash_ok = mode_ok
            && call_preserving(core, QOL_LOAD_GAME_DATA,
                               0U, 0U, 0U, 0U) == 1U
            && s58e_bind_bag_pockets(core)
            && read16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP)
                == S58E_BP_START
            && s58e_item_count(core, S58E_ABILITY_PATCH_ITEM) == 0U
            && s58e_hash(core, QOL_LEDGER, S58E_LEDGER_SIZE) == before;
        evidence->cross_store_fault_rollback =
            evidence->cross_store_fault_rollback && flash_ok;
    }
    restore_snapshot(core, &base);

    s58e_remove_all(core, S58E_ABILITY_PATCH_ITEM);
    s58e_set_bp(core, S58E_BP_START);
    bool first = call_preserving(
            core, symbols->purchase_supply,
            S58E_ABILITY_PATCH_INDEX, 0U, 0U, 0U) == QOL_STATUS_OK
        && read16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP)
            == S58E_BP_START - S58E_ABILITY_PATCH_PRICE
        && s58e_item_count(core, S58E_ABILITY_PATCH_ITEM) == 1U;
    bool same_session_limited = call_preserving(
            core, symbols->purchase_supply,
            S58E_ABILITY_PATCH_INDEX, 0U, 0U, 0U)
            == QOL_STATUS_ALREADY_CLAIMED
        && read16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP)
            == S58E_BP_START - S58E_ABILITY_PATCH_PRICE
        && s58e_item_count(core, S58E_ABILITY_PATCH_ITEM) == 1U;
    bool reopened = s58e_cancel_menu(core, symbols)
        && call_preserving(core, symbols->purchase_supply,
                           S58E_ABILITY_PATCH_INDEX, 0U, 0U, 0U)
            == QOL_STATUS_OK
        && read16(core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP)
            == S58E_BP_START - 2U * S58E_ABILITY_PATCH_PRICE
        && s58e_item_count(core, S58E_ABILITY_PATCH_ITEM) == 2U;
    evidence->limited_repeatable_reopen =
        first && same_session_limited && reopened;
    restore_snapshot(core, &base);

    evidence->currency_owner_api_integration =
        s58e_currency_owner_api_add(core);
    evidence->currency_owner_api_saved =
        evidence->currency_owner_api_integration;
    restore_snapshot(core, &base);
    free(base.bytes);

    bool passed = evidence->normal_menu_cancel_no_mutation
        && evidence->bag_full_no_debit
        && evidence->insufficient_no_mutation
        && evidence->cross_store_fault_rollback
        && evidence->limited_repeatable_reopen
        && evidence->currency_owner_api_integration;
    if (!passed)
        fprintf(stderr, "transaction boundaries cancel=%u full=%u"
                " insufficient=%u faults=%u limited=%u owner=%u cap=%u\n",
                evidence->normal_menu_cancel_no_mutation ? 1U : 0U,
                evidence->bag_full_no_debit ? 1U : 0U,
                evidence->insufficient_no_mutation ? 1U : 0U,
                evidence->cross_store_fault_rollback ? 1U : 0U,
                evidence->limited_repeatable_reopen ? 1U : 0U,
                evidence->currency_owner_api_integration ? 1U : 0U,
                *bag_capacity);
    return passed;
}

static bool s58e_collection_owner_47(
    struct mCore *core, const struct QolSymbols *symbols, uint16_t *count_out)
{
    *count_out = 0U;
    s58e_set_bp(core, 2000U);
    for (uint32_t index = 0U; index < S58E_QOL_SUPPLY_COUNT; ++index) {
        /* Bottle Cap and Gold Bottle Cap intentionally remain Collection
         * services.  Every other T19 catalog row is owned only by T19. */
        if (index == 42U || index == 43U)
            continue;
        uint32_t supply = S58E_QOL_SUPPLY_TABLE
            + index * S58E_QOL_SUPPLY_STRIDE;
        uint16_t item = read16(core, supply);
        uint32_t collection = S58E_COLLECTION_ITEM_TABLE
            + (uint32_t)item * S58E_COLLECTION_ITEM_STRIDE;
        uint32_t available = call_preserving(
            core, symbols->dispatch, QOL_SERVICE_SUPPLY_AVAILABLE,
            index, 0, 0);
        if (item >= S58E_COLLECTION_ITEM_COUNT
            || read16(core, collection) != item
            || read8(core, collection + S58E_COLLECTION_ITEM_SOURCE_OFFSET)
                != S58E_COLLECTION_SOURCE_EXISTING
            || available != QOL_STATUS_OK) {
            fprintf(stderr, "collection row=%" PRIu32 " item=%u"
                    " available=%" PRIu32 " source=%u\n",
                    index, item, available,
                    read8(core, collection
                                  + S58E_COLLECTION_ITEM_SOURCE_OFFSET));
            return false;
        }
        ++*count_out;
    }
    return *count_out == 47U;
}

static bool s58e_phase1(struct mCore *core,
                        const struct QolSymbols *symbols,
                        uint16_t *bag_capacity,
                        struct S58eEvidence *evidence)
{
    s58e_trace("field-trace");
    if (!qol_run_field_trace(core))
        return false;
    /* Start the production trainer path before any test progression owner is
     * called.  The catalog audit is isolated after the first normal save. */
    s58e_trace("actual-trainer");
    if (!s58e_actual_trainer_chain(core, symbols, evidence))
        return false;
    struct Snapshot e2e_base = take_snapshot(core);
    s58e_trace("static-feature-34");
    qol_set_badges_through(core, 7U);
    (void)call_preserving(core, QOL_FLAG_SET,
                          QOL_FLAG_DH_CLEAR, 0U, 0U, 0U);
    (void)call_preserving(core, QOL_FLAG_SET,
                          QOL_FLAG_HALL_OF_FAME, 0U, 0U, 0U);
    write8(core, QOL_LEDGER + QOL_LEDGER_KANTO_UNLOCKED, 1U);
    write8(core, QOL_LEDGER + QOL_LEDGER_KANTO_VISITED, 1U);
    write8(core, QOL_LEDGER + QOL_LEDGER_HALL_OF_FAME, 1U);
    write8(core, QOL_LEDGER + QOL_LEDGER_CERTIFICATIONS, 0x0FU);
    write8(core, QOL_LEDGER + QOL_LEDGER_LEAGUE_II, 1U);
    (void)call_preserving(core, QOL_SAVE_FINALIZE,
                          QOL_LEDGER, 0U, 0U, 0U);
    if (call_preserving(core, symbols->dispatch,
                        QOL_SERVICE_SET_DAYCARE_QUEST,
                        1U, 0U, 0U) != QOL_STATUS_OK) {
        fprintf(stderr, "progression daycare quest dispatch failed\n");
        return false;
    }
    uint32_t feature23 = call_preserving(
        core, symbols->feature_unlocked,
        S58E_ABILITY_PATCH_FEATURE, 0U, 0U, 0U);
    uint32_t feature34 = call_preserving(
        core, symbols->feature_unlocked, 34U, 0U, 0U, 0U);
    if (feature23 == 0U || feature34 == 0U) {
        fprintf(stderr, "progression feature23=%" PRIu32
                " feature34=%" PRIu32 " cb=%08" PRIx32
                " pc=%08" PRIx32 "\n", feature23, feature34,
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                (uint32_t)read_register(core, "pc"));
        return false;
    }
    s58e_trace("feature-gates-ready");
    s58e_repair_wait_pc(core);
    run_key_frames(core, 0U, 4U);
    if (read32(core, BATTLE_CORE_MAIN_CALLBACK2) != S58E_CB2_OVERWORLD
        || read8(core, S58E_FIELD_LOCK) != 0U) {
        fprintf(stderr, "progression settle cb=%08" PRIx32
                " lock=%u pc=%08" PRIx32 "\n",
                read32(core, BATTLE_CORE_MAIN_CALLBACK2),
                read8(core, S58E_FIELD_LOCK),
                (uint32_t)read_register(core, "pc"));
        return false;
    }
    s58e_trace("static-audits");
    evidence->low_raid_xs = s58e_low_raid_xs_rng(
        core, &evidence->low_pre_hits, &evidence->low_post_hits);
    evidence->research_rate_71 = s58e_research_rate_71(
        core, &evidence->research_count);
    evidence->honey_no_profit = s58e_honey_no_profit(core);
    if (read32(core, S58E_COLLECTION_OWNER) != S58E_COLLECTION_OWNER_MAGIC)
        return false;
    evidence->collection_owner_47 = s58e_collection_owner_47(
        core, symbols, &evidence->collection_owner_count);
    s58e_trace("transaction-boundaries");
    bool transaction_boundaries = evidence->collection_owner_47
        && s58e_transaction_boundaries(
            core, symbols, bag_capacity, evidence);
    s58e_trace("restore-e2e-base");
    restore_snapshot(core, &e2e_base);
    free(e2e_base.bytes);
    if (!evidence->low_raid_xs || !evidence->research_rate_71
        || !evidence->honey_no_profit || !evidence->collection_owner_47
        || !transaction_boundaries)
        return false;
    s58e_trace("actual-factory");
    return s58e_actual_factory_chain(core, symbols, evidence);
}

static bool s58e_reload(struct mCore *core,
                        const struct QolSymbols *symbols,
                        struct S58eEvidence *evidence)
{
    (void)symbols;
    run_key_frames(core, 0U, 180U);
    if (call_preserving(core, QOL_LOAD_GAME_DATA, 0, 0, 0, 0) != 1U)
        return false;
    /* The normal Continue path calls this after rotating save blocks.  A
     * direct test-only LoadGameData call must reproduce that volatile setup
     * before CheckBagItem or a subsequent purchase can observe the bag. */
    (void)call_preserving(core, S58E_SET_BAG_POCKETS_POINTERS, 0, 0, 0, 0);
    evidence->reload_money = s58e_money(core);
    evidence->reload_honey = s58e_item_count(core, S58E_HONEY_ITEM);
    evidence->reload_bp = read16(
        core, QOL_LEDGER + QOL_LEDGER_FACTORY_BP);
    evidence->reload_patch = s58e_item_count(
        core, S58E_ABILITY_PATCH_ITEM);
    evidence->trainer_fresh_reload =
        evidence->reload_money == S58E_TRAINER_MONEY_AFTER_HONEY
        && s58e_saved_item_count(core, S58E_HONEY_ITEM) == 1U
        && evidence->reload_honey == 1U;
    evidence->factory_fresh_reload = evidence->reload_bp == 0U
        && s58e_saved_item_count(core, S58E_ABILITY_PATCH_ITEM) == 1U
        && evidence->reload_patch == 1U;
    return evidence->trainer_fresh_reload && evidence->factory_fresh_reload;
}

#ifndef S58E_EMBEDDED
int main(int argc, char **argv)
{
    if (argc != 11) {
        fprintf(stderr,
                "usage: %s ROM SAVE EXPECTED_SHA phase1|reload PROBE "
                "DISPATCH FEATURE PURCHASE OPEN INJECT\n", argv[0]);
        return 2;
    }
    char digest[65];
    sha256_file(argv[1], digest);
    if (strlen(argv[3]) != 64U || strcmp(digest, argv[3]) != 0)
        s58e_die("ROM SHA-256 mismatch");
    bool phase1 = strcmp(argv[4], "phase1") == 0;
    if (!phase1 && strcmp(argv[4], "reload") != 0)
        return 2;
    struct QolSymbols symbols = {0};
    symbols.probe = qol_number(argv[5], "probe");
    symbols.dispatch = qol_number(argv[6], "dispatch");
    symbols.feature_unlocked = qol_number(argv[7], "feature");
    symbols.purchase_supply = qol_number(argv[8], "purchase");
    symbols.open_supply_shop = qol_number(argv[9], "open");
    symbols.inject_persist_fault = qol_number(argv[10], "inject");

    if (phase1)
        qol_initialize_save(argv[2]);
    struct mLogger logger = {.log = qol_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mCore *core = qol_open(argv[1], argv[2]);
    qol_log_core = core;
    uint16_t capacity = 0U;
    struct S58eEvidence evidence = {0};
    bool passed = phase1
        ? s58e_phase1(core, &symbols, &capacity, &evidence)
        : s58e_reload(core, &symbols, &evidence);
    bool warnings = log_problem_count == 0U;
    char test_json[2048];
    if (phase1) {
        (void)snprintf(
            test_json, sizeof(test_json),
            "\"normal_menu_cancel_no_mutation\":%s,"
            "\"bag_full_no_debit\":%s,"
            "\"insufficient_no_mutation\":%s,"
            "\"cross_store_fault_rollback\":%s,"
            "\"limited_repeatable_reopen\":%s,"
            "\"currency_owner_api_integration_boundary\":%s,"
            "\"low_raid_xs_unlock_runtime\":%s,"
            "\"collection_qol_owner_47_runtime\":%s,"
            "\"honey_buy_sell_no_profit_runtime\":%s,"
            "\"research_rate_71_runtime\":%s,"
            "\"normal_trainer_victory_prize_honey_normal_save_phase1\":%s,"
            "\"factory_prepare_real_battles_bp_patch_normal_save_phase1\":%s",
            evidence.normal_menu_cancel_no_mutation ? "true" : "false",
            evidence.bag_full_no_debit ? "true" : "false",
            evidence.insufficient_no_mutation ? "true" : "false",
            evidence.cross_store_fault_rollback ? "true" : "false",
            evidence.limited_repeatable_reopen ? "true" : "false",
            evidence.currency_owner_api_integration ? "true" : "false",
            evidence.low_raid_xs ? "true" : "false",
            evidence.collection_owner_47 ? "true" : "false",
            evidence.honey_no_profit ? "true" : "false",
            evidence.research_rate_71 ? "true" : "false",
            evidence.trainer_earned_purchased_saved ? "true" : "false",
            evidence.factory_earned_purchased_saved ? "true" : "false");
    } else {
        (void)snprintf(
            test_json, sizeof(test_json),
            "\"fresh_process_trainer_prize_honey_reload\":%s,"
            "\"fresh_process_factory_reward_ability_patch_reload\":%s",
            evidence.trainer_fresh_reload ? "true" : "false",
            evidence.factory_fresh_reload ? "true" : "false");
    }
    printf("{\"schema_version\":1,\"task\":"
           "\"USER-20260828-STAGE57-QOL-WORLD-CONVENIENCE-DEBUG\","
           "\"stage\":58,\"status\":\"%s\",\"phase\":\"%s\","
           "\"rom_sha256\":\"%s\",\"warnings_errors\":%u,"
           "\"tests\":{%s},"
           "\"test_routes\":{"
           "\"transaction_boundaries\":"
             "\"ISOLATED_SNAPSHOTS_INDIVIDUAL_RESULTS_AND_FLASH_ROLLBACK\","
           "\"low_raid_xs_unlock_runtime\":"
             "\"EXACT_ROM_REWARD_TABLE_EXHAUSTIVE_RNG_OUTPUT_ABI\","
           "\"collection_qol_owner_47_runtime\":"
             "\"EXACT_ROM_47_ROWS_SOURCE_AND_PRODUCTION_AVAILABILITY\","
           "\"honey_buy_sell_no_profit_runtime\":"
             "\"PHYSICAL_COLLECTION_BUY_UI_PLUS_STANDARD_SELL_PRICE_ABI\","
           "\"research_rate_71_runtime\":"
             "\"EXACT_ROM_COMPLETE_TABLE_RATE_ABI\","
           "\"normal_trainer_actual_earn\":"
             "\"AUTHORED_TYPE0_TRAINERBATTLE_NORMAL_INPUT_OUTCOME_AND_PRIZE\","
           "\"normal_trainer_fixture_scope\":"
             "\"AUTHORED_TRAINER89_SCRIPT_COPY_AND_ENEMY_HP1_NO_OUTCOME_"
             "OR_PRIZE_WRITE\","
           "\"factory_actual_earn\":"
             "\"VOID_SPECIALVAR_OWNER_ABI_PREPARE_STOCK_STARTTRAINER_"
             "THREE_CONTROLLER_WINS_COMPLETE_REWARD\","
           "\"factory_fixture_scope\":"
             "\"HOST_SELECTED_ORDER_HP_MAXHP_SPEED_MOVE_PP_ACTION_AND_MOVE_"
             "CURSORS_NO_OUTCOME_OR_REWARD_WRITE\","
           "\"ability_patch_purchase\":"
             "\"PRODUCTION_BPSHOP_PURCHASE_BY_INDEX_RAW_AND_SPECIAL_RESULT\"},"
           "\"e2e_boundaries\":{"
             "\"normal_trainer_victory_to_prize_honey_normal_save\":%s,"
             "\"factory_prepare_to_real_battle_to_bp_reward\":%s,"
             "\"factory_reward_to_patch_normal_save\":%s,"
             "\"fresh_process_earned_purchases_reload\":%s,"
             "\"factory_physical_npc_and_selection_ui\":false,"
             "\"factory_unmodified_battle_fixture\":false,"
             "\"low_raid_field_battle\":false,"
             "\"honey_sell_ui\":false,"
             "\"synthetic_currency_owner_api_is_actual_earn\":false},"
           "\"completion_claim\":"
             "\"%s\","
           "\"trainer_evidence\":{"
             "\"observed_in_phase1\":%s,"
             "\"trainer_id\":%u,\"script\":\"0x%08" PRIx32 "\","
             "\"money_before\":%" PRIu32 ",\"money_after\":%" PRIu32 ","
             "\"prize_delta\":%" PRIu32 ","
             "\"money_after_honey\":%" PRIu32 ","
             "\"outcome\":%u,\"enemy_fainted\":%s,"
             "\"runtime_cleaned\":%s,\"battlers_after_diagnostic\":%u,"
             "\"normal_save_hash\":\"0x%016" PRIx64 "\"},"
           "\"factory_evidence\":{"
             "\"observed_in_phase1\":%s,"
             "\"outcomes\":[%u,%u,%u],\"payload_starts\":%u,"
             "\"bp_before\":%u,\"bp_after_reward\":%u,"
             "\"bp_delta\":%u,\"bp_after_purchase\":%u,"
             "\"purchase_raw_result\":%" PRIu32 ","
             "\"purchase_special_result\":%u,"
             "\"normal_save_hash\":\"0x%016" PRIx64 "\"},"
           "\"reload_evidence\":{"
             "\"observed_in_fresh_process\":%s,"
             "\"money\":%" PRIu32 ",\"honey\":%u,"
             "\"bp\":%u,\"ability_patch\":%u},"
           "\"evidence_counts\":{"
             "\"phase1_transaction_boundaries_contract\":5,"
             "\"transaction_boundaries_observed_this_phase\":%u,"
             "\"low_pre_xs_hits\":%" PRIu32 ","
             "\"low_post_xs_hits\":%" PRIu32 ","
             "\"collection_owner_rows\":%u,"
             "\"research_reprice_rows\":%u},"
           "\"ability_patch\":{\"catalog_index\":35,\"item_id\":943,"
           "\"price_bp\":64,\"bag_capacity\":%u,"
           "\"bag_capacity_observed_phase1\":%u},"
           "\"process_contract\":\"fresh-core-two-phase\"}\n",
           passed && warnings ? "PASS" : "FAIL",
           phase1 ? "phase1" : "reload", digest, log_problem_count,
           test_json,
           (phase1 && evidence.trainer_earned_purchased_saved)
               ? "true" : "false",
           (phase1 && evidence.factory_earned_purchased_saved)
               ? "true" : "false",
           (phase1 && evidence.factory_earned_purchased_saved)
               ? "true" : "false",
           (!phase1 && evidence.trainer_fresh_reload
                    && evidence.factory_fresh_reload) ? "true" : "false",
           !passed || !warnings
               ? "INCOMPLETE_RUNTIME_GATE"
               : phase1
                   ? "ACTUAL_TRAINER_AND_FACTORY_EARN_PURCHASE_NORMAL_SAVE"
                   : "ACTUAL_TRAINER_AND_FACTORY_EARN_PURCHASE_NORMAL_SAVE_"
                     "FRESH_PROCESS_RELOAD",
           phase1 ? "true" : "false",
           S58E_NORMAL_TRAINER_ID, S58E_NORMAL_TRAINER_SOURCE,
           evidence.trainer_money_before, evidence.trainer_money_after,
           evidence.trainer_money_delta,
           evidence.trainer_money_after_purchase,
           evidence.trainer_outcome,
           evidence.trainer_enemy_fainted ? "true" : "false",
           evidence.trainer_runtime_cleaned ? "true" : "false",
           evidence.trainer_battlers_after, evidence.trainer_save_hash,
           phase1 ? "true" : "false",
           evidence.factory_outcomes[0], evidence.factory_outcomes[1],
           evidence.factory_outcomes[2], evidence.factory_payload_starts,
           evidence.factory_bp_before, evidence.factory_bp_after,
           evidence.factory_bp_delta, evidence.factory_bp_after_purchase,
           evidence.factory_purchase_raw_result,
           evidence.factory_purchase_special_result,
           evidence.factory_save_hash,
           phase1 ? "false" : "true",
           evidence.reload_money, evidence.reload_honey,
           evidence.reload_bp, evidence.reload_patch,
           phase1 ? 5U : 0U,
           evidence.low_pre_hits, evidence.low_post_hits,
           evidence.collection_owner_count, evidence.research_count,
           S58E_BAG_STACK_MAX, capacity);
    fflush(stdout);
    qol_close(core);
    return passed && warnings ? EXIT_SUCCESS : EXIT_FAILURE;
}
#endif
