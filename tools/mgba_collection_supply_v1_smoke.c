/* Stage56 Collection Supply V1 exact-ROM quick/full validation. */
#if defined(__GNUC__)
#pragma GCC diagnostic ignored "-Wunused-function"
#endif
#define VW_RUNTIME_EMBEDDED
#include "mgba_windows_box14_vault_smoke.c"

#include <ctype.h>

enum {
    CS_RESULT_SUCCESS = 0U,
    CS_RESULT_EFFECTLESS = 1U,
    CS_RESULT_INVALID = 5U,
    CS_RESULT_INSUFFICIENT = 14U,
    CS_RESULT_BAG_FULL = 15U,
    CS_RESULT_PERSIST_FAILED = 17U,
    CS_RESULT_RAID_REQUEST = 22U,
    CS_RESULT_BATTLE_STARTED = 23U,

    CS_CURRENCY_MONEY = 1U,
    CS_CURRENCY_BP = 2U,
    CS_CURRENCY_RESEARCH = 3U,

    CS_ABI_VERSION = 0x43535631U,
    CS_OWNER = 0x0203D900U,
    CS_OWNER_SIZE = 512U,
    CS_OWNER_MAGIC = 0x31565343U,
    CS_OWNER_CRC = 12U,
    CS_OWNER_GENERATION = 16U,
    CS_OWNER_PENDING = 20U,
    CS_VOLATILE = 0x0203F720U,
    CS_READ_KEYS_SITE = 0x080005ECU,
    CS_SAVE_LOAD_SITE = 0x080DB4E4U,
    CS_LAND_WATER_SITE = 0x080826D8U,
    CS_WILD_END_SITE = 0x0807F270U,
    CS_GMAX_BYTE = 0x47U,
    CS_GMAX_MASK = 0x08U,
    CS_TERA_BYTE = 0x11U,
    CS_HOST_COUNT = 14U,
    CS_VAULT_BATCH = 30U,
};

static const char *const cs_test_names[] = {
    "probe_and_canonical_counts",
    "owner_crc_and_sector31_restore",
    "money_bp_research_and_relic_transactions",
    "form_service_gift_egg_and_wild_overlay",
    "gmax_toggle_capture_and_raw80_vault",
    "raid_rotation_capture_reward_and_retry",
    "fourteen_world_hosts_normal_a_input",
    "stage55_world_regression",
    "warnings_zero",
};

#define CS_SYMBOL_LIST(X) \
    X(probe, "CollectionSupply_Probe") \
    X(field_host, "CollectionSupply_FieldHost") \
    X(start_raid, "CollectionSupply_StartSelectedRaid") \
    X(read_keys, "CollectionSupply_ReadKeysAdapter") \
    X(save_load, "CollectionSupply_SaveLoadAdapter") \
    X(land_water, "CollectionSupply_TryGenerateWildMonAdapter") \
    X(wild_end, "CollectionSupply_EndWildBattleAdapter") \
    X(test_initialize, "CollectionSupply_TestInitialize") \
    X(test_purchase, "CollectionSupply_TestPurchase") \
    X(test_apply_form, "CollectionSupply_TestApplyForm") \
    X(test_toggle_gmax, "CollectionSupply_TestToggleGmax") \
    X(test_prepare_raid, "CollectionSupply_TestPrepareRaid") \
    X(test_complete_raid, "CollectionSupply_TestCompleteRaid") \
    X(test_gift, "CollectionSupply_TestGift") \
    X(test_claim_relic, "CollectionSupply_TestClaimRelic") \
    X(test_owner_field, "CollectionSupply_TestOwnerField") \
    X(test_balance, "CollectionSupply_TestBalance") \
    X(test_sector_round_trip, "CollectionSupply_TestSectorRoundTrip") \
    X(test_set_fault, "CollectionSupply_TestSetFault") \
    X(test_set_balances, "CollectionSupply_TestSetBalances") \
    X(test_set_bag, "CollectionSupply_TestSetBag") \
    X(test_seed_party, "CollectionSupply_TestSeedParty") \
    X(test_party_field, "CollectionSupply_TestPartyField") \
    X(test_bag_count, "CollectionSupply_TestBagCount") \
    X(test_bag_item, "CollectionSupply_TestBagItem") \
    X(test_gift_field, "CollectionSupply_TestGiftField") \
    X(test_raid_field, "CollectionSupply_TestRaidField")

struct CsSymbols {
#define CS_MEMBER(member, name) uint32_t member;
    CS_SYMBOL_LIST(CS_MEMBER)
#undef CS_MEMBER
};

struct CsCases {
    bool exact_tests;
    uint32_t money_index, money_item, money_price, money_quantity;
    uint32_t bp_index, bp_item, bp_price, bp_quantity;
    uint32_t research_index, research_item, research_price, research_quantity;
    uint32_t relic_index, relic_item;
    uint32_t form_index, form_base, form_target;
    uint32_t fixed_gift_index, fixed_gift_species;
    uint32_t research_egg_index, research_egg_species;
    uint32_t gmax_base, dynamax_candy_item, gmax_host, raid_retry_host;
    uint32_t stage55_fixtures, stage55_processes;
    uint32_t quick_iterations, full_iterations;
    uint32_t map_site[CS_HOST_COUNT];
    uint32_t map_target[CS_HOST_COUNT];
    uint32_t map_bg_count[CS_HOST_COUNT];
    uint32_t map_x[CS_HOST_COUNT];
    uint32_t map_y[CS_HOST_COUNT];
    uint32_t map_elevation[CS_HOST_COUNT];
};

static uint32_t cs_call(struct mCore *core, uint32_t function,
                        uint32_t r0, uint32_t r1,
                        uint32_t r2, uint32_t r3)
{
    return cwr_call(core, function, r0, r1, r2, r3);
}

static struct CsSymbols cs_load_symbols(const char *path)
{
    char *text = cbr_read_text(path);
    struct CsSymbols result = {0};
#define CS_LOAD(member, name) result.member = cbr_json_symbol(text, name);
    CS_SYMBOL_LIST(CS_LOAD)
#undef CS_LOAD
    free(text);
    return result;
}

static uint32_t cs_case_number(const char *text, const char *name)
{
    return cbr_json_symbol(text, name);
}

static struct CsCases cs_load_cases(const char *path)
{
    char *text = cbr_read_text(path);
    struct CsCases result = {0};
    result.exact_tests = true;
    for (unsigned index = 0U; index < ARRAY_LEN(cs_test_names); ++index) {
        char quoted[192];
        if (snprintf(quoted, sizeof(quoted), "\"%s\"",
                     cs_test_names[index]) < 0)
            cwr_die("Collection test name formatting failed");
        result.exact_tests = result.exact_tests
            && cbr_occurrences(text, quoted) == 1U;
    }
#define CS_CASE(name) result.name = cs_case_number(text, #name)
    CS_CASE(money_index); CS_CASE(money_item); CS_CASE(money_price);
    CS_CASE(money_quantity); CS_CASE(bp_index); CS_CASE(bp_item);
    CS_CASE(bp_price); CS_CASE(bp_quantity); CS_CASE(research_index);
    CS_CASE(research_item); CS_CASE(research_price);
    CS_CASE(research_quantity); CS_CASE(relic_index); CS_CASE(relic_item);
    CS_CASE(form_index); CS_CASE(form_base); CS_CASE(form_target);
    CS_CASE(fixed_gift_index); CS_CASE(fixed_gift_species);
    CS_CASE(research_egg_index); CS_CASE(research_egg_species);
    CS_CASE(gmax_base); CS_CASE(dynamax_candy_item); CS_CASE(gmax_host);
    CS_CASE(raid_retry_host); CS_CASE(quick_iterations);
    CS_CASE(full_iterations);
#undef CS_CASE
    result.stage55_fixtures = cs_case_number(
        text, "stage55_world_fixture_count");
    result.stage55_processes = cs_case_number(
        text, "stage55_world_process_count");
    for (unsigned index = 0U; index < CS_HOST_COUNT; ++index) {
        char key[64];
#define CS_MAP_FIELD(member, suffix) \
        (void)snprintf(key, sizeof(key), "map_%02u_" suffix, index); \
        result.member[index] = cs_case_number(text, key)
        CS_MAP_FIELD(map_site, "site");
        CS_MAP_FIELD(map_target, "target");
        CS_MAP_FIELD(map_bg_count, "bg_count");
        CS_MAP_FIELD(map_x, "x");
        CS_MAP_FIELD(map_y, "y");
        CS_MAP_FIELD(map_elevation, "elevation");
#undef CS_MAP_FIELD
    }
    free(text);
    return result;
}

static bool cs_jump_root(struct mCore *core, uint32_t site, uint32_t target)
{
    return read16(core, site) == 0x4B00U
        && read16(core, site + 2U) == 0x4718U
        && read32(core, site + 4U) == target;
}

static bool cs_owner_valid(struct mCore *core)
{
    uint8_t raw[CS_OWNER_SIZE];
    for (unsigned index = 0U; index < sizeof(raw); ++index)
        raw[index] = read8(core, CS_OWNER + index);
    uint32_t stored = vw_get32(raw, CS_OWNER_CRC);
    memset(raw + CS_OWNER_CRC, 0, 4U);
    return vw_get32(raw, 0U) == CS_OWNER_MAGIC
        && vw_get32(raw, 4U) == ~(uint32_t)CS_OWNER_MAGIC
        && vw_get16(raw, 8U) == 1U
        && vw_get16(raw, 10U) == CS_OWNER_SIZE
        && stored == cbr_crc_bytes(raw, sizeof(raw));
}

static bool cs_probe_test(struct mCore *core, const struct CsSymbols *symbols,
                          const struct CsCases *cases)
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
        && cs_jump_root(core, CS_LAND_WATER_SITE, symbols->land_water)
        && cs_jump_root(core, CS_WILD_END_SITE, symbols->wild_end);
}

static bool cs_owner_test(struct mCore *core,
                          const struct CsSymbols *symbols)
{
    if (cs_call(core, symbols->test_initialize, 0U, 0U, 0U, 0U)
            != CS_RESULT_SUCCESS || !cs_owner_valid(core))
        return false;
    uint32_t generation = read32(core, CS_OWNER + CS_OWNER_GENERATION);
    if (cs_call(core, symbols->test_sector_round_trip, 0U, 0U, 0U, 0U)
            != CS_RESULT_SUCCESS || !cs_owner_valid(core)
            || read32(core, CS_OWNER + CS_OWNER_GENERATION) != generation)
        return false;
    write8(core, CS_OWNER + 120U,
           (uint8_t)(read8(core, CS_OWNER + 120U) ^ 0x5AU));
    if (cs_owner_valid(core))
        return false;
    return cs_call(core, symbols->test_owner_field, 0U, 0U, 0U, 0U) == 1U
        && read8(core, CS_OWNER + CS_OWNER_PENDING) == 0U
        && cs_owner_valid(core);
}

static bool cs_purchase_one(struct mCore *core,
                            const struct CsSymbols *symbols,
                            uint32_t currency, uint32_t index,
                            uint32_t item, uint32_t price,
                            uint32_t quantity)
{
    uint32_t money = currency == CS_CURRENCY_MONEY ? price : 0U;
    uint32_t bp = currency == CS_CURRENCY_BP ? price : 0U;
    uint32_t research = currency == CS_CURRENCY_RESEARCH ? price : 0U;
    bool passed = cs_call(core, symbols->test_initialize, 0U, 0U, 0U, 0U)
            == CS_RESULT_SUCCESS
        && cs_call(core, symbols->test_set_balances,
                   money, bp, research, 0U) == CS_RESULT_SUCCESS
        && cs_call(core, symbols->test_set_bag, 0U, 0U, 999U, 0U)
            == CS_RESULT_SUCCESS
        && cs_call(core, symbols->test_purchase, index, 0U, 0U, 0U)
            == CS_RESULT_SUCCESS
        && cs_call(core, symbols->test_bag_count, item, 0U, 0U, 0U)
            == quantity
        && cs_call(core, symbols->test_balance, currency, 0U, 0U, 0U) == 0U
        && cs_call(core, symbols->test_owner_field, 1U, 0U, 0U, 0U) == 0U
        && cs_owner_valid(core);
    money = currency == CS_CURRENCY_MONEY ? price - 1U : 0U;
    bp = currency == CS_CURRENCY_BP ? price - 1U : 0U;
    research = currency == CS_CURRENCY_RESEARCH ? price - 1U : 0U;
    passed = passed
        && cs_call(core, symbols->test_initialize, 0U, 0U, 0U, 0U) == 0U
        && cs_call(core, symbols->test_set_balances,
                   money, bp, research, 0U) == 0U
        && cs_call(core, symbols->test_purchase, index, 0U, 0U, 0U)
            == CS_RESULT_INSUFFICIENT
        && cs_call(core, symbols->test_bag_count, item, 0U, 0U, 0U) == 0U;
    money = currency == CS_CURRENCY_MONEY ? price : 0U;
    bp = currency == CS_CURRENCY_BP ? price : 0U;
    research = currency == CS_CURRENCY_RESEARCH ? price : 0U;
    passed = passed
        && cs_call(core, symbols->test_initialize, 0U, 0U, 0U, 0U) == 0U
        && cs_call(core, symbols->test_set_balances,
                   money, bp, research, 0U) == 0U
        && cs_call(core, symbols->test_set_fault, 1U, 0U, 0U, 0U) == 0U
        && cs_call(core, symbols->test_purchase, index, 0U, 0U, 0U)
            == CS_RESULT_PERSIST_FAILED
        && cs_call(core, symbols->test_bag_count, item, 0U, 0U, 0U) == 0U
        && cs_call(core, symbols->test_balance, currency, 0U, 0U, 0U)
            == price
        && cs_call(core, symbols->test_owner_field, 1U, 0U, 0U, 0U) == 0U
        && cs_owner_valid(core);
    return passed;
}

static bool cs_transaction_test(struct mCore *core,
                                const struct CsSymbols *symbols,
                                const struct CsCases *cases)
{
    bool passed = cs_purchase_one(
        core, symbols, CS_CURRENCY_MONEY, cases->money_index,
        cases->money_item, cases->money_price, cases->money_quantity);
    passed = passed && cs_purchase_one(
        core, symbols, CS_CURRENCY_BP, cases->bp_index,
        cases->bp_item, cases->bp_price, cases->bp_quantity);
    passed = passed && cs_purchase_one(
        core, symbols, CS_CURRENCY_RESEARCH, cases->research_index,
        cases->research_item, cases->research_price,
        cases->research_quantity);
    passed = passed
        && cs_call(core, symbols->test_initialize, 0U, 0U, 0U, 0U) == 0U
        && cs_call(core, symbols->test_set_bag, 0U, 0U, 999U, 0U) == 0U
        && cs_call(core, symbols->test_claim_relic,
                   cases->relic_index, 0U, 0U, 0U) == CS_RESULT_SUCCESS
        && cs_call(core, symbols->test_bag_count,
                   cases->relic_item, 0U, 0U, 0U) == 1U
        && cs_call(core, symbols->test_claim_relic,
                   cases->relic_index, 0U, 0U, 0U) == CS_RESULT_EFFECTLESS
        && cs_call(core, symbols->test_owner_field, 1U, 0U, 0U, 0U) == 0U;
    return passed;
}

static bool cs_form_gift_test(struct mCore *core,
                              const struct CsSymbols *symbols,
                              const struct CsCases *cases)
{
    bool passed = cs_call(core, symbols->test_initialize, 0U, 0U, 0U, 0U)
            == 0U
        && cs_call(core, symbols->test_seed_party,
                   cases->form_base, 0U, 0U, 0U) == 0U
        && cs_call(core, symbols->test_apply_form,
                   cases->form_index, 0U, 0U, 0U) == 0U
        && cs_call(core, symbols->test_party_field, 0U, 0U, 0U, 0U)
            == cases->form_target
        && cs_call(core, symbols->test_apply_form,
                   cases->form_index, 0U, 0U, 0U) == 0U
        && cs_call(core, symbols->test_party_field, 0U, 0U, 0U, 0U)
            == cases->form_base;
    passed = passed
        && cs_call(core, symbols->test_gift,
                   cases->fixed_gift_index, 0U, 0U, 0U) == 0U
        && cs_call(core, symbols->test_gift_field, 0U, 0U, 0U, 0U)
            == cases->fixed_gift_species
        && cs_call(core, symbols->test_gift,
                   cases->fixed_gift_index, 0U, 0U, 0U)
            == CS_RESULT_EFFECTLESS
        && cs_call(core, symbols->test_owner_field, 4U, 0U, 0U, 0U) != 0U;
    passed = passed
        && cs_call(core, symbols->test_gift,
                   cases->research_egg_index, 0U, 0U, 0U) == 0U
        && cs_call(core, symbols->test_gift_field, 0U, 0U, 0U, 0U)
            == cases->research_egg_species
        && cs_call(core, symbols->test_gift,
                   cases->research_egg_index, 0U, 0U, 0U) == 0U;
    return passed && cs_owner_valid(core);
}

static bool cs_gmax_toggle_test(struct mCore *core,
                                const struct CsSymbols *symbols,
                                const struct CsCases *cases)
{
    uint8_t before[CWR_MON_SIZE], after[CWR_MON_SIZE];
    bool passed = cs_call(core, symbols->test_initialize, 0U, 0U, 0U, 0U)
            == 0U
        && cs_call(core, symbols->test_seed_party,
                   cases->gmax_base, 0U, 0U, 0U) == 0U
        && cs_call(core, symbols->test_set_bag,
                   cases->dynamax_candy_item, 2U, 2U, 0U) == 0U;
    vw_read_bytes(core, ADDR_PLAYER_PARTY, before, sizeof(before));
    passed = passed
        && cs_call(core, symbols->test_toggle_gmax, 0U, 0U, 0U, 0U) == 0U;
    vw_read_bytes(core, ADDR_PLAYER_PARTY, after, sizeof(after));
    for (unsigned index = 0U; index < sizeof(before); ++index) {
        if (index != CS_GMAX_BYTE && before[index] != after[index])
            passed = false;
    }
    passed = passed
        && (after[CS_GMAX_BYTE] ^ before[CS_GMAX_BYTE]) == CS_GMAX_MASK
        && cs_call(core, symbols->test_party_field, 0U, 1U, 0U, 0U) == 1U
        && cs_call(core, symbols->test_bag_count,
                   cases->dynamax_candy_item, 0U, 0U, 0U) == 1U
        && cs_call(core, symbols->test_toggle_gmax, 0U, 0U, 0U, 0U) == 0U;
    vw_read_bytes(core, ADDR_PLAYER_PARTY, after, sizeof(after));
    return passed && !memcmp(before, after, sizeof(before))
        && cs_call(core, symbols->test_bag_count,
                   cases->dynamax_candy_item, 0U, 0U, 0U) == 0U;
}

static bool cs_vault_batch_once(struct mCore *core,
                                const struct CwrSymbols *vault,
                                const struct CbrSymbols *t27,
                                uint32_t nonce)
{
    uint8_t expected[CS_VAULT_BATCH][VW_RECORD_SIZE];
    uint8_t request[96], transfer[VW_TRANSFER_SIZE], payload[9];
    if (!vw_prepare_idle(core, vault, t27, nonce))
        return false;
    cwr_clear_boxes(core);
    for (unsigned slot = 0U; slot < CS_VAULT_BATCH; ++slot) {
        uint16_t species = slot % 3U == 0U ? 894U
            : (slot % 3U == 1U ? 154U : 742U);
        uint16_t held = (uint16_t)(13U + slot);
        cwr_create_mon(core, CWR_SCRATCH, species, 50U,
                       0x56000000U + slot);
        cwr_write16(core, CWR_SCRATCH + 0x100U, held);
        (void)cbr_call(core, VW_SET_BOX_MON_DATA, CWR_SCRATCH, 12U,
                       CWR_SCRATCH + 0x100U, 0U);
        write8(core, CWR_SCRATCH + CS_TERA_BYTE,
               (uint8_t)(1U + slot % 18U));
        if ((slot & 1U) != 0U)
            write8(core, CWR_SCRATCH + CS_GMAX_BYTE,
                   (uint8_t)(read8(core, CWR_SCRATCH + CS_GMAX_BYTE)
                             | CS_GMAX_MASK));
        (void)cbr_call(core, CWR_SET_BOX_MON, VW_BOX, slot,
                       CWR_SCRATCH, 0U);
        vw_read_bytes(core, vw_box_address(core, slot),
                      expected[slot], VW_RECORD_SIZE);
        if (cbr_call(core, CWR_GET_BOX_MON_DATA,
                     VW_BOX, slot, 11U, 0U) != species
            || cbr_call(core, CWR_GET_BOX_MON_DATA,
                        VW_BOX, slot, 12U, 0U) != held)
            return false;
    }
    for (unsigned slot = 0U; slot < CS_VAULT_BATCH; ++slot) {
        uint8_t selected = (uint8_t)slot;
        if (!cwr_send(core, vault, VW_COMMAND_EXPORT, &selected, 1U,
                      slot + 1U, request)
            || !vw_transfer_valid(core, VW_COMMAND_EXPORT, selected,
                                  nonce, transfer)
            || vw_get16(transfer, 26U) != VW_RECORD_SIZE
            || memcmp(transfer + VW_RECORD_OFFSET,
                      expected[slot], VW_RECORD_SIZE))
            return false;
    }
    cwr_clear_boxes(core);
    for (unsigned slot = 0U; slot < CS_VAULT_BATCH; ++slot) {
        uint32_t generation = 0x56010000U + slot;
        vw_build_input(transfer, (uint8_t)slot, generation,
                       nonce, expected[slot]);
        vw_write_bytes(core, VW_TRANSFER, transfer, sizeof(transfer));
        payload[0] = (uint8_t)slot;
        cbr_put32(payload, 1U, generation);
        cbr_put32(payload, 5U,
                  cbr_crc_bytes(expected[slot], VW_RECORD_SIZE));
        if (!cwr_send(core, vault, VW_COMMAND_IMPORT,
                      payload, sizeof(payload), slot + 31U, request))
            return false;
    }
    for (unsigned slot = 0U; slot < CS_VAULT_BATCH; ++slot) {
        uint8_t actual[VW_RECORD_SIZE];
        vw_read_bytes(core, vw_box_address(core, slot),
                      actual, sizeof(actual));
        if (memcmp(actual, expected[slot], sizeof(actual)))
            return false;
    }
    if (cbr_call(core, CWR_LOAD_GAME_DATA, 0U, 0U, 0U, 0U) != 1U)
        return false;
    for (unsigned slot = 0U; slot < CS_VAULT_BATCH; ++slot) {
        uint8_t actual[VW_RECORD_SIZE];
        vw_read_bytes(core, vw_box_address(core, slot),
                      actual, sizeof(actual));
        if (memcmp(actual, expected[slot], sizeof(actual)))
            return false;
    }
    return true;
}

static bool cs_raid_test(struct mCore *core,
                         const struct CsSymbols *symbols,
                         const struct CsCases *cases,
                         unsigned iterations)
{
    bool passed = true;
    for (unsigned iteration = 0U; iteration < iterations; ++iteration) {
        for (unsigned host = 0U; host < CS_HOST_COUNT; ++host) {
            passed = passed
                && cs_call(core, symbols->test_initialize,
                           0U, 0U, 0U, 0U) == 0U
                && cs_call(core, symbols->test_prepare_raid,
                           host, 0U, 0U, 0U) == CS_RESULT_RAID_REQUEST
                && cs_call(core, symbols->test_raid_field,
                           0U, 0U, 0U, 0U) == host
                && cs_call(core, symbols->start_raid,
                           0U, 0U, 0U, 0U) == CS_RESULT_BATTLE_STARTED
                && cs_call(core, symbols->test_raid_field,
                           4U, 0U, 0U, 0U) == 1U;
            if (host == cases->gmax_host)
                passed = passed
                    && cs_call(core, symbols->test_raid_field,
                               3U, 0U, 0U, 0U) == 1U
                    && (read8(core, ADDR_ENEMY_PARTY + CS_GMAX_BYTE)
                        & CS_GMAX_MASK) != 0U;
            passed = passed
                && cs_call(core, symbols->test_complete_raid,
                           0U, 0U, 0U, 0U) == 0U
                && cs_call(core, symbols->test_owner_field,
                           16U + host, 0U, 0U, 0U) == 0U;
        }
    }
    passed = passed
        && cs_call(core, symbols->test_initialize, 0U, 0U, 0U, 0U) == 0U
        && cs_call(core, symbols->test_set_bag, 0U, 0U, 999U, 0U) == 0U
        && cs_call(core, symbols->test_prepare_raid, 0U, 0U, 0U, 0U)
            == CS_RESULT_RAID_REQUEST
        && cs_call(core, symbols->start_raid, 0U, 0U, 0U, 0U)
            == CS_RESULT_BATTLE_STARTED
        && cs_call(core, symbols->test_complete_raid, 1U, 0U, 0U, 0U) == 0U
        && (cs_call(core, symbols->test_owner_field, 3U, 0U, 0U, 0U)
            & 1U) != 0U
        && cs_call(core, symbols->test_owner_field, 16U, 0U, 0U, 0U) == 1U
        && cs_call(core, symbols->test_bag_item, 0U, 0U, 0U, 0U) != 0U;
    uint32_t retry = cases->raid_retry_host;
    passed = passed
        && cs_call(core, symbols->test_initialize, 0U, 0U, 0U, 0U) == 0U
        && cs_call(core, symbols->test_set_bag, 999U, 1U, 1U, 0U) == 0U
        && cs_call(core, symbols->test_prepare_raid, retry, 0U, 0U, 0U)
            == CS_RESULT_RAID_REQUEST
        && cs_call(core, symbols->start_raid, 0U, 0U, 0U, 0U)
            == CS_RESULT_BATTLE_STARTED
        && cs_call(core, symbols->test_complete_raid, 1U, 0U, 0U, 0U)
            == CS_RESULT_BAG_FULL
        && cs_call(core, symbols->test_owner_field, 6U, 0U, 0U, 0U)
            == retry + 1U
        && cs_call(core, symbols->test_set_bag, 0U, 0U, 999U, 0U) == 0U
        && cs_call(core, symbols->test_prepare_raid, retry, 0U, 0U, 0U)
            == CS_RESULT_RAID_REQUEST
        && cs_call(core, symbols->start_raid, 0U, 0U, 0U, 0U) == 0U
        && cs_call(core, symbols->test_owner_field, 6U, 0U, 0U, 0U) == 0U
        && cs_call(core, symbols->test_owner_field,
                   16U + retry, 0U, 0U, 0U) == 1U
        && cs_owner_valid(core);
    return passed;
}

static bool cs_world_hosts_test(struct mCore *core,
                                const struct CsSymbols *symbols,
                                const struct CsCases *cases)
{
    for (unsigned host = 0U; host < CS_HOST_COUNT; ++host) {
        if (read32(core, cases->map_site[host]) != cases->map_target[host])
            return false;
        uint32_t event = cases->map_target[host];
        uint32_t count = read8(core, event + 3U);
        uint32_t bg = read32(core, event + 16U);
        if (count != cases->map_bg_count[host] || !count
            || bg < 0x08000000U || bg >= 0x0A000000U)
            return false;
        uint32_t record = bg + (count - 1U) * 12U;
        uint32_t script = read32(core, record + 8U);
        if (read16(core, record) != cases->map_x[host]
            || read16(core, record + 2U) != cases->map_y[host]
            || read8(core, record + 4U) != cases->map_elevation[host]
            || read8(core, record + 5U) != 0U
            || read16(core, record + 6U) != 0U
            || read8(core, script) != 0x6AU
            || read8(core, script + 1U) != 0x16U
            || read16(core, script + 2U) != 0x8004U
            || read16(core, script + 4U) != host
            || read8(core, script + 6U) != 0x23U
            || cwr_read32_unaligned(core, script + 7U)
                != symbols->field_host)
            return false;
    }
    return true;
}

int main(int argc, char **argv)
{
    if (argc != 6) {
        fprintf(stderr, "usage: %s ROM SYMBOLS CASES quick|full SAVE\n",
                argv[0]);
        return 2;
    }
    bool full = !strcmp(argv[4], "full");
    if (!full && strcmp(argv[4], "quick"))
        return 2;
    (void)argv[5];
    struct CsSymbols symbols = cs_load_symbols(argv[2]);
    struct CsCases cases = cs_load_cases(argv[3]);
    struct CwrSymbols vault = cwr_load_symbols(argv[2]);
    struct CbrSymbols t27 = cbr_load_symbols(argv[2]);
    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {
        .sample = NULL, .unixTime = fixed_unix_time,
        .serialize = NULL, .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core))
        cwr_die("Collection mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1]))
        cwr_die("Collection ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);
    run_trace_prefix(core);
    run_fixed_frames(core);
    struct Snapshot base = take_snapshot(core);

    bool tests[ARRAY_LEN(cs_test_names)] = {false};
    tests[0] = cs_probe_test(core, &symbols, &cases);
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
        core, &vault, &t27, full ? 0x56005002U : 0x56005001U);
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

    char rom_sha[65], runner_sha[65], symbols_sha[65], cases_sha[65];
    sha256_file(argv[1], rom_sha);
    sha256_file(argv[0], runner_sha);
    sha256_file(argv[2], symbols_sha);
    sha256_file(argv[3], cases_sha);
    printf("{\"schema_version\":1,\"task\":"
           "\"USER-20260827-COLLECTION-SUPPLY-V1-IMPLEMENTATION\","
           "\"stage\":56,\"mode\":\"%s\",\"status\":\"%s\","
           "\"result_identity\":\"CSV56:388:34:999:14:292:217:raw80x30\","
           "\"rom_sha256\":\"%s\",\"runner_sha256\":\"%s\","
           "\"symbols_sha256\":\"%s\",\"cases_sha256\":\"%s\","
           "\"tests\":{",
           argv[4], passed ? "PASS" : "FAIL", rom_sha, runner_sha,
           symbols_sha, cases_sha);
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
