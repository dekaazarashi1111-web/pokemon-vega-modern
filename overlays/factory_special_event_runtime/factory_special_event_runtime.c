/*
 * USER-20260818-FACTORY-SPECIAL-EVENT-RUNTIME
 *
 * Chain after the Stage 29 Factory repeat-reward wrapper and connect the
 * ACTIVE 49-streak SPECIAL_EVENT row as a one-time Factory Master claim key.
 * Stage 29 owns the completed run, party restore, base/bonus BP, items, and
 * pre-existing claim persistence; this wrapper only appends claim bit 8.
 */

#include "factory_special_event_runtime.h"

#include <stddef.h>
#include <stdint.h>

#include "../save_migration/save_migration.h"

#include "factory_special_event_catalog_generated.h"

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;

#define PTR(type, address) ((type)(uintptr_t)(address))
#define FACTORY_SPECIAL_EVENT_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))

#ifndef VEGA_FACTORY_REPEAT_REWARD_COMPLETE_ADDRESS
#error "VEGA_FACTORY_REPEAT_REWARD_COMPLETE_ADDRESS must be supplied by Stage 29"
#endif
#ifndef VEGA_SAVE_FINALIZE_ADDRESS
#error "VEGA_SAVE_FINALIZE_ADDRESS must be supplied by the save ABI contract"
#endif
#ifndef VEGA_SAVE_VALIDATE_ADDRESS
#error "VEGA_SAVE_VALIDATE_ADDRESS must be supplied by the save ABI contract"
#endif

enum {
    FACTORY_SPECIAL_EVENT_SAVE_SECTOR = 31,
    FACTORY_SPECIAL_EVENT_SAVE_SECTOR_DATA_SIZE = 0x0FF0,
    FACTORY_SPECIAL_EVENT_SAVE_SECTOR_SIZE = 0x1000,
    FACTORY_SPECIAL_EVENT_BASE_RESULT = 9,
    FACTORY_SPECIAL_EVENT_MODE_TRIAL = 0
};

typedef u16 (*CompleteFn)(void);
typedef u8 (*TryWriteSectorFn)(u16 sector, const void *source);
typedef void (*SaveFinalizeFn)(VegaModernSaveData *data);
typedef VegaSaveStatus (*SaveValidateFn)(const VegaModernSaveData *data,
                                          size_t available_size);

#define G_SPECIAL_RESULT PTR(volatile u16 *, 0x02037004u)
#define FN_STAGE29_COMPLETE \
    PTR(CompleteFn, VEGA_FACTORY_REPEAT_REWARD_COMPLETE_ADDRESS)
#define FN_TRY_WRITE_SECTOR PTR(TryWriteSectorFn, 0x080DA9C1u)
#define FN_SAVE_FINALIZE PTR(SaveFinalizeFn, VEGA_SAVE_FINALIZE_ADDRESS)
#define FN_SAVE_VALIDATE PTR(SaveValidateFn, VEGA_SAVE_VALIDATE_ADDRESS)
#define FACTORY_SPECIAL_EVENT_SAVE_BUFFER PTR(u8 *, 0x020399B0u)
#define FACTORY_SPECIAL_EVENT_SECTOR31_IMAGE PTR(const u8 *, 0x0203CF9Cu)

_Static_assert(FACTORY_SPECIAL_EVENT_STREAK_THRESHOLD == 49u,
               "49-streak event threshold ABI changed");
_Static_assert(FACTORY_SPECIAL_EVENT_CLAIM_BIT == 8u,
               "49-streak event claim bit ABI changed");
_Static_assert(FACTORY_SPECIAL_EVENT_CLAIM_MASK == 0x00000100u,
               "49-streak event claim mask ABI changed");

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
    clear_bytes(FACTORY_SPECIAL_EVENT_SAVE_BUFFER,
                FACTORY_SPECIAL_EVENT_SAVE_SECTOR_SIZE);
    copy_bytes(FACTORY_SPECIAL_EVENT_SAVE_BUFFER,
               FACTORY_SPECIAL_EVENT_SECTOR31_IMAGE,
               FACTORY_SPECIAL_EVENT_SAVE_SECTOR_DATA_SIZE);
    return (u8)(FN_TRY_WRITE_SECTOR(FACTORY_SPECIAL_EVENT_SAVE_SECTOR,
                                    FACTORY_SPECIAL_EVENT_SAVE_BUFFER) == 1u);
}

static u8 ledger_valid(void)
{
    return (u8)(FN_SAVE_VALIDATE(gVegaModernSaveData,
                                 VEGA_SAVE_LEDGER_SIZE) == VEGA_SAVE_OK);
}

static u8 special_event_pending(void)
{
    if (!ledger_valid())
        return 0u;
    if (!gVegaModernSaveData->league_ii_cleared)
        return 0u;
    if (gVegaModernSaveData->factory
            .current_streak[FACTORY_SPECIAL_EVENT_MODE_TRIAL]
        < FACTORY_SPECIAL_EVENT_STREAK_THRESHOLD)
        return 0u;
    return (u8)((gVegaModernSaveData->factory.reward_claim_bits
                 & FACTORY_SPECIAL_EVENT_CLAIM_MASK) == 0u);
}

static void rollback_special_event(void)
{
    copy_bytes(gVegaModernSaveData, gVegaSaveRollbackData,
               VEGA_SAVE_LEDGER_SIZE);
    /* The snapshot is the exact finalized post-Stage-29 ledger. */
    (void)persist_save_sector();
}

static void apply_special_event_claim(void)
{
    if (!special_event_pending())
        return;

    copy_bytes(gVegaSaveRollbackData, gVegaModernSaveData,
               VEGA_SAVE_LEDGER_SIZE);
    gVegaModernSaveData->factory.reward_claim_bits |=
        FACTORY_SPECIAL_EVENT_CLAIM_MASK;
    gVegaModernSaveData->factory.transaction_id++;
    FN_SAVE_FINALIZE(gVegaModernSaveData);

    if (!persist_save_sector())
        rollback_special_event();
}

FACTORY_SPECIAL_EVENT_EXPORT(FactorySpecialEventRuntime_Probe)
u16 FactorySpecialEventRuntime_Probe(void)
{
    set_result(VEGA_FACTORY_SPECIAL_EVENT_ABI_VERSION);
    return VEGA_FACTORY_SPECIAL_EVENT_ABI_VERSION;
}

FACTORY_SPECIAL_EVENT_EXPORT(FactorySpecialEventRuntime_Complete)
u16 FactorySpecialEventRuntime_Complete(void)
{
    u16 base_result = FN_STAGE29_COMPLETE();
    if (base_result == FACTORY_SPECIAL_EVENT_BASE_RESULT)
        apply_special_event_claim();
    set_result(base_result);
    return base_result;
}
