/*
 * USER-20260818-FACTORY-REWARD-RUNTIME
 *
 * Preserve the established Trial completion path (party restore, streak,
 * base 9 BP) and append the ACTIVE manifest first-clear / streak rewards as
 * a compensating transaction.  A full bag never invalidates a completed run:
 * the bonus claim remains unset and is retried on a later successful clear.
 */

#include "factory_reward_runtime.h"

#include <stddef.h>
#include <stdint.h>

#include "../save_migration/save_migration.h"

#include "factory_reward_catalog_generated.h"

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;

#define PTR(type, address) ((type)(uintptr_t)(address))
#define FACTORY_REWARD_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))

#ifndef VEGA_FACILITY_COMPLETE_ADDRESS
#error "VEGA_FACILITY_COMPLETE_ADDRESS must be supplied by the stage20 contract"
#endif

enum {
    FACTORY_REWARD_SAVE_SECTOR = 31,
    FACTORY_REWARD_SAVE_SECTOR_DATA_SIZE = 0x0FF0,
    FACTORY_REWARD_SAVE_SECTOR_SIZE = 0x1000,
    FACTORY_REWARD_BASE_RESULT = 9,
    FACTORY_REWARD_MODE_TRIAL = 0
};

typedef void (*VoidFn)(void);
typedef u8 (*BagFn)(u16 item, u16 quantity);
typedef u8 (*TryWriteSectorFn)(u16 sector, const void *source);
typedef u8 (*TrySavingDataFn)(u8 save_type);

#define G_SPECIAL_RESULT PTR(volatile u16 *, 0x02037004u)
#define FN_OLD_FACILITY_COMPLETE \
    PTR(VoidFn, VEGA_FACILITY_COMPLETE_ADDRESS)
#define FN_ADD_BAG_ITEM PTR(BagFn, 0x08099A8Du)
#define FN_REMOVE_BAG_ITEM PTR(BagFn, 0x08099BE1u)
#define FN_TRY_WRITE_SECTOR PTR(TryWriteSectorFn, 0x080DA9C1u)
#define FN_TRY_SAVING_DATA PTR(TrySavingDataFn, 0x080DB34Du)
#define FACTORY_REWARD_SAVE_BUFFER PTR(u8 *, 0x020399B0u)
#define FACTORY_REWARD_SECTOR31_IMAGE PTR(const u8 *, 0x0203CF9Cu)

_Static_assert(FACTORY_REWARD_STREAK_COUNT == 4u,
               "manifest streak reward count changed");
_Static_assert(FACTORY_REWARD_FIRST_CLAIM_MASK == 0x0Eu,
               "first-clear claim ABI changed");

static void copy_bytes(void *destination, const void *source, u32 size)
{
    u8 *out = (u8 *)destination;
    const u8 *in = (const u8 *)source;
    u32 index;
    for (index = 0u; index < size; ++index)
        out[index] = in[index];
}

static void clear_bytes(void *destination, u32 size)
{
    u8 *out = (u8 *)destination;
    u32 index;
    for (index = 0u; index < size; ++index)
        out[index] = 0u;
}

static void set_result(u16 result)
{
    *G_SPECIAL_RESULT = result;
}

static u8 persist_save_sector(void)
{
    clear_bytes(FACTORY_REWARD_SAVE_BUFFER, FACTORY_REWARD_SAVE_SECTOR_SIZE);
    copy_bytes(FACTORY_REWARD_SAVE_BUFFER, FACTORY_REWARD_SECTOR31_IMAGE,
               FACTORY_REWARD_SAVE_SECTOR_DATA_SIZE);
    return (u8)(FN_TRY_WRITE_SECTOR(FACTORY_REWARD_SAVE_SECTOR,
                                    FACTORY_REWARD_SAVE_BUFFER) == 1u);
}

static u8 persist_standard_save(void)
{
    return (u8)(FN_TRY_SAVING_DATA(0u) == 1u);
}

static u8 ledger_valid(void)
{
    return (u8)(VegaSaveValidate(gVegaModernSaveData,
                                 VEGA_SAVE_LEDGER_SIZE) == VEGA_SAVE_OK);
}

static u8 claim_is_set(u8 bit)
{
    return (u8)((gVegaModernSaveData->factory.reward_claim_bits
                 & (1u << bit)) != 0u);
}

static void set_claim(u8 bit)
{
    gVegaModernSaveData->factory.reward_claim_bits |= 1u << bit;
}

static u8 first_bonus_pending(void)
{
    return (u8)((gVegaModernSaveData->factory.reward_claim_bits
                 & FACTORY_REWARD_FIRST_CLAIM_MASK)
                != FACTORY_REWARD_FIRST_CLAIM_MASK);
}

static u8 collect_due_streaks(u8 due[FACTORY_REWARD_STREAK_COUNT])
{
    u16 streak = gVegaModernSaveData->factory
        .current_streak[FACTORY_REWARD_MODE_TRIAL];
    u8 count = 0u;
    u8 index;
    for (index = 0u; index < FACTORY_REWARD_STREAK_COUNT; ++index) {
        due[index] = (u8)(streak >= gFactoryRewardStreakThresholds[index]
                          && !claim_is_set(gFactoryRewardStreakClaimBits[index]));
        count = (u8)(count + due[index]);
    }
    return count;
}

static void add_due_streaks(const u8 due[FACTORY_REWARD_STREAK_COUNT])
{
    u8 index;
    for (index = 0u; index < FACTORY_REWARD_STREAK_COUNT; ++index) {
        u8 kind;
        if (!due[index])
            continue;
        kind = gFactoryRewardStreakCreditKinds[index];
        if (gVegaModernSaveData->encounter_credits[kind] != UINT16_MAX)
            ++gVegaModernSaveData->encounter_credits[kind];
        set_claim(gFactoryRewardStreakClaimBits[index]);
    }
}

static void rollback_bonus(u8 added_xs, u8 added_s)
{
    copy_bytes(gVegaModernSaveData, gVegaSaveRollbackData,
               VEGA_SAVE_LEDGER_SIZE);
    if (added_s)
        (void)FN_REMOVE_BAG_ITEM(FACTORY_REWARD_ITEM_EXP_CANDY_S,
                                 FACTORY_REWARD_ITEM_EXP_CANDY_S_QUANTITY);
    if (added_xs)
        (void)FN_REMOVE_BAG_ITEM(FACTORY_REWARD_ITEM_EXP_CANDY_XS,
                                 FACTORY_REWARD_ITEM_EXP_CANDY_XS_QUANTITY);
    /* Best-effort compensation rewrites both durable owners to the exact
     * post-base-completion snapshot.  The completed run itself remains valid. */
    (void)persist_standard_save();
    (void)persist_save_sector();
}

static void apply_manifest_bonus(void)
{
    u8 due[FACTORY_REWARD_STREAK_COUNT];
    u8 first;
    u8 due_count;
    u8 added_xs = 0u;
    u8 added_s = 0u;

    if (!ledger_valid())
        return;
    first = first_bonus_pending();
    due_count = collect_due_streaks(due);
    if (!first && due_count == 0u)
        return;

    copy_bytes(gVegaSaveRollbackData, gVegaModernSaveData,
               VEGA_SAVE_LEDGER_SIZE);

    if (first) {
        if (!FN_ADD_BAG_ITEM(FACTORY_REWARD_ITEM_EXP_CANDY_XS,
                             FACTORY_REWARD_ITEM_EXP_CANDY_XS_QUANTITY))
            return;
        added_xs = 1u;
        if (!FN_ADD_BAG_ITEM(FACTORY_REWARD_ITEM_EXP_CANDY_S,
                             FACTORY_REWARD_ITEM_EXP_CANDY_S_QUANTITY)) {
            (void)FN_REMOVE_BAG_ITEM(FACTORY_REWARD_ITEM_EXP_CANDY_XS,
                                     FACTORY_REWARD_ITEM_EXP_CANDY_XS_QUANTITY);
            return;
        }
        added_s = 1u;
        (void)VegaFactoryAddBattlePoints(gVegaModernSaveData,
                                         FACTORY_REWARD_FIRST_BP);
        set_claim(FACTORY_REWARD_FIRST_XS_CLAIM_BIT);
        set_claim(FACTORY_REWARD_FIRST_S_CLAIM_BIT);
        set_claim(FACTORY_REWARD_FIRST_BP_CLAIM_BIT);
    }
    add_due_streaks(due);
    gVegaModernSaveData->factory.transaction_id++;
    VegaSaveFinalize(gVegaModernSaveData);

    if (!persist_standard_save() || !persist_save_sector())
        rollback_bonus(added_xs, added_s);
}

FACTORY_REWARD_EXPORT(FactoryRewardRuntime_Probe)
u16 FactoryRewardRuntime_Probe(void)
{
    set_result(VEGA_FACTORY_REWARD_ABI_VERSION);
    return VEGA_FACTORY_REWARD_ABI_VERSION;
}

FACTORY_REWARD_EXPORT(FactoryRewardRuntime_Complete)
u16 FactoryRewardRuntime_Complete(void)
{
    u16 base_result;
    FN_OLD_FACILITY_COMPLETE();
    base_result = *G_SPECIAL_RESULT;
    if (base_result == FACTORY_REWARD_BASE_RESULT)
        apply_manifest_bonus();
    set_result(base_result);
    return base_result;
}
