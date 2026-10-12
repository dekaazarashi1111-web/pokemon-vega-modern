/*
 * USER-MODERNIZATION-FLOETTE-ETERNAL-GIFT
 *
 * A synchronous, compensating one-time gift transaction.  The legacy
 * FireRed Pokedex owns only 52-byte bitmaps, so National Dex 670 is recorded
 * in the existing canonical collection ledger instead of indexing those
 * bitmaps out of bounds.  Expanded flag 0x14CD remains the form-specific
 * source of truth.
 */

#include "modernization_floette_gift.h"

#include <stddef.h>
#include <stdint.h>

#include "../save_migration/save_migration.h"
#include "../../vendor/vega_acquisition/generated/acquisition_collection_defs.h"
#include "../../vendor/vega_acquisition/generated/acquisition_save_layout.h"

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;

#define PTR(type, address) ((type)(uintptr_t)(address))
#define FLOETTE_GIFT_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))

enum {
    FLOETTE_GIFT_PARTY_SIZE = 6,
    FLOETTE_GIFT_MON_SIZE = 100,
    FLOETTE_GIFT_BOX_COUNT = 14,
    FLOETTE_GIFT_BOX_CAPACITY = 30,
    FLOETTE_GIFT_MON_DATA_SPECIES = 11,
    FLOETTE_GIFT_MON_DATA_LEVEL = 56,
    FLOETTE_GIFT_PC_BOX_VAR = 0x4037,
    FLOETTE_GIFT_SAVE_SECTOR = 31,
    FLOETTE_GIFT_SAVE_SECTOR_DATA_SIZE = 0x0FF0,
    FLOETTE_GIFT_SAVE_SECTOR_SIZE = 0x1000,
    FLOETTE_GIFT_TOKEN_PARTY = 0x10000000,
    FLOETTE_GIFT_TOKEN_BOX = 0x20000000,
    FLOETTE_GIFT_TOKEN_KIND_MASK = 0xF0000000
};

typedef u8 (*FlagFn)(u16 flag);
typedef u8 (*BagFn)(u16 item, u16 quantity);
typedef VegaAcqPendingTransaction *(*GetPendingFn)(void);
typedef void (*FinalizeInMemoryFn)(void);
typedef void (*CreateMonFn)(void *mon, u16 species, u8 level, u8 fixed_iv,
                            u8 has_fixed_personality, u32 personality,
                            u8 ot_id_type, u32 fixed_ot_id);
typedef u8 (*GiveMonFn)(void *mon);
typedef u32 (*GetMonDataFn)(const void *mon, int field, u8 *destination);
typedef u32 (*GetBoxMonDataAtFn)(u8 box, u8 position, int field);
typedef void (*ZeroBoxMonAtFn)(u8 box, u8 position);
typedef u16 (*VarGetFn)(u16 variable);
typedef u8 (*VarSetFn)(u16 variable, u16 value);
typedef u8 (*CalculatePartyCountFn)(void);
typedef u8 (*TryWriteSectorFn)(u16 sector, const void *source);
typedef u8 (*TrySavingDataFn)(u8 save_type);

#ifdef MODERNIZATION_FLOETTE_GIFT_HOST_TEST
extern u8 FloetteGiftHost_FlagSet(u16 flag);
extern u8 FloetteGiftHost_FlagClear(u16 flag);
extern u8 FloetteGiftHost_FlagGet(u16 flag);
extern u8 FloetteGiftHost_CheckBagHasItem(u16 item, u16 quantity);
extern VegaAcqPendingTransaction *FloetteGiftHost_GetPending(void);
extern void FloetteGiftHost_FinalizeInMemory(void);
extern void FloetteGiftHost_CreateMon(void *mon, u16 species, u8 level,
                                     u8 fixed_iv, u8 has_fixed_personality,
                                     u32 personality, u8 ot_id_type,
                                     u32 fixed_ot_id);
extern u8 FloetteGiftHost_GiveMon(void *mon);
extern u32 FloetteGiftHost_GetMonData(const void *mon, int field,
                                     u8 *destination);
extern u32 FloetteGiftHost_GetBoxMonDataAt(u8 box, u8 position, int field);
extern void FloetteGiftHost_ZeroBoxMonAt(u8 box, u8 position);
extern u16 FloetteGiftHost_VarGet(u16 variable);
extern u8 FloetteGiftHost_VarSet(u16 variable, u16 value);
extern u8 FloetteGiftHost_CalculatePartyCount(void);
extern u8 FloetteGiftHost_TryWriteSector(u16 sector, const void *source);
extern u8 FloetteGiftHost_TrySavingData(u8 save_type);
extern volatile u16 gFloetteGiftHostSpecialResult;
extern u8 gFloetteGiftHostPlayerParty[FLOETTE_GIFT_PARTY_SIZE
                                      * FLOETTE_GIFT_MON_SIZE];
extern volatile u8 gFloetteGiftHostPlayerPartyCount;
extern volatile u16 gFloetteGiftHostSpecialMonBoxId;
extern volatile u16 gFloetteGiftHostSpecialMonBoxPos;
extern VegaModernSaveData gFloetteGiftHostModernSave;
extern VegaModernSaveData gFloetteGiftHostRollbackSave;
extern u8 gFloetteGiftHostTransactionScratch[256];

#undef gVegaModernSaveData
#undef gVegaSaveRollbackData
#undef gVegaSaveTransactionScratch
#define gVegaModernSaveData (&gFloetteGiftHostModernSave)
#define gVegaSaveRollbackData (&gFloetteGiftHostRollbackSave)
#define gVegaSaveTransactionScratch gFloetteGiftHostTransactionScratch
#define G_SPECIAL_RESULT (&gFloetteGiftHostSpecialResult)
#define G_PLAYER_PARTY gFloetteGiftHostPlayerParty
#define G_PLAYER_PARTY_COUNT (&gFloetteGiftHostPlayerPartyCount)
#define G_SPECIAL_MON_BOX_ID (&gFloetteGiftHostSpecialMonBoxId)
#define G_SPECIAL_MON_BOX_POS (&gFloetteGiftHostSpecialMonBoxPos)
#define FN_FLAG_SET FloetteGiftHost_FlagSet
#define FN_FLAG_CLEAR FloetteGiftHost_FlagClear
#define FN_FLAG_GET FloetteGiftHost_FlagGet
#define FN_CHECK_BAG_HAS_ITEM FloetteGiftHost_CheckBagHasItem
#define FN_ACQ_GET_PENDING FloetteGiftHost_GetPending
#define FN_ACQ_FINALIZE FloetteGiftHost_FinalizeInMemory
#define FN_CREATE_MON FloetteGiftHost_CreateMon
#define FN_GIVE_MON FloetteGiftHost_GiveMon
#define FN_GET_MON_DATA FloetteGiftHost_GetMonData
#define FN_GET_BOX_MON_DATA FloetteGiftHost_GetBoxMonDataAt
#define FN_ZERO_BOX_MON_AT FloetteGiftHost_ZeroBoxMonAt
#define FN_VAR_GET FloetteGiftHost_VarGet
#define FN_VAR_SET FloetteGiftHost_VarSet
#define FN_CALCULATE_PARTY_COUNT FloetteGiftHost_CalculatePartyCount
#define FN_TRY_WRITE_SECTOR FloetteGiftHost_TryWriteSector
#define FN_TRY_SAVING_DATA FloetteGiftHost_TrySavingData
#else
#ifndef VEGA_FLOETTE_ACQ_GET_PENDING_ADDRESS
#error "VEGA_FLOETTE_ACQ_GET_PENDING_ADDRESS is required"
#endif
#ifndef VEGA_FLOETTE_ACQ_FINALIZE_ADDRESS
#error "VEGA_FLOETTE_ACQ_FINALIZE_ADDRESS is required"
#endif
#ifndef VEGA_FLOETTE_GIVE_MON_ADDRESS
#error "VEGA_FLOETTE_GIVE_MON_ADDRESS is required"
#endif
#ifndef VEGA_FLOETTE_GET_BOX_MON_DATA_ADDRESS
#error "VEGA_FLOETTE_GET_BOX_MON_DATA_ADDRESS is required"
#endif
#ifndef VEGA_FLOETTE_ZERO_BOX_MON_AT_ADDRESS
#error "VEGA_FLOETTE_ZERO_BOX_MON_AT_ADDRESS is required"
#endif
#define G_SPECIAL_RESULT PTR(volatile u16 *, 0x02037004u)
#define G_PLAYER_PARTY PTR(u8 *, 0x020241E4u)
#define G_PLAYER_PARTY_COUNT PTR(volatile u8 *, 0x02023F89u)
#define G_SPECIAL_MON_BOX_ID PTR(volatile u16 *, 0x0203700Au)
#define G_SPECIAL_MON_BOX_POS PTR(volatile u16 *, 0x0203700Cu)
#define FN_FLAG_SET PTR(FlagFn, 0x0806DE75u)
#define FN_FLAG_CLEAR PTR(FlagFn, 0x0806DE9Du)
#define FN_FLAG_GET PTR(FlagFn, 0x0806DEC5u)
#define FN_CHECK_BAG_HAS_ITEM PTR(BagFn, 0x08099949u)
#define FN_ACQ_GET_PENDING \
    PTR(GetPendingFn, VEGA_FLOETTE_ACQ_GET_PENDING_ADDRESS)
#define FN_ACQ_FINALIZE \
    PTR(FinalizeInMemoryFn, VEGA_FLOETTE_ACQ_FINALIZE_ADDRESS)
#define FN_CREATE_MON PTR(CreateMonFn, 0x0803D1C1u)
#define FN_GIVE_MON PTR(GiveMonFn, VEGA_FLOETTE_GIVE_MON_ADDRESS)
#define FN_GET_MON_DATA PTR(GetMonDataFn, 0x0803F355u)
#define FN_GET_BOX_MON_DATA \
    PTR(GetBoxMonDataAtFn, VEGA_FLOETTE_GET_BOX_MON_DATA_ADDRESS)
#define FN_ZERO_BOX_MON_AT \
    PTR(ZeroBoxMonAtFn, VEGA_FLOETTE_ZERO_BOX_MON_AT_ADDRESS)
#define FN_VAR_GET PTR(VarGetFn, 0x0806DD5Du)
#define FN_VAR_SET PTR(VarSetFn, 0x0806DD79u)
#define FN_CALCULATE_PARTY_COUNT PTR(CalculatePartyCountFn, 0x08040331u)
#define FN_TRY_WRITE_SECTOR PTR(TryWriteSectorFn, 0x080DA9C1u)
#define FN_TRY_SAVING_DATA PTR(TrySavingDataFn, 0x080DB34Du)
#define FLOETTE_GIFT_SAVE_BUFFER PTR(u8 *, 0x020399B0u)
#define FLOETTE_GIFT_SECTOR31_IMAGE PTR(const u8 *, 0x0203CF9Cu)
#endif

_Static_assert(MODERNIZATION_FLOETTE_GIFT_COLLECTION_BIT <
                   VEGA_ACQ_COLLECTION_LEDGER_BIT_COUNT,
               "Floette collection bit is outside acquisition ledger");
_Static_assert(sizeof(VegaAcqSaveBlock) == VEGA_ACQUISITION_SAVE_BYTES,
               "acquisition save ABI changed");

static void clear_bytes(void *destination, u32 size)
{
    u8 *out = (u8 *)destination;
    u32 index;
    for (index = 0u; index < size; ++index)
        out[index] = 0u;
}

static void copy_bytes(void *destination, const void *source, u32 size)
{
    u8 *out = (u8 *)destination;
    const u8 *in = (const u8 *)source;
    u32 index;
    for (index = 0u; index < size; ++index)
        out[index] = in[index];
}

static void set_result(u16 result)
{
    *G_SPECIAL_RESULT = result;
}

static VegaAcqSaveBlock *acquisition_save_block(void)
{
    return (VegaAcqSaveBlock *)(void *)
        gVegaModernSaveData->acquisition_save_block;
}

static u8 collection_registered(void)
{
    const VegaAcqSaveBlock *block = acquisition_save_block();
    const u16 bit = MODERNIZATION_FLOETTE_GIFT_COLLECTION_BIT;
    return (u8)((block->collection_bits[bit >> 3] >> (bit & 7u)) & 1u);
}

static void set_collection_registered(void)
{
    VegaAcqSaveBlock *block = acquisition_save_block();
    const u16 bit = MODERNIZATION_FLOETTE_GIFT_COLLECTION_BIT;
    block->collection_bits[bit >> 3] |= (u8)(1u << (bit & 7u));
}

static u8 persist_standard(void)
{
    return (u8)(FN_TRY_SAVING_DATA(0u) == 1u);
}

static u8 persist_sector(void)
{
#ifdef MODERNIZATION_FLOETTE_GIFT_HOST_TEST
    return (u8)(FN_TRY_WRITE_SECTOR(FLOETTE_GIFT_SAVE_SECTOR,
                                    gVegaModernSaveData) == 1u);
#else
    clear_bytes(FLOETTE_GIFT_SAVE_BUFFER, FLOETTE_GIFT_SAVE_SECTOR_SIZE);
    copy_bytes(FLOETTE_GIFT_SAVE_BUFFER, FLOETTE_GIFT_SECTOR31_IMAGE,
               FLOETTE_GIFT_SAVE_SECTOR_DATA_SIZE);
    return (u8)(FN_TRY_WRITE_SECTOR(FLOETTE_GIFT_SAVE_SECTOR,
                                    FLOETTE_GIFT_SAVE_BUFFER) == 1u);
#endif
}

static u8 storage_available(void)
{
    u8 box;
    u8 position;
    if (*G_PLAYER_PARTY_COUNT < FLOETTE_GIFT_PARTY_SIZE)
        return 1u;
    for (box = 0u; box < FLOETTE_GIFT_BOX_COUNT; ++box) {
        for (position = 0u; position < FLOETTE_GIFT_BOX_CAPACITY;
             ++position) {
            if (FN_GET_BOX_MON_DATA(
                    box, position, FLOETTE_GIFT_MON_DATA_SPECIES) == 0u)
                return 1u;
        }
    }
    return 0u;
}

static u16 destination_species(u32 token)
{
    const u32 kind = token & FLOETTE_GIFT_TOKEN_KIND_MASK;
    if (kind == FLOETTE_GIFT_TOKEN_PARTY) {
        const u8 slot = (u8)token;
        if (slot < FLOETTE_GIFT_PARTY_SIZE) {
            return (u16)FN_GET_MON_DATA(
                G_PLAYER_PARTY + (u32)slot * FLOETTE_GIFT_MON_SIZE,
                FLOETTE_GIFT_MON_DATA_SPECIES, NULL);
        }
    } else if (kind == FLOETTE_GIFT_TOKEN_BOX) {
        const u8 box = (u8)(token >> 8);
        const u8 position = (u8)token;
        if (box < FLOETTE_GIFT_BOX_COUNT
            && position < FLOETTE_GIFT_BOX_CAPACITY) {
            return (u16)FN_GET_BOX_MON_DATA(
                box, position, FLOETTE_GIFT_MON_DATA_SPECIES);
        }
    }
    return 0u;
}

static void rollback_destination(u32 token)
{
    const u32 kind = token & FLOETTE_GIFT_TOKEN_KIND_MASK;
    if (kind == FLOETTE_GIFT_TOKEN_PARTY) {
        const u8 slot = (u8)token;
        if (slot < FLOETTE_GIFT_PARTY_SIZE) {
            clear_bytes(G_PLAYER_PARTY + (u32)slot * FLOETTE_GIFT_MON_SIZE,
                        FLOETTE_GIFT_MON_SIZE);
            *G_PLAYER_PARTY_COUNT = FN_CALCULATE_PARTY_COUNT();
        }
    } else if (kind == FLOETTE_GIFT_TOKEN_BOX) {
        const u8 box = (u8)(token >> 8);
        const u8 position = (u8)token;
        if (box < FLOETTE_GIFT_BOX_COUNT
            && position < FLOETTE_GIFT_BOX_CAPACITY)
            FN_ZERO_BOX_MON_AT(box, position);
    }
}

static u8 create_gift(void)
{
    clear_bytes(gVegaSaveTransactionScratch, FLOETTE_GIFT_MON_SIZE);
    FN_CREATE_MON(gVegaSaveTransactionScratch,
                  MODERNIZATION_FLOETTE_GIFT_SPECIES,
                  MODERNIZATION_FLOETTE_GIFT_LEVEL,
                  32u, 0u, 0u, 0u, 0u);
    return (u8)(FN_GET_MON_DATA(
                    gVegaSaveTransactionScratch,
                    FLOETTE_GIFT_MON_DATA_SPECIES, NULL)
                        == MODERNIZATION_FLOETTE_GIFT_SPECIES
                && FN_GET_MON_DATA(
                    gVegaSaveTransactionScratch,
                    FLOETTE_GIFT_MON_DATA_LEVEL, NULL)
                        == MODERNIZATION_FLOETTE_GIFT_LEVEL);
}

static u8 deliver_gift(u32 *token)
{
    const u8 party_before = *G_PLAYER_PARTY_COUNT;
    u16 previous_box = 0u;
    u8 outcome;
    if (party_before >= FLOETTE_GIFT_PARTY_SIZE) {
        previous_box = FN_VAR_GET(FLOETTE_GIFT_PC_BOX_VAR);
        (void)FN_VAR_SET(FLOETTE_GIFT_PC_BOX_VAR, 0u);
    }
    outcome = FN_GIVE_MON(gVegaSaveTransactionScratch);
    if (party_before >= FLOETTE_GIFT_PARTY_SIZE)
        (void)FN_VAR_SET(FLOETTE_GIFT_PC_BOX_VAR, previous_box);
    if (outcome == 0u && party_before < FLOETTE_GIFT_PARTY_SIZE) {
        *token = FLOETTE_GIFT_TOKEN_PARTY | party_before;
    } else if (outcome == 1u
               && *G_SPECIAL_MON_BOX_ID < FLOETTE_GIFT_BOX_COUNT
               && *G_SPECIAL_MON_BOX_POS < FLOETTE_GIFT_BOX_CAPACITY) {
        *token = FLOETTE_GIFT_TOKEN_BOX
            | ((u32)*G_SPECIAL_MON_BOX_ID << 8)
            | (u32)*G_SPECIAL_MON_BOX_POS;
    } else {
        *token = 0u;
        return 0u;
    }
    if (destination_species(*token)
            != MODERNIZATION_FLOETTE_GIFT_SPECIES) {
        rollback_destination(*token);
        *token = 0u;
        return 0u;
    }
    return 1u;
}

static u8 rollback_transaction(u32 token)
{
    (void)FN_FLAG_CLEAR(MODERNIZATION_FLOETTE_GIFT_CLAIM_FLAG);
    rollback_destination(token);
    copy_bytes(gVegaModernSaveData, gVegaSaveRollbackData,
               VEGA_SAVE_LEDGER_SIZE);
    FN_ACQ_FINALIZE();
    if (FN_FLAG_GET(MODERNIZATION_FLOETTE_GIFT_CLAIM_FLAG)
        || destination_species(token)
            == MODERNIZATION_FLOETTE_GIFT_SPECIES)
        return 0u;
    return (u8)(persist_standard() && persist_sector());
}

FLOETTE_GIFT_EXPORT(FloetteGift_Probe)
u16 FloetteGift_Probe(void)
{
    set_result(MODERNIZATION_FLOETTE_GIFT_ABI_VERSION);
    return MODERNIZATION_FLOETTE_GIFT_ABI_VERSION;
}

FLOETTE_GIFT_EXPORT(FloetteGift_IsFormObtained)
u16 FloetteGift_IsFormObtained(void)
{
    u16 result = FN_FLAG_GET(MODERNIZATION_FLOETTE_GIFT_CLAIM_FLAG) != 0u;
    set_result(result);
    return result;
}

FLOETTE_GIFT_EXPORT(FloetteGift_IsNationalDexSeen)
u16 FloetteGift_IsNationalDexSeen(void)
{
    u16 result = collection_registered() != 0u;
    set_result(result);
    return result;
}

FLOETTE_GIFT_EXPORT(FloetteGift_IsNationalDexCaught)
u16 FloetteGift_IsNationalDexCaught(void)
{
    /* The canonical collection ledger has registered/not-registered state;
     * a registered gift is both caught and seen. */
    return FloetteGift_IsNationalDexSeen();
}

FLOETTE_GIFT_EXPORT(FloetteGift_Claim)
u16 FloetteGift_Claim(void)
{
    VegaAcqPendingTransaction *pending;
    u32 token = 0u;
    u16 result;

    if (FN_FLAG_GET(MODERNIZATION_FLOETTE_GIFT_CLAIM_FLAG)) {
        result = FLOETTE_GIFT_RESULT_ALREADY_CLAIMED;
        set_result(result);
        return result;
    }
    if (!FN_CHECK_BAG_HAS_ITEM(
            MODERNIZATION_FLOETTE_GIFT_KEY_STONE_ITEM, 1u)) {
        result = FLOETTE_GIFT_RESULT_LOCKED;
        set_result(result);
        return result;
    }
    pending = FN_ACQ_GET_PENDING();
    if (pending == NULL) {
        result = FLOETTE_GIFT_RESULT_ENGINE_REJECTED;
        set_result(result);
        return result;
    }
    if (pending->magic != 0u) {
        result = FLOETTE_GIFT_RESULT_BUSY;
        set_result(result);
        return result;
    }
    if (!storage_available()) {
        result = FLOETTE_GIFT_RESULT_NO_CAPACITY;
        set_result(result);
        return result;
    }

    copy_bytes(gVegaSaveRollbackData, gVegaModernSaveData,
               VEGA_SAVE_LEDGER_SIZE);
    if (!create_gift() || !deliver_gift(&token)) {
        if (token != 0u)
            rollback_destination(token);
        result = FLOETTE_GIFT_RESULT_ENGINE_REJECTED;
        set_result(result);
        return result;
    }

    (void)FN_FLAG_SET(MODERNIZATION_FLOETTE_GIFT_CLAIM_FLAG);
    if (!FN_FLAG_GET(MODERNIZATION_FLOETTE_GIFT_CLAIM_FLAG)) {
        rollback_destination(token);
        result = FLOETTE_GIFT_RESULT_ENGINE_REJECTED;
        set_result(result);
        return result;
    }
    set_collection_registered();
    FN_ACQ_FINALIZE();

    /* Required publication order: delivery -> form flag -> standard save.
     * Sector 31 follows, making the canonical National Dex registration
     * durable.  Any failure performs and persists a compensating rollback. */
    if (!persist_standard() || !persist_sector()) {
        result = rollback_transaction(token)
            ? FLOETTE_GIFT_RESULT_PERSIST_FAILED
            : FLOETTE_GIFT_RESULT_ROLLBACK_FAILED;
        set_result(result);
        return result;
    }

    result = FLOETTE_GIFT_RESULT_SUCCESS;
    set_result(result);
    return result;
}
