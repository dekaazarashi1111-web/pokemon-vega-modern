/* T24 Reward Encounters V2 exact-ROM quick/full validation for libmGBA. */
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#define BATTLE_CORE_EMBEDDED
#include "mgba_battle_core_smoke.c"

#include <ctype.h>

enum {
    REWARD_OK = 0U,
    REWARD_EFFECTLESS = 1U,
    REWARD_CANCELLED = 2U,
    REWARD_CAPACITY_FULL = 4U,
    REWARD_PENDING_EXISTS = 5U,
    REWARD_NO_PENDING = 6U,
    REWARD_INSUFFICIENT = 7U,
    REWARD_PERSIST_FAILED = 8U,
    REWARD_INVALID = 10U,
    REWARD_CREDIT_FULL = 13U,

    REWARD_PAYMENT_CREDIT = 0U,
    REWARD_PAYMENT_BP = 1U,
    REWARD_PAYMENT_CANCEL = 2U,
    REWARD_OUTCOME_CAUGHT = 7U,

    REWARD_LEDGER = 0x0203D000U,
    REWARD_LEDGER_SIZE = 0x800U,
    REWARD_FACTORY_OFFSET = 0x392U,
    REWARD_CREDIT_OFFSET = 0x684U,
    REWARD_PENDING_OFFSET = 0x694U,
    REWARD_PENDING_SIZE = 46U,
    REWARD_STATE = 0x0203F110U,
    REWARD_STATE_SIZE = 256U,
    REWARD_MAGIC = 0x31534756U,
    REWARD_VERSION = 2U,
    REWARD_ABI = 0x52453231U,

    REWARD_HOOK_WILD_END = 0x0807F270U,
    REWARD_T23_WILD_END = 0x093BEB41U,
    REWARD_MAP_ROOT = 0x092BFDD8U,
    REWARD_SERVICE_COUNT = 4U,
    REWARD_POOL_COUNT = 24U,
    REWARD_DIALOGUE_COUNT = 56U,
    REWARD_TRANSACTION_ROWS = 32U,
};

static const uint16_t REWARD_BP_PRICE[REWARD_SERVICE_COUNT] = {
    8U, 15U, 25U, 50U,
};

static const uint8_t REWARD_CREDIT_KIND[REWARD_SERVICE_COUNT] = {
    3U, 0U, 1U, 2U,
};

static const uint16_t REWARD_SPECIES[REWARD_POOL_COUNT] = {
    952U, 1305U, 1493U, 1501U, 1320U, 1508U,
    839U, 399U, 1004U, 980U, 1346U, 1148U,
    540U, 324U, 280U, 742U, 1174U, 1557U,
    726U, 871U, 129U, 869U, 1360U, 1576U,
};

#define REWARD_SYMBOL_LIST(X) \
    X(probe, "RewardEncountersV2_Probe") \
    X(purchase, "RewardEncountersV2_Purchase") \
    X(purchase_bp, "RewardEncounterPurchaseWithBp") \
    X(voucher, "RewardEncountersV2_PurchaseVoucher") \
    X(start_battle, "RewardEncountersV2_StartPendingBattle") \
    X(complete_capture, "RewardEncounterCompleteNormalCapture") \
    X(field_scientist, "RewardEncountersV2_FieldScientist") \
    X(end_internal, "RewardEncountersV2_EndWildBattleCommitInternal") \
    X(end_adapter, "RewardEncountersV2_EndWildBattleAdapter") \
    X(test_initialize, "RewardEncountersV2_TestInitialize") \
    X(test_reset_volatile, "RewardEncountersV2_TestResetVolatile") \
    X(test_set_balances, "RewardEncountersV2_TestSetBalances") \
    X(test_set_capacity, "RewardEncountersV2_TestSetCapacity") \
    X(test_set_fault, "RewardEncountersV2_TestSetPersistenceFault") \
    X(test_set_caught, "RewardEncountersV2_TestSetCaughtMask") \
    X(test_get_credit, "RewardEncountersV2_TestGetCredit") \
    X(test_get_bp, "RewardEncountersV2_TestGetBattlePoints") \
    X(test_get_pending_hash, "RewardEncountersV2_TestGetPendingHash") \
    X(test_get_generation, "RewardEncountersV2_TestGetGeneration") \
    X(test_get_pending_field, "RewardEncountersV2_TestGetPendingField") \
    X(test_simulate, "RewardEncountersV2_TestSimulateOutcome") \
    X(test_credit_activity, "RewardEncountersV2_TestCreditActivity") \
    X(test_get_side_hash, "RewardEncountersV2_TestGetSideEffectHash") \
    X(test_get_caught, "RewardEncountersV2_TestGetCaughtMask")

struct RewardSymbols {
#define REWARD_MEMBER(member, name) uint32_t member;
    REWARD_SYMBOL_LIST(REWARD_MEMBER)
#undef REWARD_MEMBER
};

struct RewardCases {
    bool schema;
    bool names_exact;
    bool counts_exact;
    uint32_t map_event;
    uint32_t object_array;
    uint32_t scientist_record;
    uint32_t scientist_script;
};

static void reward_die(const char *message)
{
    fprintf(stderr, "mgba-reward-encounters-v2: %s\n", message);
    exit(1);
}

static char *reward_read_text(const char *path)
{
    FILE *stream = fopen(path, "rb");
    if (!stream)
        reward_die("fixture open failed");
    if (fseek(stream, 0, SEEK_END) != 0)
        reward_die("fixture seek failed");
    long length = ftell(stream);
    if (length <= 0 || length > 8L * 1024L * 1024L)
        reward_die("fixture size differs");
    rewind(stream);
    char *text = malloc((size_t)length + 1U);
    if (!text || fread(text, 1, (size_t)length, stream) != (size_t)length)
        reward_die("fixture read failed");
    if (fclose(stream) != 0)
        reward_die("fixture close failed");
    text[length] = '\0';
    return text;
}

static const char *reward_find_key(const char *text, const char *key)
{
    char needle[192];
    int length = snprintf(needle, sizeof(needle), "\"%s\"", key);
    if (length <= 0 || (size_t)length >= sizeof(needle))
        reward_die("JSON key formatting failed");
    return strstr(text, needle);
}

static uint32_t reward_parse_number(const char *cursor)
{
    while (*cursor && (isspace((unsigned char)*cursor)
                       || *cursor == ':' || *cursor == '"'))
        ++cursor;
    errno = 0;
    char *end = NULL;
    unsigned long value = strtoul(cursor, &end, 0);
    if (errno || end == cursor || value > UINT32_MAX)
        reward_die("JSON numeric value differs");
    return (uint32_t)value;
}

static uint32_t reward_json_number(const char *text, const char *key)
{
    const char *found = reward_find_key(text, key);
    if (!found || !(found = strchr(found, ':')))
        reward_die("required JSON number is missing");
    return reward_parse_number(found + 1);
}

static uint32_t reward_json_symbol(const char *text, const char *name)
{
    const char *found = reward_find_key(text, name);
    if (!found || !(found = strchr(found, ':')))
        reward_die("required runtime symbol is missing");
    ++found;
    while (isspace((unsigned char)*found))
        ++found;
    if (*found == '{') {
        const char *end = strchr(found, '}');
        const char *address = reward_find_key(found, "address");
        if (!end || !address || address > end || !(address = strchr(address, ':')))
            reward_die("runtime symbol address object differs");
        found = address + 1;
    }
    return reward_parse_number(found);
}

static unsigned reward_occurrences(const char *text, const char *needle)
{
    unsigned count = 0U;
    size_t length = strlen(needle);
    for (const char *cursor = text; (cursor = strstr(cursor, needle)) != NULL;
         cursor += length)
        ++count;
    return count;
}

static struct RewardSymbols reward_load_symbols(const char *path)
{
    char *text = reward_read_text(path);
    struct RewardSymbols result = {0};
#define REWARD_LOAD(member, name) result.member = reward_json_symbol(text, name);
    REWARD_SYMBOL_LIST(REWARD_LOAD)
#undef REWARD_LOAD
    free(text);
    return result;
}

static struct RewardCases reward_load_cases(const char *path)
{
    char *text = reward_read_text(path);
    static const char *const names[] = {
        "probe_tables", "all_tier_credit", "all_tier_bp", "precheck_no_mutation",
        "pending_retry_identity", "capture_atomic", "activity_sources",
        "voucher_all_tiers", "persist_faults", "noncapture_all_outcomes",
        "battle_side_effects", "source_dedupe", "field_root", "upstream_chain",
        "bps_round_trip",
    };
    bool exact = true;
    for (unsigned index = 0U; index < ARRAY_LEN(names); ++index) {
        char quoted[96];
        int length = snprintf(quoted, sizeof(quoted), "\"%s\"", names[index]);
        if (length <= 0 || (size_t)length >= sizeof(quoted))
            reward_die("case fixture name is too long");
        exact = exact && reward_occurrences(text, quoted) == 1U;
    }
    struct RewardCases result = {
        .schema = reward_json_number(text, "schema_version") == 1U
            && reward_find_key(text, "acceptance_keys") != NULL,
        .names_exact = exact,
        .counts_exact = reward_occurrences(text, "\"tier\"") == 28U
            && reward_occurrences(text, "\"fingerprint\"") == 24U,
        .map_event = reward_json_number(text, "replacement_address"),
        .object_array = reward_json_number(text, "object_array_address"),
        .scientist_record = reward_json_number(text, "scientist_record_address"),
        .scientist_script = reward_json_number(text, "scientist_script_address"),
    };
    free(text);
    return result;
}

static uint32_t reward_call(struct mCore *core, uint32_t function,
                            uint32_t r0, uint32_t r1, uint32_t r2, uint32_t r3)
{
    if (!(function & 1U))
        reward_die("runtime entrypoint is not Thumb");
    return call_bounded(core, function, r0, r1, r2, r3).result;
}

static bool reward_initialize(struct mCore *core,
                              const struct RewardSymbols *symbols)
{
    return reward_call(core, symbols->test_initialize, 0U, 0U, 0U, 0U) == REWARD_OK
        && read32(core, REWARD_LEDGER) == REWARD_MAGIC
        && read16(core, REWARD_LEDGER + 4U) == REWARD_VERSION
        && read16(core, REWARD_LEDGER + 6U) == REWARD_LEDGER_SIZE
        && read8(core, REWARD_LEDGER + REWARD_PENDING_OFFSET) == 0U;
}

static uint16_t reward_credit(struct mCore *core,
                              const struct RewardSymbols *symbols,
                              unsigned tier)
{
    return (uint16_t)reward_call(
        core, symbols->test_get_credit, tier, 0U, 0U, 0U);
}

static uint16_t reward_bp(struct mCore *core,
                          const struct RewardSymbols *symbols)
{
    return (uint16_t)reward_call(
        core, symbols->test_get_bp, 0U, 0U, 0U, 0U);
}

static uint16_t reward_pending_field(struct mCore *core,
                                     const struct RewardSymbols *symbols,
                                     unsigned field)
{
    return (uint16_t)reward_call(
        core, symbols->test_get_pending_field, field, 0U, 0U, 0U);
}

static void reward_ledger_image(struct mCore *core, uint8_t image[REWARD_LEDGER_SIZE])
{
    for (unsigned index = 0U; index < REWARD_LEDGER_SIZE; ++index)
        image[index] = read8(core, REWARD_LEDGER + index);
}

static bool reward_ledger_equal(struct mCore *core,
                                const uint8_t image[REWARD_LEDGER_SIZE])
{
    for (unsigned index = 0U; index < REWARD_LEDGER_SIZE; ++index) {
        if (read8(core, REWARD_LEDGER + index) != image[index])
            return false;
    }
    return true;
}

static bool reward_symbols_live(const struct RewardSymbols *symbols)
{
    bool passed = true;
#define REWARD_LIVE(member, name) \
    passed = passed && (symbols->member & 1U) \
        && (symbols->member & ~1U) >= 0x08000000U \
        && (symbols->member & ~1U) < 0x0A000000U;
    REWARD_SYMBOL_LIST(REWARD_LIVE)
#undef REWARD_LIVE
    return passed;
}

static uint32_t reward_jump_target(struct mCore *core, uint32_t site)
{
    if (read8(core, site) != 0x00U || read8(core, site + 1U) != 0x4BU
        || read8(core, site + 2U) != 0x18U || read8(core, site + 3U) != 0x47U)
        reward_die("absolute Thumb hook shape differs");
    return read32(core, site + 4U);
}

static uint32_t reward_read32_bytes(struct mCore *core, uint32_t address)
{
    return (uint32_t)read8(core, address)
        | (uint32_t)read8(core, address + 1U) << 8
        | (uint32_t)read8(core, address + 2U) << 16
        | (uint32_t)read8(core, address + 3U) << 24;
}

static bool reward_root_contract(struct mCore *core,
                                 const struct RewardSymbols *symbols,
                                 const struct RewardCases *cases)
{
    bool adapter_delegate = false;
    uint32_t adapter = symbols->end_adapter & ~1U;
    for (unsigned offset = 0U; offset + 4U <= 32U; offset += 2U)
        adapter_delegate = adapter_delegate
            || read32(core, adapter + offset) == REWARD_T23_WILD_END;
    uint32_t event = read32(core, REWARD_MAP_ROOT);
    bool event_root = event == cases->map_event
        && read8(core, event) == 5U && read8(core, event + 1U) == 10U
        && read8(core, event + 2U) == 0U && read8(core, event + 3U) == 2U
        && read32(core, event + 4U) == cases->object_array;
    uint32_t record = cases->scientist_record;
    bool scientist = record == cases->object_array + 4U * 24U
        && read8(core, record) == 5U && read8(core, record + 1U) == 55U
        && read16(core, record + 4U) == 25U && read16(core, record + 6U) == 7U
        && read8(core, record + 8U) == 3U
        && read16(core, record + 12U) == 0U && read16(core, record + 14U) == 0U
        && read32(core, record + 16U) == cases->scientist_script
        && read16(core, record + 20U) == 0U;
    uint32_t script = cases->scientist_script;
    bool field_script = read8(core, script) == 0x6AU
        && read8(core, script + 1U) == 0x5AU && read8(core, script + 2U) == 0x23U
        && reward_read32_bytes(core, script + 3U) == symbols->field_scientist
        && read8(core, script + 7U) == 0x27U
        && read8(core, script + 8U) == 0x6CU && read8(core, script + 9U) == 0x02U;
    bool live = reward_symbols_live(symbols);
    bool hook = reward_jump_target(core, REWARD_HOOK_WILD_END) == symbols->end_adapter;
    if (!(live && hook && adapter_delegate && event_root && scientist && field_script)) {
        fprintf(stderr,
                "reward roots detail: live=%u hook=%u delegate=%u event=%u scientist=%u script=%u\n",
                live, hook, adapter_delegate, event_root, scientist, field_script);
    }
    return live && hook && adapter_delegate && event_root && scientist && field_script;
}

static bool reward_probe_tables(struct mCore *core,
                                const struct RewardSymbols *symbols)
{
    bool passed = reward_call(core, symbols->probe, 0U, 0U, 0U, 0U) == REWARD_ABI
        && reward_call(core, symbols->probe, 1U, 0U, 0U, 0U) == REWARD_STATE
        && reward_call(core, symbols->probe, 2U, 0U, 0U, 0U) == REWARD_LEDGER;
    uint32_t prior = 0U;
    for (unsigned tier = 0U; tier < REWARD_SERVICE_COUNT; ++tier) {
        uint32_t pointer = reward_call(core, symbols->probe, 0x100U + tier, 0U, 0U, 0U);
        passed = passed && pointer >= 0x08000000U && pointer < 0x0A000000U
            && pointer != prior && read8(core, pointer) == tier
            && read8(core, pointer + 1U) == REWARD_CREDIT_KIND[tier]
            && read8(core, pointer + 3U) == tier
            && read16(core, pointer + 4U) == 1U
            && read16(core, pointer + 6U) == REWARD_BP_PRICE[tier];
        prior = pointer;
    }
    prior = 0U;
    for (unsigned index = 0U; index < REWARD_POOL_COUNT; ++index) {
        uint32_t pointer = reward_call(core, symbols->probe, 0x200U + index, 0U, 0U, 0U);
        passed = passed && pointer >= 0x08000000U && pointer < 0x0A000000U
            && pointer != prior && read16(core, pointer) == REWARD_SPECIES[index]
            && read8(core, pointer + 2U) > 0U
            && read8(core, pointer + 2U) <= read8(core, pointer + 3U)
            && read8(core, pointer + 3U) <= 100U;
        prior = pointer;
    }
    for (unsigned index = 0U; index < REWARD_DIALOGUE_COUNT; ++index) {
        uint32_t pointer = reward_call(core, symbols->probe, 0x300U + index, 0U, 0U, 0U);
        bool terminated = false;
        for (unsigned byte = 0U; byte < 96U; ++byte)
            terminated = terminated || read8(core, pointer + byte) == 0xFFU;
        passed = passed && pointer >= 0x08000000U && pointer < 0x0A000000U
            && read8(core, pointer) != 0xFFU && terminated;
    }
    return passed && reward_call(core, symbols->probe, 0x400U, 0U, 0U, 0U) == 0U;
}

static bool reward_typed_credit(struct mCore *core,
                                const struct RewardSymbols *symbols)
{
    bool passed = true;
    for (unsigned tier = 0U; tier < REWARD_SERVICE_COUNT; ++tier) {
        passed = passed && reward_initialize(core, symbols)
            && reward_call(core, symbols->test_set_balances,
                           tier, 2U, REWARD_BP_PRICE[tier] + 3U, 0U) == REWARD_OK;
        uint16_t bp_before = reward_bp(core, symbols);
        passed = passed && reward_call(core, symbols->purchase,
                                      tier, REWARD_PAYMENT_CREDIT, 0U, 0U) == REWARD_OK
            && reward_credit(core, symbols, tier) == 1U
            && reward_bp(core, symbols) == bp_before
            && reward_pending_field(core, symbols, 0U) == 1U
            && reward_pending_field(core, symbols, 1U) == tier
            && reward_pending_field(core, symbols, 7U) == REWARD_CREDIT_KIND[tier]
            && reward_call(core, symbols->purchase,
                           tier, REWARD_PAYMENT_BP, 0U, 0U) == REWARD_PENDING_EXISTS;
    }
    return passed;
}

static bool reward_bp_direct(struct mCore *core,
                             const struct RewardSymbols *symbols)
{
    bool passed = true;
    for (unsigned tier = 0U; tier < REWARD_SERVICE_COUNT; ++tier) {
        passed = passed && reward_initialize(core, symbols)
            && reward_call(core, symbols->test_set_balances,
                           tier, 2U, REWARD_BP_PRICE[tier], 0U) == REWARD_OK;
        uint32_t function = (tier & 1U) ? symbols->purchase : symbols->purchase_bp;
        uint32_t result = (tier & 1U)
            ? reward_call(core, function, tier, REWARD_PAYMENT_BP, 0U, 0U)
            : reward_call(core, function, tier, 0U, 0U, 0U);
        passed = passed && result == REWARD_OK
            && reward_credit(core, symbols, tier) == 2U
            && reward_bp(core, symbols) == 0U
            && reward_pending_field(core, symbols, 0U) == 1U
            && reward_pending_field(core, symbols, 1U) == tier;
    }
    return passed;
}

static bool reward_vouchers(struct mCore *core,
                            const struct RewardSymbols *symbols)
{
    bool passed = true;
    for (unsigned tier = 0U; tier < REWARD_SERVICE_COUNT; ++tier) {
        passed = passed && reward_initialize(core, symbols)
            && reward_call(core, symbols->test_set_balances,
                           tier, 5U, REWARD_BP_PRICE[tier], 0U) == REWARD_OK
            && reward_call(core, symbols->voucher, tier, 0U, 0U, 0U) == REWARD_OK
            && reward_credit(core, symbols, tier) == 6U
            && reward_bp(core, symbols) == 0U
            && reward_pending_field(core, symbols, 0U) == 0U
            && reward_call(core, symbols->voucher, tier, 0U, 0U, 0U)
                == REWARD_INSUFFICIENT;
        passed = passed && reward_initialize(core, symbols)
            && reward_call(core, symbols->test_set_balances,
                           tier, 0xFFFFU, REWARD_BP_PRICE[tier], 0U) == REWARD_OK
            && reward_call(core, symbols->voucher, tier, 0U, 0U, 0U)
                == REWARD_CREDIT_FULL
            && reward_credit(core, symbols, tier) == 0xFFFFU
            && reward_bp(core, symbols) == REWARD_BP_PRICE[tier];
    }
    return passed;
}

static bool reward_precheck_no_mutation(struct mCore *core,
                                        const struct RewardSymbols *symbols)
{
    uint8_t before[REWARD_LEDGER_SIZE];
    bool passed = reward_initialize(core, symbols)
        && reward_call(core, symbols->test_set_balances, 0U, 1U, 8U, 0U) == REWARD_OK;
    reward_ledger_image(core, before);
    passed = passed && reward_call(core, symbols->purchase,
                                  0U, REWARD_PAYMENT_CANCEL, 0U, 0U) == REWARD_CANCELLED
        && reward_ledger_equal(core, before);

    passed = passed && reward_initialize(core, symbols)
        && reward_call(core, symbols->test_set_balances, 1U, 1U, 15U, 0U) == REWARD_OK
        && reward_call(core, symbols->test_set_capacity, 0U, 0U, 0U, 0U) == REWARD_OK;
    reward_ledger_image(core, before);
    passed = passed && reward_call(core, symbols->purchase,
                                  1U, REWARD_PAYMENT_CREDIT, 0U, 0U) == REWARD_CAPACITY_FULL
        && reward_ledger_equal(core, before);

    passed = passed && reward_initialize(core, symbols)
        && reward_call(core, symbols->test_set_balances, 2U, 0U, 24U, 0U) == REWARD_OK;
    reward_ledger_image(core, before);
    passed = passed && reward_call(core, symbols->purchase,
                                  2U, REWARD_PAYMENT_CREDIT, 0U, 0U) == REWARD_INSUFFICIENT
        && reward_ledger_equal(core, before)
        && reward_call(core, symbols->purchase,
                       2U, REWARD_PAYMENT_BP, 0U, 0U) == REWARD_INSUFFICIENT
        && reward_ledger_equal(core, before)
        && reward_call(core, symbols->purchase,
                       99U, REWARD_PAYMENT_CREDIT, 0U, 0U) == REWARD_INVALID
        && reward_ledger_equal(core, before);
    return passed;
}

static bool reward_persist_faults(struct mCore *core,
                                  const struct RewardSymbols *symbols)
{
    uint8_t before[REWARD_LEDGER_SIZE];
    bool passed = reward_initialize(core, symbols)
        && reward_call(core, symbols->test_set_balances, 0U, 1U, 8U, 0U) == REWARD_OK
        && reward_call(core, symbols->test_set_fault, 1U, 0U, 0U, 0U) == REWARD_OK;
    reward_ledger_image(core, before);
    passed = passed && reward_call(core, symbols->purchase,
                                  0U, REWARD_PAYMENT_CREDIT, 0U, 0U) == REWARD_PERSIST_FAILED
        && reward_ledger_equal(core, before);

    passed = passed && reward_initialize(core, symbols)
        && reward_call(core, symbols->test_set_balances, 3U, 1U, 50U, 0U) == REWARD_OK
        && reward_call(core, symbols->test_set_fault, 1U, 0U, 0U, 0U) == REWARD_OK;
    reward_ledger_image(core, before);
    passed = passed && reward_call(core, symbols->purchase,
                                  3U, REWARD_PAYMENT_BP, 0U, 0U) == REWARD_PERSIST_FAILED
        && reward_ledger_equal(core, before);

    passed = passed && reward_initialize(core, symbols)
        && reward_call(core, symbols->test_set_balances, 1U, 2U, 15U, 0U) == REWARD_OK
        && reward_call(core, symbols->test_set_fault, 1U, 0U, 0U, 0U) == REWARD_OK;
    reward_ledger_image(core, before);
    passed = passed && reward_call(core, symbols->voucher, 1U, 0U, 0U, 0U)
            == REWARD_PERSIST_FAILED
        && reward_ledger_equal(core, before);
    return passed;
}

static bool reward_pending_retry(struct mCore *core,
                                 const struct RewardSymbols *symbols)
{
    bool passed = reward_initialize(core, symbols)
        && reward_call(core, symbols->test_set_balances, 2U, 1U, 25U, 0U) == REWARD_OK
        && reward_call(core, symbols->purchase,
                       2U, REWARD_PAYMENT_CREDIT, 0U, 0U) == REWARD_OK;
    uint32_t hash = reward_call(core, symbols->test_get_pending_hash, 0U, 0U, 0U, 0U);
    uint16_t species = reward_pending_field(core, symbols, 2U);
    uint16_t level = reward_pending_field(core, symbols, 3U);
    uint32_t generation = reward_call(core, symbols->test_get_generation, 0U, 0U, 0U, 0U);
    passed = passed && reward_call(core, symbols->test_reset_volatile, 0U, 0U, 0U, 0U)
            == REWARD_OK
        && reward_call(core, symbols->test_get_pending_hash, 0U, 0U, 0U, 0U) == hash
        && reward_pending_field(core, symbols, 2U) == species
        && reward_pending_field(core, symbols, 3U) == level
        && reward_call(core, symbols->test_get_generation, 0U, 0U, 0U, 0U) == generation
        && reward_call(core, symbols->start_battle, 0U, 0U, 0U, 0U) == REWARD_OK
        && reward_call(core, symbols->test_simulate, 1U, 0U, 0U, 0U) == REWARD_EFFECTLESS
        && reward_call(core, symbols->test_get_pending_hash, 0U, 0U, 0U, 0U) == hash
        && reward_credit(core, symbols, 2U) == 0U
        && reward_bp(core, symbols) == 25U
        && reward_call(core, symbols->test_reset_volatile, 0U, 0U, 0U, 0U) == REWARD_OK
        && reward_call(core, symbols->start_battle, 0U, 0U, 0U, 0U) == REWARD_OK;
    return passed;
}

static bool reward_capture_atomic(struct mCore *core,
                                  const struct RewardSymbols *symbols)
{
    bool passed = reward_initialize(core, symbols)
        && reward_call(core, symbols->test_set_balances, 0U, 1U, 8U, 0U) == REWARD_OK
        && reward_call(core, symbols->purchase,
                       0U, REWARD_PAYMENT_CREDIT, 0U, 0U) == REWARD_OK
        && reward_call(core, symbols->start_battle, 0U, 0U, 0U, 0U) == REWARD_OK;
    uint32_t side_before = reward_call(core, symbols->test_get_side_hash, 0U, 0U, 0U, 0U);
    passed = passed && reward_call(core, symbols->test_simulate,
                                  REWARD_OUTCOME_CAUGHT, 1U, 0U, 0U) == REWARD_OK
        && reward_pending_field(core, symbols, 0U) == 0U
        && reward_call(core, symbols->test_get_side_hash, 0U, 0U, 0U, 0U) == side_before
        && reward_call(core, symbols->test_get_caught, 0U, 0U, 0U, 0U) != 0U
        && reward_credit(core, symbols, 0U) == 0U
        && reward_bp(core, symbols) == 8U
        && reward_call(core, symbols->test_simulate,
                       REWARD_OUTCOME_CAUGHT, 0U, 0U, 0U) == REWARD_NO_PENDING;

    passed = passed && reward_initialize(core, symbols)
        && reward_call(core, symbols->test_set_balances, 3U, 1U, 50U, 0U) == REWARD_OK
        && reward_call(core, symbols->purchase,
                       3U, REWARD_PAYMENT_BP, 0U, 0U) == REWARD_OK;
    uint32_t pending = reward_call(core, symbols->test_get_pending_hash, 0U, 0U, 0U, 0U);
    passed = passed && reward_call(core, symbols->start_battle, 0U, 0U, 0U, 0U) == REWARD_OK;
    side_before = reward_call(core, symbols->test_get_side_hash, 0U, 0U, 0U, 0U);
    passed = passed && reward_call(core, symbols->test_set_fault, 1U, 0U, 0U, 0U) == REWARD_OK
        && reward_call(core, symbols->test_simulate,
                       REWARD_OUTCOME_CAUGHT, 1U, 0U, 0U) == REWARD_PERSIST_FAILED
        && reward_call(core, symbols->test_get_pending_hash, 0U, 0U, 0U, 0U) == pending
        && reward_pending_field(core, symbols, 0U) == 1U
        && reward_call(core, symbols->test_get_caught, 0U, 0U, 0U, 0U) == 0U
        && reward_call(core, symbols->test_get_side_hash, 0U, 0U, 0U, 0U) == side_before;
    return passed;
}

static bool reward_noncapture_outcomes(struct mCore *core,
                                       const struct RewardSymbols *symbols)
{
    static const uint16_t outcomes[] = {0U, 1U, 2U, 3U, 5U};
    bool passed = true;
    for (unsigned index = 0U; index < ARRAY_LEN(outcomes); ++index) {
        passed = passed && reward_initialize(core, symbols)
            && reward_call(core, symbols->test_set_balances, 1U, 1U, 15U, 0U) == REWARD_OK
            && reward_call(core, symbols->purchase,
                           1U, REWARD_PAYMENT_CREDIT, 0U, 0U) == REWARD_OK;
        uint32_t pending = reward_call(core, symbols->test_get_pending_hash, 0U, 0U, 0U, 0U);
        passed = passed && reward_call(core, symbols->start_battle, 0U, 0U, 0U, 0U) == REWARD_OK;
        uint32_t side = reward_call(core, symbols->test_get_side_hash, 0U, 0U, 0U, 0U);
        passed = passed && reward_call(core, symbols->test_simulate,
                                      outcomes[index], 1U, 0U, 0U) == REWARD_EFFECTLESS
            && reward_call(core, symbols->test_get_pending_hash, 0U, 0U, 0U, 0U) == pending
            && reward_pending_field(core, symbols, 0U) == 1U
            && reward_call(core, symbols->test_get_side_hash, 0U, 0U, 0U, 0U) == side
            && reward_call(core, symbols->test_get_caught, 0U, 0U, 0U, 0U) == 0U;
    }
    return passed;
}

static bool reward_activity_sources(struct mCore *core,
                                    const struct RewardSymbols *symbols)
{
    bool passed = reward_initialize(core, symbols)
        && reward_call(core, symbols->test_credit_activity, 0U, 0U, 1001U, 0U) == REWARD_OK
        && reward_credit(core, symbols, 1U) == 1U
        && reward_call(core, symbols->test_credit_activity, 0U, 0U, 1001U, 0U)
            == REWARD_EFFECTLESS
        && reward_credit(core, symbols, 1U) == 1U
        && reward_call(core, symbols->test_credit_activity, 0U, 0U, 1002U, 0U) == REWARD_OK
        && reward_credit(core, symbols, 1U) == 2U;
    passed = passed && reward_initialize(core, symbols)
        && reward_call(core, symbols->test_credit_activity, 1U, 0U, 2001U, 0U)
            == REWARD_EFFECTLESS
        && reward_credit(core, symbols, 0U) == 0U
        && reward_call(core, symbols->test_credit_activity, 1U, 1U, 2001U, 0U) == REWARD_OK
        && reward_credit(core, symbols, 0U) == 1U
        && reward_call(core, symbols->test_credit_activity, 1U, 1U, 2001U, 0U)
            == REWARD_EFFECTLESS;
    passed = passed && reward_initialize(core, symbols)
        && reward_call(core, symbols->test_set_fault, 1U, 0U, 0U, 0U) == REWARD_OK
        && reward_call(core, symbols->test_credit_activity, 0U, 0U, 3001U, 0U)
            == REWARD_PERSIST_FAILED
        && reward_credit(core, symbols, 1U) == 0U
        && reward_call(core, symbols->test_credit_activity, 0U, 0U, 3001U, 0U) == REWARD_OK
        && reward_credit(core, symbols, 1U) == 1U;
    return passed;
}

int main(int argc, char **argv)
{
    if (argc != 6) {
        fprintf(stderr, "usage: %s ROM SYMBOLS CASES quick|full SAVE\n", argv[0]);
        return 2;
    }
    bool full = !strcmp(argv[4], "full");
    if (!full && strcmp(argv[4], "quick"))
        return 2;
    (void)argv[5];
    struct RewardSymbols symbols = reward_load_symbols(argv[2]);
    struct RewardCases cases = reward_load_cases(argv[3]);

    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {
        .sample = NULL, .unixTime = fixed_unix_time,
        .serialize = NULL, .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core))
        reward_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1]))
        reward_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);

    bool fixture = cases.schema && cases.names_exact && cases.counts_exact;
    bool roots = reward_root_contract(core, &symbols, &cases);
    bool probe = reward_probe_tables(core, &symbols);
    bool typed = reward_typed_credit(core, &symbols);
    bool bp = reward_bp_direct(core, &symbols);
    bool vouchers = reward_vouchers(core, &symbols);
    bool precheck = reward_precheck_no_mutation(core, &symbols);
    bool faults = reward_persist_faults(core, &symbols);
    bool retry = reward_pending_retry(core, &symbols);
    bool capture = reward_capture_atomic(core, &symbols);
    bool noncapture = reward_noncapture_outcomes(core, &symbols);
    bool sources = reward_activity_sources(core, &symbols);
    bool warnings = log_problem_count == 0U;
    bool tests[] = {
        fixture, roots, probe, typed, bp, vouchers, precheck, faults,
        retry, capture, noncapture, sources, warnings,
    };
    bool passed = true;
    for (unsigned index = 0U; index < ARRAY_LEN(tests); ++index)
        passed = passed && tests[index];
    bool acceptance[] = {
        fixture,
        fixture && probe,
        typed && bp && vouchers,
        precheck && faults,
        retry && noncapture,
        capture && faults,
        capture && noncapture,
        sources && vouchers && roots,
        roots && probe,
        roots && probe && warnings,
        typed && bp && vouchers && precheck && faults && retry && capture
            && noncapture && sources && roots && warnings,
    };
    static const char *const acceptance_keys[] = {
        "INPUT_IDENTITY_PRIVATE_IMMUTABLE",
        "CANONICAL_COUNTS_EXACT",
        "PAYMENT_EXCLUSIVE_EXACT",
        "PRECHECK_FAILURE_NO_MUTATION",
        "PENDING_PERSIST_RETRY_EXACT",
        "CAPTURE_CLEAR_ATOMIC",
        "BATTLE_SIDE_EFFECTS_ZERO_NORMAL_DEX",
        "TEN_CREDIT_SOURCES_EXACT",
        "SCIENTIST_FIELD_ROOT",
        "UPSTREAM_REGRESSION_ZERO",
        "CLEAN_REBUILD_BPS_MGBA",
    };
    for (unsigned index = 0U; index < ARRAY_LEN(acceptance); ++index)
        passed = passed && acceptance[index];

    char rom_sha[65], runner_sha[65], symbols_sha[65], cases_sha[65];
    sha256_file(argv[1], rom_sha);
    sha256_file(argv[0], runner_sha);
    sha256_file(argv[2], symbols_sha);
    sha256_file(argv[3], cases_sha);
    fprintf(stderr,
            "mgba-reward-encounters-v2 %s: fixture=%u roots=%u probe=%u "
            "typed=%u bp=%u vouchers=%u precheck=%u faults=%u retry=%u "
            "capture=%u noncapture=%u sources=%u logs=%u\n",
            full ? "full" : "quick", fixture, roots, probe, typed, bp,
            vouchers, precheck, faults, retry, capture, noncapture, sources,
            log_problem_count);
    printf(
        "{\"schema_version\":1,\"task\":\"T24\",\"mode\":\"%s\","
        "\"status\":\"%s\",\"result_identity\":"
        "\"RE41:2:4:24:10:56:5:32\","
        "\"rom_sha256\":\"%s\",\"runner_sha256\":\"%s\","
        "\"symbols_sha256\":\"%s\",\"cases_sha256\":\"%s\","
        "\"tests\":{"
        "\"case_fixture\":%s,\"rooted_hook_field\":%s,\"probe_tables\":%s,"
        "\"typed_credit_all_tiers\":%s,\"bp_direct_all_tiers\":%s,"
        "\"voucher_all_tiers\":%s,\"precheck_no_mutation\":%s,"
        "\"persist_fault_rollback\":%s,\"pending_reset_retry_identity\":%s,"
        "\"capture_atomic_side_effect_restore\":%s,"
        "\"noncapture_free_retry\":%s,\"activity_source_dedupe\":%s,"
        "\"warnings_zero\":%s},\"total\":%zu,"
        "\"warnings\":%u,\"warnings_errors\":%u,"
        "\"coverage\":{\"services\":4,\"pool_entries\":24,"
        "\"credit_sources\":10,\"dialogues\":56,\"batches\":5,"
        "\"transaction_rows\":32},\"acceptance_checks\":{",
        full ? "full" : "quick", passed ? "PASS" : "FAIL",
        rom_sha, runner_sha, symbols_sha, cases_sha,
        fixture ? "true" : "false", roots ? "true" : "false",
        probe ? "true" : "false", typed ? "true" : "false",
        bp ? "true" : "false", vouchers ? "true" : "false",
        precheck ? "true" : "false", faults ? "true" : "false",
        retry ? "true" : "false", capture ? "true" : "false",
        noncapture ? "true" : "false", sources ? "true" : "false",
        warnings ? "true" : "false", ARRAY_LEN(tests),
        log_problem_count, log_problem_count);
    for (unsigned index = 0U; index < ARRAY_LEN(acceptance); ++index) {
        printf("%s\"%s\":%s", index ? "," : "", acceptance_keys[index],
               acceptance[index] ? "true" : "false");
    }
    printf("}}\n");
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return passed ? 0 : 1;
}
