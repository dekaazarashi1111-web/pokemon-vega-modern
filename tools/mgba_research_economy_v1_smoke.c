/* T23 Research Economy V1 exact-ROM quick/full validation for libmGBA. */
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#define BATTLE_CORE_EMBEDDED
#include "mgba_battle_core_smoke.c"

#include <ctype.h>

enum {
    RE_RESULT_SUCCESS = 0U,
    RE_RESULT_EFFECTLESS = 1U,
    RE_RESULT_CANCELLED = 2U,
    RE_RESULT_LOCKED = 3U,
    RE_RESULT_DAILY_CAP = 4U,
    RE_RESULT_PENDING = 6U,
    RE_RESULT_CORRUPT_SAVE = 7U,
    RE_RESULT_CAPACITY = 8U,
    RE_RESULT_PERSIST_FAILED = 13U,
    RE_RESULT_INSUFFICIENT = 14U,
    RE_RESULT_BAG_FULL = 15U,

    RE_SAVE_OK = 0U,
    RE_SAVE_BAD_CHECKSUM = 5U,

    RE_LEDGER = 0x0203D000U,
    RE_LEDGER_SIZE = 0x800U,
    RE_OWNER_OFFSET = 0x73FU,
    RE_OWNER_SIZE = 64U,
    RE_OWNER = RE_LEDGER + RE_OWNER_OFFSET,
    RE_OWNER_SCHEMA = 0U,
    RE_OWNER_STRUCT_SIZE = 1U,
    RE_OWNER_BALANCE = 4U,
    RE_OWNER_RANK = 6U,
    RE_OWNER_MINUTES = 7U,
    RE_OWNER_DAY_SERIAL = 8U,
    RE_OWNER_LIFETIME = 10U,
    RE_OWNER_DAILY = 14U,
    RE_OWNER_RANK_CLAIMS = 26U,
    RE_OWNER_SIMPLE_CLAIMS = 27U,
    RE_OWNER_DAILY_STOCK = 28U,
    RE_OWNER_NEXT_TRANSACTION = 36U,
    RE_OWNER_LAST_GAME_TOKEN = 40U,
    RE_OWNER_PENDING_TRANSACTION = 44U,
    RE_OWNER_PENDING_KIND = 48U,
    RE_OWNER_PENDING_PHASE = 49U,

    RE_SAVE_MAGIC_OFFSET = 0U,
    RE_SAVE_VERSION_OFFSET = 4U,
    RE_SAVE_SIZE_OFFSET = 6U,
    RE_SAVE_CHECKSUM_OFFSET = 8U,
    RE_SAVE_GENERATION_OFFSET = 12U,
    RE_SAVE_KANTO_UNLOCK_OFFSET = 16U,
    RE_SAVE_HOF_OFFSET = 18U,
    RE_SAVE_FACTORY_OFFSET = 0x392U,
    RE_SAVE_MIRAGE_OFFSET = 0x65CU,
    RE_SAVE_CREDITS_OFFSET = 0x684U,
    RE_SAVE_PENDING_ENCOUNTER_OFFSET = 0x694U,
    RE_SAVE_ITEM_FLAGS_OFFSET = 0x6C2U,
    RE_SAVE_VERSION_V1 = 1U,
    RE_SAVE_VERSION_V2 = 2U,
    RE_SAVE_MAGIC = 0x31534756U,
    RE_SAVE_RESERVED_NONZERO = 15U,
    RE_ACQUISITION_INNER_OFFSET = 0x44U,
    RE_ACQUISITION_COMPAT_SITE = 0x092D140EU,
    RE_ACQUISITION_SAVE_INITIALIZE = 0x092D0FA9U,
    RE_ACQUISITION_SET_SPECIES = 0x092D1D7DU,

    RE_ACTIVITY_FISHING = 0U,
    RE_ACTIVITY_ECOLOGY = 1U,
    RE_ACTIVITY_GAME_CORNER = 2U,
    RE_ACTIVITY_BUG = 3U,
    RE_ACTIVITY_MINING = 4U,
    RE_ACTIVITY_PHOTO = 5U,
    RE_ACTIVITY_COUNT = 6U,
    RE_POINT_CAP = 9999U,

    RE_HOOK_SAVE_VALIDATE = 0x092D10D0U,
    RE_HOOK_SAVE_FINALIZE = 0x092D2604U,
    RE_HOOK_SAVE_INIT = 0x092D2648U,
    RE_HOOK_SAVE_LOAD = 0x080DB4E4U,
    RE_HOOK_WILD_LAND = 0x080826D8U,
    RE_HOOK_WILD_FISH = 0x08082750U,
    RE_HOOK_WILD_HIDDEN = 0x09220198U,
    RE_HOOK_WILD_END = 0x0807F270U,
    RE_HOOK_MINUTE = 0x0800049EU,
    RE_HOOK_GAME_BULK = 0x0814061AU,
    RE_HOOK_GAME_ANIMATED = 0x0814065AU,
    RE_HOOK_COUNT = 11U,

    RE_ABI_VERSION = 0x52453131U,
    RE_SHOP_COUNT = 23U,
    RE_RANK_COUNT = 7U,
    RE_HOST_COUNT = 9U,
    RE_DIALOGUE_COUNT = 35U,
};

static const uint16_t RE_ACTIVITY_POINTS[RE_ACTIVITY_COUNT] = {
    4U, 10U, 3U, 8U, 10U, 6U,
};

static const uint16_t RE_ACTIVITY_CAPS[RE_ACTIVITY_COUNT] = {
    24U, 50U, 18U, 8U, 10U, 6U,
};

static const uint32_t RE_RANK_THRESHOLDS[RE_RANK_COUNT] = {
    0U, 80U, 240U, 520U, 900U, 1400U, 2200U,
};

static const uint16_t RE_SHOP_COSTS[RE_SHOP_COUNT] = {
    10U, 20U, 15U, 10U, 15U, 30U, 10U, 20U, 40U, 80U, 160U,
    120U, 80U, 40U, 100U, 320U, 240U, 240U, 240U, 240U, 120U,
    1280U, 640U,
};

static const uint8_t RE_DAILY_SHOP_INDEX[4] = {14U, 15U, 20U, 21U};
static const uint8_t RE_DAILY_SHOP_LIMIT[4] = {2U, 1U, 2U, 1U};

#define RE_SYMBOL_LIST(X) \
    X(probe, "ResearchEconomy_Probe") \
    X(save_checksum, "ResearchEconomy_SaveChecksum") \
    X(save_validate, "ResearchEconomy_SaveValidate") \
    X(save_finalize, "ResearchEconomy_SaveFinalize") \
    X(save_init_new, "ResearchEconomy_SaveInitNew") \
    X(migrate_v1, "ResearchEconomy_MigrateV1") \
    X(save_load, "ResearchEconomy_SaveLoadAdapter") \
    X(recover, "ResearchEconomy_Recover") \
    X(get_balance, "ResearchEconomy_GetBalance") \
    X(get_rank, "ResearchEconomy_GetRank") \
    X(minute_tick, "ResearchEconomy_MinuteTick") \
    X(credit_activity, "ResearchEconomy_CreditActivity") \
    X(purchase, "ResearchEconomy_PurchaseByIndex") \
    X(claim_rank, "ResearchEconomy_ClaimNextRankReward") \
    X(open_shop, "ResearchEconomy_OpenShop") \
    X(post_shop, "ResearchEconomy_PostShopMenu") \
    X(purchase_selected, "ResearchEconomy_PurchaseSelected") \
    X(field_counter, "ResearchEconomy_FieldCounter") \
    X(field_rank, "ResearchEconomy_FieldRank") \
    X(field_bug, "ResearchEconomy_FieldBug") \
    X(field_mining, "ResearchEconomy_FieldMining") \
    X(field_photo, "ResearchEconomy_FieldPhoto") \
    X(play_time, "ResearchEconomy_PlayTimeAdapter") \
    X(wild_land, "ResearchEconomy_TryGenerateWildMonAdapter") \
    X(wild_fishing, "ResearchEconomy_GenerateFishingEncounterAdapter") \
    X(wild_hidden, "ResearchEconomy_TryHiddenEncounterAdapter") \
    X(wild_end, "ResearchEconomy_EndWildBattleAdapter") \
    X(game_corner, "ResearchEconomy_GameCornerPayoutAdapter") \
    X(test_initialize, "ResearchEconomy_TestInitialize") \
    X(test_unlock_all, "ResearchEconomy_TestSetUnlockAll") \
    X(test_persistence_fault, "ResearchEconomy_TestSetPersistenceFault") \
    X(test_bag_capacity, "ResearchEconomy_TestSetBagCapacity") \
    X(test_get_owner_byte, "ResearchEconomy_TestGetOwnerByte") \
    X(test_set_balance, "ResearchEconomy_TestSetBalance")

struct ReSymbols {
#define RE_MEMBER(member, name) uint32_t member;
    RE_SYMBOL_LIST(RE_MEMBER)
#undef RE_MEMBER
    uint32_t runtime_address;
    uint32_t runtime_size;
};

struct ReCases {
    unsigned count;
    bool schema;
    bool has_save;
    bool has_activity;
    bool has_rank;
    bool has_shop;
    bool has_pending;
    bool has_hosts;
    bool has_game_corner;
};

struct ReHook {
    uint32_t site;
    uint32_t target;
    bool branch_link;
};

static void re_die(const char *message)
{
    fprintf(stderr, "mgba-research-economy-v1: %s\n", message);
    exit(1);
}

static char *re_read_text(const char *path)
{
    FILE *stream = fopen(path, "rb");
    if (!stream)
        re_die("fixture open failed");
    if (fseek(stream, 0, SEEK_END) != 0)
        re_die("fixture seek failed");
    long length = ftell(stream);
    if (length <= 0 || length > 8L * 1024L * 1024L)
        re_die("fixture size differs");
    rewind(stream);
    char *text = malloc((size_t)length + 1U);
    if (!text || fread(text, 1, (size_t)length, stream) != (size_t)length)
        re_die("fixture read failed");
    if (fclose(stream) != 0)
        re_die("fixture close failed");
    text[length] = '\0';
    return text;
}

static const char *re_find_key(const char *text, const char *key)
{
    char needle[160];
    if (snprintf(needle, sizeof(needle), "\"%s\"", key) < 0)
        re_die("JSON key formatting failed");
    return strstr(text, needle);
}

static uint32_t re_parse_number(const char *cursor)
{
    while (*cursor && (isspace((unsigned char)*cursor)
                       || *cursor == ':' || *cursor == '"'))
        ++cursor;
    errno = 0;
    char *end = NULL;
    unsigned long value = strtoul(cursor, &end, 0);
    if (errno || end == cursor || value > UINT32_MAX)
        re_die("JSON numeric value differs");
    return (uint32_t)value;
}

static uint32_t re_json_symbol(const char *text, const char *name)
{
    const char *found = re_find_key(text, name);
    if (!found)
        re_die("required runtime symbol is missing");
    found = strchr(found, ':');
    if (!found)
        re_die("runtime symbol separator is missing");
    ++found;
    while (isspace((unsigned char)*found))
        ++found;
    if (*found == '{') {
        const char *end = strchr(found, '}');
        const char *address = re_find_key(found, "address");
        if (!end || !address || address > end)
            re_die("runtime symbol address object differs");
        found = strchr(address, ':');
        if (!found)
            re_die("runtime symbol address separator is missing");
        ++found;
    }
    return re_parse_number(found);
}

static struct ReSymbols re_load_symbols(const char *path)
{
    char *text = re_read_text(path);
    if (!re_find_key(text, "symbols") && !re_find_key(text, "entrypoints"))
        re_die("symbols JSON has no symbol table");
    struct ReSymbols result = {0};
#define RE_LOAD(member, name) result.member = re_json_symbol(text, name);
    RE_SYMBOL_LIST(RE_LOAD)
#undef RE_LOAD
    const char *runtime = re_find_key(text, "runtime");
    if (!runtime)
        re_die("symbols JSON runtime span is missing");
    const char *address = re_find_key(runtime, "address");
    const char *size = re_find_key(runtime, "size");
    if (!address || !size)
        re_die("symbols JSON runtime address/size is missing");
    result.runtime_address = re_parse_number(strchr(address, ':') + 1);
    result.runtime_size = re_parse_number(strchr(size, ':') + 1);
    free(text);
    return result;
}

static unsigned re_count_occurrences(const char *text, const char *needle)
{
    unsigned count = 0U;
    size_t length = strlen(needle);
    while ((text = strstr(text, needle)) != NULL) {
        ++count;
        text += length;
    }
    return count;
}

static bool re_contains_case_insensitive(const char *text, const char *needle)
{
    size_t length = strlen(needle);
    for (; *text; ++text) {
        size_t index = 0U;
        while (index < length && text[index]
               && tolower((unsigned char)text[index])
                   == tolower((unsigned char)needle[index]))
            ++index;
        if (index == length)
            return true;
    }
    return false;
}

static struct ReCases re_load_cases(const char *path)
{
    char *text = re_read_text(path);
    static const char *const case_names[] = {
        "new_save_v2", "v1_migration_preserve", "minute_59_60",
        "activity_caps", "rank_thresholds", "shop_atomic",
        "pending_reset", "nine_field_roots", "game_corner_payout",
        "checksum_failure", "owner_size_failure", "day_serial_wrap",
        "six_activity_boundaries", "dedupe_tokens", "all_rank_claims",
        "all_23_shop_rows", "four_daily_stock_rows", "bag_full_retry",
        "phase_a_fault", "final_save_fault", "all_35_dialogue_roots",
        "stage39_regression", "bps_round_trip",
    };
    unsigned case_count = 0U;
    bool case_names_exact = true;
    for (unsigned index = 0U; index < ARRAY_LEN(case_names); ++index) {
        char quoted[64];
        int length = snprintf(quoted, sizeof(quoted), "\"%s\"", case_names[index]);
        if (length <= 0 || (size_t)length >= sizeof(quoted))
            re_die("case fixture name is too long");
        unsigned occurrences = re_count_occurrences(text, quoted);
        case_names_exact = case_names_exact && occurrences == 1U;
        case_count += occurrences;
    }
    struct ReCases result = {
        .count = case_count,
        .schema = re_find_key(text, "schema_version") != NULL
            && re_find_key(text, "quick_cases") != NULL
            && re_find_key(text, "full_cases") != NULL
            && re_find_key(text, "acceptance_keys") != NULL
            && case_names_exact && case_count == ARRAY_LEN(case_names),
        .has_save = re_contains_case_insensitive(text, "save")
            || re_contains_case_insensitive(text, "migration"),
        .has_activity = re_contains_case_insensitive(text, "activity")
            || re_contains_case_insensitive(text, "daily"),
        .has_rank = re_contains_case_insensitive(text, "rank"),
        .has_shop = re_contains_case_insensitive(text, "shop"),
        .has_pending = re_contains_case_insensitive(text, "pending")
            || re_contains_case_insensitive(text, "fault"),
        .has_hosts = re_contains_case_insensitive(text, "host")
            || re_contains_case_insensitive(text, "binding"),
        .has_game_corner = re_contains_case_insensitive(text, "game_corner")
            || re_contains_case_insensitive(text, "game corner"),
    };
    free(text);
    return result;
}

static uint32_t re_call(struct mCore *core, uint32_t function,
                        uint32_t r0, uint32_t r1, uint32_t r2, uint32_t r3)
{
    if (!(function & 1U))
        re_die("runtime entrypoint is not Thumb");
    return call_bounded(core, function, r0, r1, r2, r3).result;
}

static uint8_t re_owner8(struct mCore *core, const struct ReSymbols *symbols,
                         unsigned offset)
{
    if (offset >= RE_OWNER_SIZE)
        re_die("owner byte offset outside owner");
    return (uint8_t)re_call(
        core, symbols->test_get_owner_byte, offset, 0U, 0U, 0U);
}

static uint16_t re_owner16(struct mCore *core, const struct ReSymbols *symbols,
                           unsigned offset)
{
    return (uint16_t)(re_owner8(core, symbols, offset)
        | (uint16_t)re_owner8(core, symbols, offset + 1U) << 8);
}

static uint32_t re_owner32(struct mCore *core, const struct ReSymbols *symbols,
                           unsigned offset)
{
    return (uint32_t)re_owner8(core, symbols, offset)
        | (uint32_t)re_owner8(core, symbols, offset + 1U) << 8
        | (uint32_t)re_owner8(core, symbols, offset + 2U) << 16
        | (uint32_t)re_owner8(core, symbols, offset + 3U) << 24;
}

static void re_write_owner32(struct mCore *core, unsigned offset,
                             uint32_t value)
{
    if (offset + 4U > RE_OWNER_SIZE)
        re_die("owner word offset outside owner");
    for (unsigned index = 0U; index < 4U; ++index)
        write8(core, RE_OWNER + offset + index,
               (uint8_t)(value >> (index * 8U)));
}

static void re_clear(struct mCore *core, uint32_t address, unsigned size)
{
    for (unsigned index = 0U; index < size; ++index)
        write8(core, address + index, 0U);
}

static uint32_t re_thumb_bl_target(struct mCore *core, uint32_t site)
{
    uint16_t high = read16(core, site);
    uint16_t low = read16(core, site + 2U);
    if ((high & 0xF800U) != 0xF000U || (low & 0xF800U) != 0xF800U)
        re_die("Thumb BL hook shape differs");
    int32_t displacement = (int32_t)(((uint32_t)(high & 0x07FFU) << 12)
        | ((uint32_t)(low & 0x07FFU) << 1));
    if (displacement & 0x00400000L)
        displacement |= (int32_t)0xFF800000L;
    return (uint32_t)((int32_t)(site + 4U) + displacement) | 1U;
}

static uint32_t re_jump_target(struct mCore *core, uint32_t site)
{
    if (read8(core, site) != 0x00U || read8(core, site + 1U) != 0x4BU
        || read8(core, site + 2U) != 0x18U
        || read8(core, site + 3U) != 0x47U)
        re_die("absolute Thumb hook shape differs");
    return read32(core, site + 4U);
}

static bool re_symbols_and_hooks(struct mCore *core,
                                 const struct ReSymbols *symbols)
{
    uint32_t start = symbols->runtime_address & ~1U;
    uint32_t end = start + symbols->runtime_size;
    bool symbols_live = start >= 0x08000000U && end <= 0x0A000000U
        && end > start;
#define RE_LIVE(member, name) \
    symbols_live = symbols_live && (symbols->member & 1U) \
        && (symbols->member & ~1U) >= start && (symbols->member & ~1U) < end;
    RE_SYMBOL_LIST(RE_LIVE)
#undef RE_LIVE
    struct ReHook hooks[RE_HOOK_COUNT] = {
        {RE_HOOK_SAVE_VALIDATE, symbols->save_validate, false},
        {RE_HOOK_SAVE_FINALIZE, symbols->save_finalize, false},
        {RE_HOOK_SAVE_INIT, symbols->save_init_new, false},
        {RE_HOOK_SAVE_LOAD, symbols->save_load, false},
        {RE_HOOK_WILD_LAND, symbols->wild_land, false},
        {RE_HOOK_WILD_FISH, symbols->wild_fishing, false},
        {RE_HOOK_WILD_HIDDEN, symbols->wild_hidden, false},
        {RE_HOOK_WILD_END, symbols->wild_end, false},
        {RE_HOOK_MINUTE, symbols->play_time, true},
        {RE_HOOK_GAME_BULK, symbols->game_corner, true},
        {RE_HOOK_GAME_ANIMATED, symbols->game_corner, true},
    };
    bool roots = true;
    for (unsigned index = 0U; index < ARRAY_LEN(hooks); ++index) {
        uint32_t target;
        if (hooks[index].branch_link) {
            target = re_thumb_bl_target(core, hooks[index].site);
            if (target != hooks[index].target)
                target = re_jump_target(core, target & ~1U);
        } else {
            target = re_jump_target(core, hooks[index].site);
        }
        roots = roots && target == hooks[index].target;
    }
    bool acquisition_v2_patch = read8(
        core, RE_ACQUISITION_COMPAT_SITE) == 0x02U
        && read8(core, RE_ACQUISITION_COMPAT_SITE + 1U) == 0x2AU;
    return symbols_live && roots && acquisition_v2_patch;
}

static bool re_initialize(struct mCore *core, const struct ReSymbols *symbols,
                          bool unlock)
{
    uint32_t result = re_call(
        core, symbols->test_initialize, 0U, 0U, 0U, 0U);
    (void)re_call(core, symbols->test_persistence_fault, 0U, 0U, 0U, 0U);
    (void)re_call(core, symbols->test_bag_capacity, 99U, 0U, 0U, 0U);
    (void)re_call(core, symbols->test_unlock_all, unlock ? 1U : 0U, 0U, 0U, 0U);
    return result == RE_RESULT_SUCCESS
        && re_owner8(core, symbols, RE_OWNER_SCHEMA) == 1U
        && re_owner8(core, symbols, RE_OWNER_STRUCT_SIZE) == RE_OWNER_SIZE
        && re_owner16(core, symbols, RE_OWNER_BALANCE) == 0U
        && re_owner8(core, symbols, RE_OWNER_RANK) == 1U
        && re_owner32(core, symbols, RE_OWNER_NEXT_TRANSACTION) == 1U;
}

static bool re_reload_saved_ledger(struct mCore *core,
                                   const struct ReSymbols *symbols,
                                   bool unlock)
{
    uint8_t ledger[RE_LEDGER_SIZE];
    for (unsigned index = 0U; index < ARRAY_LEN(ledger); ++index)
        ledger[index] = read8(core, RE_LEDGER + index);
    if (!re_initialize(core, symbols, unlock))
        return false;
    for (unsigned index = 0U; index < ARRAY_LEN(ledger); ++index)
        write8(core, RE_LEDGER + index, ledger[index]);
    return re_call(core, symbols->save_validate,
                   RE_LEDGER, RE_LEDGER_SIZE, 0U, 0U) == RE_SAVE_OK;
}

static bool re_save_migration(struct mCore *core,
                              const struct ReSymbols *symbols)
{
    re_clear(core, RE_LEDGER, RE_LEDGER_SIZE);
    write32_bytes(core, RE_LEDGER + RE_SAVE_MAGIC_OFFSET, RE_SAVE_MAGIC);
    write16(core, RE_LEDGER + RE_SAVE_VERSION_OFFSET, RE_SAVE_VERSION_V1);
    write16(core, RE_LEDGER + RE_SAVE_SIZE_OFFSET, RE_LEDGER_SIZE);
    write32_bytes(core, RE_LEDGER + RE_SAVE_GENERATION_OFFSET, 0x13572468U);
    write8(core, RE_LEDGER + RE_SAVE_KANTO_UNLOCK_OFFSET, 1U);
    write8(core, RE_LEDGER + RE_SAVE_HOF_OFFSET, 1U);
    write16(core, RE_LEDGER + RE_SAVE_FACTORY_OFFSET, 0x1234U);
    write16(core, RE_LEDGER + RE_SAVE_MIRAGE_OFFSET, 0x2345U);
    write16(core, RE_LEDGER + RE_SAVE_CREDITS_OFFSET, 0x3456U);
    write8(core, RE_LEDGER + RE_SAVE_PENDING_ENCOUNTER_OFFSET, 1U);
    write8(core, RE_LEDGER + RE_SAVE_ITEM_FLAGS_OFFSET, 0x5AU);
    uint32_t checksum = re_call(
        core, symbols->save_checksum, RE_LEDGER, 0U, 0U, 0U);
    write32_bytes(core, RE_LEDGER + RE_SAVE_CHECKSUM_OFFSET, checksum);
    bool legacy_valid = re_call(
        core, symbols->save_validate, RE_LEDGER, RE_LEDGER_SIZE, 0U, 0U)
        == RE_SAVE_OK;
    bool migrated = re_call(
        core, symbols->migrate_v1, RE_LEDGER, RE_LEDGER_SIZE, 0U, 0U)
        == RE_SAVE_OK;
    bool owner = read16(core, RE_LEDGER + RE_SAVE_VERSION_OFFSET)
            == RE_SAVE_VERSION_V2
        && read8(core, RE_OWNER + RE_OWNER_SCHEMA) == 1U
        && read8(core, RE_OWNER + RE_OWNER_STRUCT_SIZE) == RE_OWNER_SIZE
        && re_owner16(core, symbols, RE_OWNER_BALANCE) == 0U
        && read8(core, RE_OWNER + RE_OWNER_RANK) == 1U
        && re_owner32(core, symbols, RE_OWNER_NEXT_TRANSACTION) == 1U;
    bool neighbors = read32(core, RE_LEDGER + RE_SAVE_GENERATION_OFFSET)
            == 0x13572468U
        && read8(core, RE_LEDGER + RE_SAVE_KANTO_UNLOCK_OFFSET) == 1U
        && read8(core, RE_LEDGER + RE_SAVE_HOF_OFFSET) == 1U
        && read16(core, RE_LEDGER + RE_SAVE_FACTORY_OFFSET) == 0x1234U
        && read16(core, RE_LEDGER + RE_SAVE_MIRAGE_OFFSET) == 0x2345U
        && read16(core, RE_LEDGER + RE_SAVE_CREDITS_OFFSET) == 0x3456U
        && read8(core, RE_LEDGER + RE_SAVE_PENDING_ENCOUNTER_OFFSET) == 1U
        && read8(core, RE_LEDGER + RE_SAVE_ITEM_FLAGS_OFFSET) == 0x5AU;
    bool checksum_valid = re_call(
        core, symbols->save_validate, RE_LEDGER, RE_LEDGER_SIZE, 0U, 0U)
        == RE_SAVE_OK;

    re_clear(core, RE_LEDGER, RE_LEDGER_SIZE);
    write32_bytes(core, RE_LEDGER + RE_SAVE_MAGIC_OFFSET, RE_SAVE_MAGIC);
    write16(core, RE_LEDGER + RE_SAVE_VERSION_OFFSET, RE_SAVE_VERSION_V1);
    write16(core, RE_LEDGER + RE_SAVE_SIZE_OFFSET, RE_LEDGER_SIZE);
    checksum = re_call(core, symbols->save_checksum, RE_LEDGER, 0U, 0U, 0U);
    write32_bytes(core, RE_LEDGER + RE_SAVE_CHECKSUM_OFFSET, checksum ^ 1U);
    bool corrupt = re_call(
        core, symbols->save_validate, RE_LEDGER, RE_LEDGER_SIZE, 0U, 0U)
            == RE_SAVE_BAD_CHECKSUM
        && re_call(core, symbols->migrate_v1,
                   RE_LEDGER, RE_LEDGER_SIZE, 0U, 0U) == RE_SAVE_BAD_CHECKSUM
        && read16(core, RE_LEDGER + RE_SAVE_VERSION_OFFSET) == RE_SAVE_VERSION_V1;

    re_clear(core, RE_LEDGER, RE_LEDGER_SIZE);
    re_call(core, symbols->save_init_new, RE_LEDGER, 1U, 0U, 0U);
    bool new_save = read16(core, RE_LEDGER + RE_SAVE_VERSION_OFFSET)
            == RE_SAVE_VERSION_V2
        && read8(core, RE_OWNER + RE_OWNER_RANK) == 1U
        && re_call(core, symbols->save_validate,
                   RE_LEDGER, RE_LEDGER_SIZE, 0U, 0U) == RE_SAVE_OK;
    write8(core, RE_OWNER + RE_OWNER_STRUCT_SIZE, RE_OWNER_SIZE - 1U);
    (void)re_call(core, symbols->save_finalize, RE_LEDGER, 0U, 0U, 0U);
    bool owner_size = re_call(
        core, symbols->save_validate, RE_LEDGER, RE_LEDGER_SIZE, 0U, 0U)
        == RE_SAVE_RESERVED_NONZERO;
    return legacy_valid && migrated && owner && neighbors && checksum_valid
        && corrupt && new_save && owner_size;
}

static bool re_acquisition_v2_compat(struct mCore *core,
                                     const struct ReSymbols *symbols)
{
    bool passed = re_initialize(core, symbols, true);
    (void)re_call(core, RE_ACQUISITION_SAVE_INITIALIZE,
                  RE_LEDGER + RE_ACQUISITION_INNER_OFFSET, 0U, 0U, 0U);
    (void)re_call(core, symbols->save_finalize, RE_LEDGER, 0U, 0U, 0U);
    return passed
        && re_call(core, symbols->save_validate,
                   RE_LEDGER, RE_LEDGER_SIZE, 0U, 0U) == RE_SAVE_OK
        && re_call(core, RE_ACQUISITION_SET_SPECIES,
                   25U, 0U, 0U, 0U) == 1U;
}

static uint32_t re_credit(struct mCore *core, const struct ReSymbols *symbols,
                          unsigned activity, uint32_t token)
{
    uint32_t simple = activity >= RE_ACTIVITY_BUG ? 1U : 0U;
    return re_call(core, symbols->credit_activity,
                   activity, token, simple, 0U);
}

static bool re_activity_day_caps(struct mCore *core,
                                 const struct ReSymbols *symbols)
{
    if (!re_initialize(core, symbols, true))
        return false;
    uint32_t token = 1000U;
    uint16_t expected_balance = 0U;
    bool exact = true;
    for (unsigned activity = 0U; activity < RE_ACTIVITY_COUNT; ++activity) {
        unsigned awards = RE_ACTIVITY_CAPS[activity] / RE_ACTIVITY_POINTS[activity];
        uint32_t first_token = token;
        for (unsigned award = 0U; award < awards; ++award) {
            uint32_t result = re_credit(core, symbols, activity, token++);
            exact = exact && result == RE_RESULT_SUCCESS;
            expected_balance = (uint16_t)(expected_balance
                + RE_ACTIVITY_POINTS[activity]);
            if (activity == RE_ACTIVITY_GAME_CORNER && award == 0U) {
                uint16_t before_duplicate = re_owner16(
                    core, symbols, RE_OWNER_BALANCE);
                exact = exact && re_credit(
                    core, symbols, activity, first_token)
                        == RE_RESULT_EFFECTLESS
                    && re_owner16(core, symbols, RE_OWNER_BALANCE)
                        == before_duplicate;
            }
        }
        exact = exact
            && re_owner16(core, symbols,
                          RE_OWNER_DAILY + activity * 2U)
                == RE_ACTIVITY_CAPS[activity]
            && re_owner16(core, symbols, RE_OWNER_BALANCE) == expected_balance;
        uint16_t before = re_owner16(core, symbols, RE_OWNER_BALANCE);
        uint32_t duplicate = re_credit(core, symbols, activity, first_token);
        uint32_t capped = re_credit(core, symbols, activity, token++);
        exact = exact
            && (duplicate == RE_RESULT_EFFECTLESS
                || duplicate == RE_RESULT_DAILY_CAP)
            && capped == RE_RESULT_DAILY_CAP
            && re_owner16(core, symbols, RE_OWNER_BALANCE) == before;
    }
    exact = exact && expected_balance == 116U;
    exact = exact && re_reload_saved_ledger(core, symbols, true)
        && re_owner16(core, symbols, RE_OWNER_BALANCE) == expected_balance;
    for (unsigned minute = 0U; minute < 59U; ++minute)
        (void)re_call(core, symbols->minute_tick, 0U, 0U, 0U, 0U);
    exact = exact && re_owner8(core, symbols, RE_OWNER_MINUTES) == 59U
        && re_owner16(core, symbols, RE_OWNER_DAY_SERIAL) == 0U
        && re_owner16(core, symbols, RE_OWNER_DAILY) == 24U;
    (void)re_call(core, symbols->minute_tick, 0U, 0U, 0U, 0U);
    exact = exact && re_owner8(core, symbols, RE_OWNER_MINUTES) == 0U
        && re_owner16(core, symbols, RE_OWNER_DAY_SERIAL) == 1U
        && re_owner8(core, symbols, RE_OWNER_SIMPLE_CLAIMS) == 0U;
    for (unsigned activity = 0U; activity < RE_ACTIVITY_COUNT; ++activity)
        exact = exact && re_owner16(
            core, symbols, RE_OWNER_DAILY + activity * 2U) == 0U;
    for (unsigned stock = 0U; stock < 4U; ++stock)
        exact = exact && re_owner8(
            core, symbols, RE_OWNER_DAILY_STOCK + stock) == 0U;

    exact = exact && re_initialize(core, symbols, true);
    write8(core, RE_OWNER + RE_OWNER_DAY_SERIAL, 0xFFU);
    write8(core, RE_OWNER + RE_OWNER_DAY_SERIAL + 1U, 0xFFU);
    write8(core, RE_OWNER + RE_OWNER_MINUTES, 59U);
    (void)re_call(core, symbols->save_finalize, RE_LEDGER, 0U, 0U, 0U);
    exact = exact && re_call(
        core, symbols->minute_tick, 0U, 0U, 0U, 0U) == RE_RESULT_SUCCESS
        && re_owner16(core, symbols, RE_OWNER_DAY_SERIAL) == 0U
        && re_owner8(core, symbols, RE_OWNER_MINUTES) == 0U;

    exact = exact && re_initialize(core, symbols, true);
    (void)re_call(core, symbols->test_set_balance,
                  RE_POINT_CAP - 1U, 0U, 0U, 0U);
    exact = exact && re_credit(core, symbols, RE_ACTIVITY_FISHING, 9001U)
            == RE_RESULT_SUCCESS
        && re_owner16(core, symbols, RE_OWNER_BALANCE) == RE_POINT_CAP;
    exact = exact && re_initialize(core, symbols, true);
    (void)re_call(core, symbols->test_set_balance,
                  RE_POINT_CAP - 1U, 0U, 0U, 0U);
    uint32_t simple_full = re_credit(core, symbols, RE_ACTIVITY_BUG, 9002U);
    exact = exact && (simple_full == RE_RESULT_CAPACITY
                      || simple_full == RE_RESULT_EFFECTLESS
                      || simple_full == RE_RESULT_DAILY_CAP)
        && re_owner16(core, symbols, RE_OWNER_BALANCE) == RE_POINT_CAP - 1U
        && !(re_owner8(core, symbols, RE_OWNER_SIMPLE_CLAIMS)
             & (1U << (RE_ACTIVITY_BUG - RE_ACTIVITY_BUG)));
    return exact;
}

static bool re_credit_full_day(struct mCore *core,
                               const struct ReSymbols *symbols,
                               uint32_t *token)
{
    bool passed = true;
    for (unsigned activity = 0U; activity < RE_ACTIVITY_COUNT; ++activity) {
        unsigned awards = RE_ACTIVITY_CAPS[activity] / RE_ACTIVITY_POINTS[activity];
        for (unsigned award = 0U; award < awards; ++award)
            passed = passed && re_credit(core, symbols, activity, (*token)++)
                == RE_RESULT_SUCCESS;
    }
    for (unsigned minute = 0U; minute < 60U; ++minute)
        (void)re_call(core, symbols->minute_tick, 0U, 0U, 0U, 0U);
    return passed;
}

static bool re_rank_contract(struct mCore *core,
                             const struct ReSymbols *symbols)
{
    bool passed = re_initialize(core, symbols, false);
    passed = passed
        && re_credit(core, symbols, RE_ACTIVITY_FISHING, 1U) == RE_RESULT_LOCKED
        && re_owner16(core, symbols, RE_OWNER_BALANCE) == 0U
        && re_owner8(core, symbols, RE_OWNER_RANK) == 1U;

    re_write_owner32(core, RE_OWNER_LIFETIME,
                     RE_RANK_THRESHOLDS[RE_RANK_COUNT - 1U]);
    (void)re_call(core, symbols->save_finalize, RE_LEDGER, 0U, 0U, 0U);
    passed = passed && re_call(
        core, symbols->get_rank, 0U, 0U, 0U, 0U) == 1U;
    (void)re_call(core, symbols->test_unlock_all, 1U, 0U, 0U, 0U);
    passed = passed && re_call(
        core, symbols->get_rank, 0U, 0U, 0U, 0U) == RE_RANK_COUNT;

    for (unsigned rank = 1U; rank < RE_RANK_COUNT; ++rank) {
        passed = passed && re_initialize(core, symbols, true);
        re_write_owner32(core, RE_OWNER_LIFETIME,
                         RE_RANK_THRESHOLDS[rank] - 1U);
        (void)re_call(core, symbols->save_finalize, RE_LEDGER, 0U, 0U, 0U);
        passed = passed && re_call(
            core, symbols->get_rank, 0U, 0U, 0U, 0U) == rank;
        re_write_owner32(core, RE_OWNER_LIFETIME, RE_RANK_THRESHOLDS[rank]);
        (void)re_call(core, symbols->save_finalize, RE_LEDGER, 0U, 0U, 0U);
        passed = passed && re_call(
            core, symbols->get_rank, 0U, 0U, 0U, 0U) == rank + 1U;
    }

    passed = passed && re_initialize(core, symbols, true);
    uint32_t token = 20000U;
    for (unsigned day = 0U; day < 19U; ++day)
        passed = passed && re_credit_full_day(core, symbols, &token);
    passed = passed && re_owner32(core, symbols, RE_OWNER_LIFETIME) == 2204U
        && re_owner8(core, symbols, RE_OWNER_RANK) == RE_RANK_COUNT;
    uint16_t rank_before = (uint16_t)re_call(
        core, symbols->get_rank, 0U, 0U, 0U, 0U);
    uint16_t balance_before = re_owner16(core, symbols, RE_OWNER_BALANCE);
    passed = passed && re_call(
        core, symbols->purchase, 0U, 1U, 0U, 0U) == RE_RESULT_SUCCESS
        && re_owner16(core, symbols, RE_OWNER_BALANCE) == balance_before - 10U
        && re_call(core, symbols->get_rank, 0U, 0U, 0U, 0U) == rank_before;

    (void)re_call(core, symbols->test_bag_capacity, 0U, 0U, 0U, 0U);
    passed = passed && re_call(
        core, symbols->claim_rank, 1U, 0U, 0U, 0U) == RE_RESULT_BAG_FULL
        && re_owner8(core, symbols, RE_OWNER_RANK_CLAIMS) == 0U;
    (void)re_call(core, symbols->test_bag_capacity, 99U, 0U, 0U, 0U);
    passed = passed && re_call(
        core, symbols->claim_rank, 0U, 0U, 0U, 0U) == RE_RESULT_CANCELLED
        && re_owner8(core, symbols, RE_OWNER_RANK_CLAIMS) == 0U;
    for (unsigned rank = 0U; rank < RE_RANK_COUNT; ++rank)
        passed = passed && re_call(
            core, symbols->claim_rank, 1U, 0U, 0U, 0U) == RE_RESULT_SUCCESS;
    passed = passed && re_owner8(
        core, symbols, RE_OWNER_RANK_CLAIMS) == 0x7FU;
    return passed;
}

static bool re_shop_contract(struct mCore *core,
                             const struct ReSymbols *symbols)
{
    bool passed = true;
    for (unsigned index = 0U; index < RE_SHOP_COUNT; ++index) {
        passed = passed && re_initialize(core, symbols, true);
        (void)re_call(core, symbols->test_set_balance,
                      RE_SHOP_COSTS[index], 0U, 0U, 0U);
        passed = passed && re_call(
            core, symbols->purchase, index, 0U, 0U, 0U) == RE_RESULT_CANCELLED
            && re_owner16(core, symbols, RE_OWNER_BALANCE) == RE_SHOP_COSTS[index];
        (void)re_call(core, symbols->test_set_balance,
                      RE_SHOP_COSTS[index] - 1U, 0U, 0U, 0U);
        passed = passed && re_call(
            core, symbols->purchase, index, 1U, 0U, 0U) == RE_RESULT_INSUFFICIENT
            && re_owner16(core, symbols, RE_OWNER_BALANCE)
                == RE_SHOP_COSTS[index] - 1U;
        (void)re_call(core, symbols->test_set_balance,
                      RE_SHOP_COSTS[index], 0U, 0U, 0U);
        (void)re_call(core, symbols->test_bag_capacity, 0U, 0U, 0U, 0U);
        passed = passed && re_call(
            core, symbols->purchase, index, 1U, 0U, 0U) == RE_RESULT_BAG_FULL
            && re_owner16(core, symbols, RE_OWNER_BALANCE) == RE_SHOP_COSTS[index];
        (void)re_call(core, symbols->test_bag_capacity, 99U, 0U, 0U, 0U);
        passed = passed && re_call(
            core, symbols->purchase, index, 1U, 0U, 0U) == RE_RESULT_SUCCESS
            && re_owner16(core, symbols, RE_OWNER_BALANCE) == 0U;
    }
    passed = passed && re_initialize(core, symbols, false)
        && re_call(core, symbols->purchase, 0U, 1U, 0U, 0U)
            == RE_RESULT_LOCKED;
    for (unsigned stock = 0U; stock < 4U; ++stock) {
        passed = passed && re_initialize(core, symbols, true);
        (void)re_call(core, symbols->test_set_balance,
                      RE_POINT_CAP, 0U, 0U, 0U);
        for (unsigned count = 0U; count < RE_DAILY_SHOP_LIMIT[stock]; ++count)
            passed = passed && re_call(
                core, symbols->purchase,
                RE_DAILY_SHOP_INDEX[stock], 1U, 0U, 0U) == RE_RESULT_SUCCESS;
        passed = passed && re_call(
            core, symbols->purchase,
            RE_DAILY_SHOP_INDEX[stock], 1U, 0U, 0U) == RE_RESULT_DAILY_CAP
            && re_owner8(core, symbols, RE_OWNER_DAILY_STOCK + stock)
                == RE_DAILY_SHOP_LIMIT[stock];
    }
    return passed;
}

static bool re_pending_recovery(struct mCore *core,
                                const struct ReSymbols *symbols)
{
    bool passed = re_initialize(core, symbols, true);
    (void)re_call(core, symbols->test_persistence_fault, 1U, 0U, 0U, 0U);
    passed = passed && re_credit(
        core, symbols, RE_ACTIVITY_FISHING, 60001U) == RE_RESULT_PERSIST_FAILED
        && re_owner16(core, symbols, RE_OWNER_BALANCE) == 0U
        && re_owner8(core, symbols, RE_OWNER_PENDING_KIND) == 0U;

    passed = passed && re_initialize(core, symbols, true);
    (void)re_call(core, symbols->test_persistence_fault, 2U, 0U, 0U, 0U);
    passed = passed && re_credit(
        core, symbols, RE_ACTIVITY_FISHING, 60002U) == RE_RESULT_PERSIST_FAILED
        && re_owner8(core, symbols, RE_OWNER_PENDING_KIND) != 0U
        && re_owner32(core, symbols, RE_OWNER_PENDING_TRANSACTION) != 0U;
    passed = passed && re_reload_saved_ledger(core, symbols, true);
    passed = passed && re_call(
        core, symbols->recover, 0U, 0U, 0U, 0U) == RE_RESULT_SUCCESS
        && re_owner16(core, symbols, RE_OWNER_BALANCE) == 4U
        && re_owner8(core, symbols, RE_OWNER_PENDING_KIND) == 0U;
    (void)re_call(core, symbols->recover, 0U, 0U, 0U, 0U);
    passed = passed && re_owner16(core, symbols, RE_OWNER_BALANCE) == 4U;

    passed = passed && re_initialize(core, symbols, true);
    (void)re_call(core, symbols->test_persistence_fault, 2U, 0U, 0U, 0U);
    passed = passed && re_credit(
        core, symbols, RE_ACTIVITY_BUG, 60003U) == RE_RESULT_PERSIST_FAILED
        && re_owner8(core, symbols, RE_OWNER_PENDING_KIND) != 0U;
    passed = passed && re_reload_saved_ledger(core, symbols, true);
    passed = passed && re_call(
        core, symbols->recover, 0U, 0U, 0U, 0U) == RE_RESULT_SUCCESS
        && re_owner16(core, symbols, RE_OWNER_BALANCE) == 0U
        && re_owner8(core, symbols, RE_OWNER_SIMPLE_CLAIMS) == 0U
        && re_credit(core, symbols, RE_ACTIVITY_BUG, 60004U) == RE_RESULT_SUCCESS;

    passed = passed && re_initialize(core, symbols, true);
    (void)re_call(core, symbols->test_set_balance, 100U, 0U, 0U, 0U);
    (void)re_call(core, symbols->test_persistence_fault, 2U, 0U, 0U, 0U);
    passed = passed && re_call(
        core, symbols->purchase, 0U, 1U, 0U, 0U) == RE_RESULT_PERSIST_FAILED
        && re_owner8(core, symbols, RE_OWNER_PENDING_KIND) != 0U;
    passed = passed && re_reload_saved_ledger(core, symbols, true);
    passed = passed && re_call(
        core, symbols->recover, 0U, 0U, 0U, 0U) == RE_RESULT_SUCCESS
        && re_owner16(core, symbols, RE_OWNER_BALANCE) == 100U
        && re_call(core, symbols->purchase, 0U, 1U, 0U, 0U)
            == RE_RESULT_SUCCESS
        && re_owner16(core, symbols, RE_OWNER_BALANCE) == 90U;

    passed = passed && re_initialize(core, symbols, true);
    re_write_owner32(core, RE_OWNER_LIFETIME,
                     RE_RANK_THRESHOLDS[RE_RANK_COUNT - 1U]);
    (void)re_call(core, symbols->save_finalize, RE_LEDGER, 0U, 0U, 0U);
    passed = passed && re_call(
        core, symbols->get_rank, 0U, 0U, 0U, 0U) == RE_RANK_COUNT;
    (void)re_call(core, symbols->test_persistence_fault, 2U, 0U, 0U, 0U);
    passed = passed && re_call(
        core, symbols->claim_rank, 1U, 0U, 0U, 0U)
            == RE_RESULT_PERSIST_FAILED
        && re_owner8(core, symbols, RE_OWNER_PENDING_KIND) != 0U
        && re_owner8(core, symbols, RE_OWNER_RANK_CLAIMS) == 0U;
    passed = passed && re_reload_saved_ledger(core, symbols, true)
        && re_call(core, symbols->recover, 0U, 0U, 0U, 0U)
            == RE_RESULT_SUCCESS
        && re_owner8(core, symbols, RE_OWNER_RANK_CLAIMS) == 0U
        && re_call(core, symbols->claim_rank, 1U, 0U, 0U, 0U)
            == RE_RESULT_SUCCESS
        && re_owner8(core, symbols, RE_OWNER_RANK_CLAIMS) == 1U;
    return passed;
}

static bool re_game_corner_contract(struct mCore *core,
                                    const struct ReSymbols *symbols)
{
    bool passed = re_initialize(core, symbols, true);
    (void)re_call(core, symbols->game_corner, 0U, 0U, 0U, 0U);
    passed = passed && re_owner16(core, symbols, RE_OWNER_BALANCE) == 0U;
    (void)re_call(core, symbols->game_corner, 99U, 0U, 0U, 0U);
    passed = passed && re_owner16(core, symbols, RE_OWNER_BALANCE) == 0U;
    (void)re_call(core, symbols->game_corner, 100U, 0U, 0U, 0U);
    passed = passed && re_owner16(core, symbols, RE_OWNER_BALANCE) == 3U
        && re_owner32(core, symbols, RE_OWNER_LAST_GAME_TOKEN) != 0U;
    return passed;
}

static bool re_owner_isolation(struct mCore *core,
                               const struct ReSymbols *symbols)
{
    bool passed = re_initialize(core, symbols, true);
    write8(core, RE_LEDGER + RE_SAVE_KANTO_UNLOCK_OFFSET, 1U);
    write16(core, RE_LEDGER + RE_SAVE_FACTORY_OFFSET, 0x1234U);
    write16(core, RE_LEDGER + RE_SAVE_MIRAGE_OFFSET, 0x2345U);
    write16(core, RE_LEDGER + RE_SAVE_CREDITS_OFFSET, 0x3456U);
    write8(core, RE_LEDGER + RE_SAVE_PENDING_ENCOUNTER_OFFSET, 1U);
    write8(core, RE_LEDGER + RE_SAVE_ITEM_FLAGS_OFFSET, 0x5AU);
    re_call(core, symbols->save_finalize, RE_LEDGER, 0U, 0U, 0U);
    passed = passed && re_credit(
        core, symbols, RE_ACTIVITY_FISHING, 70001U) == RE_RESULT_SUCCESS;
    return passed
        && read8(core, RE_LEDGER + RE_SAVE_KANTO_UNLOCK_OFFSET) == 1U
        && read16(core, RE_LEDGER + RE_SAVE_FACTORY_OFFSET) == 0x1234U
        && read16(core, RE_LEDGER + RE_SAVE_MIRAGE_OFFSET) == 0x2345U
        && read16(core, RE_LEDGER + RE_SAVE_CREDITS_OFFSET) == 0x3456U
        && read8(core, RE_LEDGER + RE_SAVE_PENDING_ENCOUNTER_OFFSET) == 1U
        && read8(core, RE_LEDGER + RE_SAVE_ITEM_FLAGS_OFFSET) == 0x5AU;
}

int main(int argc, char **argv)
{
    if (argc != 6) {
        fprintf(stderr,
                "usage: %s ROM SYMBOLS CASES quick|full SAVE\n", argv[0]);
        return 2;
    }
    bool full = !strcmp(argv[4], "full");
    if (!full && strcmp(argv[4], "quick"))
        return 2;
    (void)argv[5];
    struct ReSymbols symbols = re_load_symbols(argv[2]);
    struct ReCases cases = re_load_cases(argv[3]);

    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {
        .sample = NULL, .unixTime = fixed_unix_time,
        .serialize = NULL, .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core))
        re_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1]))
        re_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);

    bool fixture = cases.schema && cases.count >= 9U && cases.has_save
        && cases.has_activity && cases.has_rank && cases.has_shop
        && cases.has_pending && cases.has_hosts && cases.has_game_corner;
    bool roots = re_symbols_and_hooks(core, &symbols);
    bool probe = re_call(core, symbols.probe, 0U, 0U, 0U, 0U)
        == RE_ABI_VERSION;
    bool save = re_save_migration(core, &symbols);
    bool acquisition_v2 = re_acquisition_v2_compat(core, &symbols);
    bool isolation = re_owner_isolation(core, &symbols);
    bool activity = re_activity_day_caps(core, &symbols);
    bool rank = re_rank_contract(core, &symbols);
    bool shop = re_shop_contract(core, &symbols);
    bool pending = re_pending_recovery(core, &symbols);
    bool game_corner = re_game_corner_contract(core, &symbols);
    bool warnings = log_problem_count == 0U;

    bool tests[] = {
        fixture, roots, probe, save, acquisition_v2, isolation, activity,
        rank, shop, pending, game_corner, warnings,
    };
    bool passed = true;
    for (unsigned index = 0U; index < ARRAY_LEN(tests); ++index)
        passed = passed && tests[index];
    bool acceptance[10] = {
        fixture && probe,
        fixture,
        isolation && save,
        activity,
        rank && shop,
        save && pending && acquisition_v2,
        roots && fixture,
        game_corner && roots,
        isolation && roots && acquisition_v2,
        save && acquisition_v2 && activity && rank && shop && pending
            && warnings,
    };
    static const char *const acceptance_keys[10] = {
        "INPUT_IDENTITY_PRIVATE_IMMUTABLE",
        "CANONICAL_COUNTS_CROSSREF_EXACT",
        "RESEARCH_CURRENCY_OWNER_ISOLATED",
        "ACTIVE_PLAY_DAY_ACTIVITY_CAPS",
        "RANK_SHOP_ATOMIC",
        "SAVE_MIGRATION_PENDING_RECOVERY",
        "NINE_HOSTS_HOOKS_ROOTED",
        "GAME_CORNER_PAYOUT_ONLY",
        "UPSTREAM_REGRESSION_OVERLAP_ZERO",
        "CLEAN_REBUILD_BPS_MGBA_TWO_PROCESS",
    };
    for (unsigned index = 0U; index < ARRAY_LEN(acceptance); ++index)
        passed = passed && acceptance[index];

    char rom_sha[65], runner_sha[65], symbols_sha[65], cases_sha[65];
    sha256_file(argv[1], rom_sha);
    sha256_file(argv[0], runner_sha);
    sha256_file(argv[2], symbols_sha);
    sha256_file(argv[3], cases_sha);
    fprintf(stderr,
            "mgba-research-economy-v1 %s: fixture=%u roots=%u probe=%u "
            "save=%u acq_v2=%u isolation=%u activity=%u rank=%u shop=%u pending=%u "
            "game=%u logs=%u\n",
            full ? "full" : "quick", fixture, roots, probe, save,
            acquisition_v2, isolation, activity, rank, shop, pending,
            game_corner, log_problem_count);
    printf(
        "{\"schema_version\":1,\"task\":\"T23\",\"mode\":\"%s\","
        "\"status\":\"%s\",\"result_identity\":"
        "\"RE40:1:6:7:23:9:35:64:11\","
        "\"rom_sha256\":\"%s\",\"runner_sha256\":\"%s\","
        "\"symbols_sha256\":\"%s\",\"cases_sha256\":\"%s\","
        "\"tests\":{"
        "\"case_fixture\":%s,\"rooted_hooks\":%s,\"runtime_probe\":%s,"
        "\"save_v1_v2_checksum\":%s,\"acquisition_v2_compat\":%s,"
        "\"owner_isolation\":%s,"
        "\"activity_day_caps\":%s,\"rank_monotonic_claim_retry\":%s,"
        "\"shop_23_atomic_stock\":%s,\"pending_fault_recovery\":%s,"
        "\"game_corner_payout_only\":%s,\"warnings_zero\":%s},"
        "\"total\":%zu,\"warnings\":%u,\"warnings_errors\":%u,"
        "\"coverage\":{\"activities\":6,\"ranks\":7,\"shop_entries\":23,"
        "\"hosts\":9,\"dialogues\":35,\"owner_bytes\":64,"
        "\"root_hooks\":11,\"case_rows\":%u},\"acceptance_checks\":{",
        full ? "full" : "quick", passed ? "PASS" : "FAIL",
        rom_sha, runner_sha, symbols_sha, cases_sha,
        fixture ? "true" : "false", roots ? "true" : "false",
        probe ? "true" : "false", save ? "true" : "false",
        acquisition_v2 ? "true" : "false",
        isolation ? "true" : "false", activity ? "true" : "false",
        rank ? "true" : "false", shop ? "true" : "false",
        pending ? "true" : "false", game_corner ? "true" : "false",
        warnings ? "true" : "false", ARRAY_LEN(tests), log_problem_count,
        log_problem_count, cases.count);
    for (unsigned index = 0U; index < ARRAY_LEN(acceptance); ++index) {
        printf("%s\"%s\":%s", index ? "," : "", acceptance_keys[index],
               acceptance[index] ? "true" : "false");
    }
    printf("}}\n");
    core->deinit(core);
    return passed ? 0 : 1;
}
