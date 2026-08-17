/*
 * USER-20260818-FACTORY-REPEAT-REWARD-RUNTIME
 *
 * Chain after the Stage 28 Factory reward wrapper and connect only the two
 * ACTIVE TRIAL_REPEAT manifest rows.  The repeat reward is a coupled item/BP
 * transaction; failure never invalidates Stage 28's completed run.
 */

#include "factory_repeat_reward_runtime.h"

#include <stddef.h>
#include <stdint.h>

#include "../save_migration/save_migration.h"

#include "factory_repeat_reward_catalog_generated.h"

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;

#define PTR(type, address) ((type)(uintptr_t)(address))
#define FACTORY_REPEAT_REWARD_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))

#ifndef VEGA_FACTORY_REWARD_COMPLETE_ADDRESS
#error "VEGA_FACTORY_REWARD_COMPLETE_ADDRESS must be supplied by the Stage 28 contract"
#endif
#ifndef VEGA_FACTORY_ADD_BP_ADDRESS
#error "VEGA_FACTORY_ADD_BP_ADDRESS must be supplied by the Stage 28 contract"
#endif
#ifndef VEGA_SAVE_FINALIZE_ADDRESS
#error "VEGA_SAVE_FINALIZE_ADDRESS must be supplied by the Stage 28 contract"
#endif
#ifndef VEGA_SAVE_VALIDATE_ADDRESS
#error "VEGA_SAVE_VALIDATE_ADDRESS must be supplied by the Stage 28 contract"
#endif

enum {
    FACTORY_REPEAT_REWARD_SAVE_SECTOR = 31,
    FACTORY_REPEAT_REWARD_SAVE_SECTOR_DATA_SIZE = 0x0FF0,
    FACTORY_REPEAT_REWARD_SAVE_SECTOR_SIZE = 0x1000,
    FACTORY_REPEAT_REWARD_BASE_RESULT = 9
};

typedef u16 (*CompleteFn)(void);
typedef u16 (*RandomFn)(void);
typedef u8 (*BagFn)(u16 item, u16 quantity);
typedef u8 (*TryWriteSectorFn)(u16 sector, const void *source);
typedef u8 (*TrySavingDataFn)(u8 save_type);
typedef VegaSaveStatus (*AddBattlePointsFn)(VegaModernSaveData *data,
                                             u16 amount);
typedef void (*SaveFinalizeFn)(VegaModernSaveData *data);
typedef VegaSaveStatus (*SaveValidateFn)(const VegaModernSaveData *data,
                                          size_t available_size);

#define G_SPECIAL_RESULT PTR(volatile u16 *, 0x02037004u)
#define FN_STAGE28_COMPLETE PTR(CompleteFn, VEGA_FACTORY_REWARD_COMPLETE_ADDRESS)
#define FN_RANDOM PTR(RandomFn, 0x0804448Du)
#define FN_ADD_BAG_ITEM PTR(BagFn, 0x08099A8Du)
#define FN_REMOVE_BAG_ITEM PTR(BagFn, 0x08099BE1u)
#define FN_TRY_WRITE_SECTOR PTR(TryWriteSectorFn, 0x080DA9C1u)
#define FN_TRY_SAVING_DATA PTR(TrySavingDataFn, 0x080DB34Du)
#define FN_FACTORY_ADD_BP PTR(AddBattlePointsFn, VEGA_FACTORY_ADD_BP_ADDRESS)
#define FN_SAVE_FINALIZE PTR(SaveFinalizeFn, VEGA_SAVE_FINALIZE_ADDRESS)
#define FN_SAVE_VALIDATE PTR(SaveValidateFn, VEGA_SAVE_VALIDATE_ADDRESS)
#define FACTORY_REPEAT_REWARD_SAVE_BUFFER PTR(u8 *, 0x020399B0u)
#define FACTORY_REPEAT_REWARD_SECTOR31_IMAGE PTR(const u8 *, 0x0203CF9Cu)

_Static_assert(FACTORY_REPEAT_REWARD_COUNT == 2u,
               "manifest repeat reward count changed");
_Static_assert(FACTORY_REPEAT_REWARD_REQUIRED_CLAIM_MASK == 0x0Eu,
               "Stage 28 first-clear claim ABI changed");

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
    clear_bytes(FACTORY_REPEAT_REWARD_SAVE_BUFFER,
                FACTORY_REPEAT_REWARD_SAVE_SECTOR_SIZE);
    copy_bytes(FACTORY_REPEAT_REWARD_SAVE_BUFFER,
               FACTORY_REPEAT_REWARD_SECTOR31_IMAGE,
               FACTORY_REPEAT_REWARD_SAVE_SECTOR_DATA_SIZE);
    return (u8)(FN_TRY_WRITE_SECTOR(FACTORY_REPEAT_REWARD_SAVE_SECTOR,
                                    FACTORY_REPEAT_REWARD_SAVE_BUFFER) == 1u);
}

static u8 persist_standard_save(void)
{
    return (u8)(FN_TRY_SAVING_DATA(0u) == 1u);
}

static u8 ledger_valid(void)
{
    return (u8)(FN_SAVE_VALIDATE(gVegaModernSaveData,
                                 VEGA_SAVE_LEDGER_SIZE) == VEGA_SAVE_OK);
}

static u8 repeat_eligible_before_completion(void)
{
    if (!ledger_valid())
        return 0u;
    return (u8)((gVegaModernSaveData->factory.reward_claim_bits
                 & FACTORY_REPEAT_REWARD_REQUIRED_CLAIM_MASK)
                == FACTORY_REPEAT_REWARD_REQUIRED_CLAIM_MASK);
}

static void rollback_repeat_reward(u16 item, u16 quantity)
{
    copy_bytes(gVegaModernSaveData, gVegaSaveRollbackData,
               VEGA_SAVE_LEDGER_SIZE);
    (void)FN_REMOVE_BAG_ITEM(item, quantity);
    /* Re-persist the exact post-Stage-28 completion state. */
    (void)persist_standard_save();
    (void)persist_save_sector();
}

static void apply_repeat_reward(void)
{
    u16 roll;
    u16 item;
    u16 quantity;
    u16 battle_points;

    if (!ledger_valid())
        return;

    roll = (u16)(FN_RANDOM() % FACTORY_REPEAT_REWARD_COUNT);
    item = gFactoryRepeatRewardItemIds[roll];
    quantity = gFactoryRepeatRewardItemQuantities[roll];
    battle_points = gFactoryRepeatRewardBattlePoints[roll];

    copy_bytes(gVegaSaveRollbackData, gVegaModernSaveData,
               VEGA_SAVE_LEDGER_SIZE);
    if (!FN_ADD_BAG_ITEM(item, quantity))
        return;

    gVegaModernSaveData->factory.transaction_id++;
    if (FN_FACTORY_ADD_BP(gVegaModernSaveData, battle_points) != VEGA_SAVE_OK) {
        rollback_repeat_reward(item, quantity);
        return;
    }
    FN_SAVE_FINALIZE(gVegaModernSaveData);

    if (!persist_standard_save() || !persist_save_sector())
        rollback_repeat_reward(item, quantity);
}

FACTORY_REPEAT_REWARD_EXPORT(FactoryRepeatRewardRuntime_Probe)
u16 FactoryRepeatRewardRuntime_Probe(void)
{
    set_result(VEGA_FACTORY_REPEAT_REWARD_ABI_VERSION);
    return VEGA_FACTORY_REPEAT_REWARD_ABI_VERSION;
}

FACTORY_REPEAT_REWARD_EXPORT(FactoryRepeatRewardRuntime_Complete)
u16 FactoryRepeatRewardRuntime_Complete(void)
{
    u8 repeat_eligible = repeat_eligible_before_completion();
    u16 base_result = FN_STAGE28_COMPLETE();
    if (base_result == FACTORY_REPEAT_REWARD_BASE_RESULT && repeat_eligible)
        apply_repeat_reward();
    set_result(base_result);
    return base_result;
}
