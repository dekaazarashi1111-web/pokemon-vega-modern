/*
 * USER-20260818-FACTORY-SHINY-MEMORIAL-RUNTIME
 *
 * Chain after the Stage 30 Factory special-event wrapper and connect the
 * ACTIVE 100-streak SHINY_MEMORIAL row.  Delivery uses a write-ahead record in
 * the existing acquisition pending slot, a recognizable shiny personality,
 * and a recovery dispatch at VegaAcq_RecoverPending.  The marker scan is an
 * additional idempotency proof when a normal save outlives sector 31.
 */

#include "factory_shiny_memorial_runtime.h"

#include <stddef.h>
#include <stdint.h>

#include "../save_migration/save_migration.h"
#include "../../vendor/vega_acquisition/generated/acquisition_save_layout.h"

#include "factory_shiny_memorial_catalog_generated.h"

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;

#define PTR(type, address) ((type)(uintptr_t)(address))
#define FACTORY_SHINY_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))
#define VEGA_STRINGIFY_INNER(value) #value
#define VEGA_STRINGIFY(value) VEGA_STRINGIFY_INNER(value)

#ifndef VEGA_STAGE30_COMPLETE_ADDRESS
#error "VEGA_STAGE30_COMPLETE_ADDRESS must be supplied by Stage 30"
#endif
#ifndef VEGA_ACQ_GET_PENDING_ADDRESS
#error "VEGA_ACQ_GET_PENDING_ADDRESS must be supplied by the acquisition ABI"
#endif
#ifndef VEGA_ACQ_GET_PENDING_THUMB_LITERAL
#error "VEGA_ACQ_GET_PENDING_THUMB_LITERAL must be supplied for the trampoline"
#endif
#ifndef VEGA_ACQ_RECOVER_CONTINUATION_THUMB_LITERAL
#error "VEGA_ACQ_RECOVER_CONTINUATION_THUMB_LITERAL must be supplied for the trampoline"
#endif
#ifndef VEGA_ACQ_IS_SPECIES_REGISTERED_ADDRESS
#error "VEGA_ACQ_IS_SPECIES_REGISTERED_ADDRESS must be supplied by the acquisition ABI"
#endif
#ifndef VEGA_ACQ_SET_SPECIES_REGISTERED_ADDRESS
#error "VEGA_ACQ_SET_SPECIES_REGISTERED_ADDRESS must be supplied by the acquisition ABI"
#endif
#ifndef VEGA_ACQ_FINALIZE_IN_MEMORY_ADDRESS
#error "VEGA_ACQ_FINALIZE_IN_MEMORY_ADDRESS must be supplied by the acquisition ABI"
#endif
#ifndef VEGA_ACQ_GIVE_MON_ADDRESS
#error "VEGA_ACQ_GIVE_MON_ADDRESS must be supplied by the linked ABI"
#endif
#ifndef VEGA_ACQ_GET_BOX_MON_DATA_ADDRESS
#error "VEGA_ACQ_GET_BOX_MON_DATA_ADDRESS must be supplied by the linked ABI"
#endif
#ifndef VEGA_ACQ_ZERO_BOX_MON_AT_ADDRESS
#error "VEGA_ACQ_ZERO_BOX_MON_AT_ADDRESS must be supplied by the linked ABI"
#endif

enum {
    FACTORY_SHINY_MODE_TRIAL = 0,
    FACTORY_SHINY_BASE_RESULT = 9,
    FACTORY_SHINY_LEVEL = 50,
    FACTORY_SHINY_PARTY_SIZE = 6,
    FACTORY_SHINY_MON_SIZE = 100,
    FACTORY_SHINY_BOX_COUNT = 14,
    FACTORY_SHINY_BOX_CAPACITY = 30,
    FACTORY_SHINY_MON_DATA_PERSONALITY = 0,
    FACTORY_SHINY_MON_DATA_OT_ID = 1,
    FACTORY_SHINY_MON_DATA_SPECIES = 11,
    FACTORY_SHINY_PC_BOX_VAR = 0x4037,
    FACTORY_SHINY_SAVE_SECTOR = 31,
    FACTORY_SHINY_SAVE_SECTOR_DATA_SIZE = 0x0FF0,
    FACTORY_SHINY_SAVE_SECTOR_SIZE = 0x1000,
    FACTORY_SHINY_PENDING_INDEX_FLAG = 0x8000,
    FACTORY_SHINY_PENDING_MODE = 0xF1,
    FACTORY_SHINY_PENDING_RESERVED0 = 0x53,
    FACTORY_SHINY_PENDING_RESERVED1 = 0x31,
    FACTORY_SHINY_PHASE_PREPARED = 1,
    FACTORY_SHINY_PHASE_STAGED = 2,
    FACTORY_SHINY_PERSONALITY_PREFIX = 0xD300,
    FACTORY_SHINY_PERSONALITY_PREFIX_MASK = 0xFF00,
    FACTORY_SHINY_TOKEN_PARTY = 0x10000000,
    FACTORY_SHINY_TOKEN_BOX = 0x20000000,
    FACTORY_SHINY_TOKEN_KIND_MASK = 0xF0000000,
    FACTORY_SHINY_SAVE_BLOCK2_TRAINER_ID_OFFSET = 0x0A,
    FACTORY_SHINY_SAVE_BLOCK2_OWNED_OFFSET = 0x28,
    FACTORY_SHINY_SAVE_BLOCK2_SEEN_OFFSET = 0x5C,
    FACTORY_SHINY_SAVE_BLOCK1_SEEN1_OFFSET = 0x5F8,
    FACTORY_SHINY_SAVE_BLOCK1_SEEN2_OFFSET = 0x3A18,
    FACTORY_SHINY_DEX_SET_SEEN = 2,
    FACTORY_SHINY_DEX_SET_CAUGHT = 3,
    FACTORY_SHINY_COLLECTION_BITS = 1216
};

typedef u16 (*CompleteFn)(void);
typedef VegaAcqPendingTransaction *(*GetPendingFn)(void);
typedef u8 (*SpeciesRegisteredFn)(u16 species);
typedef u8 (*SetSpeciesRegisteredFn)(u16 species, u8 registered);
typedef u8 (*GetSetPokedexFlagFn)(u16 national, u8 operation);
typedef void (*FinalizeInMemoryFn)(void);
typedef void (*CreateMonFn)(void *mon, u16 species, u8 level, u8 fixed_iv,
                            u8 has_fixed_personality, u32 personality,
                            u8 ot_id_type, u32 fixed_ot_id);
typedef u8 (*GiveMonFn)(void *mon);
typedef u32 (*GetMonDataFn)(const void *mon, int field, u8 *destination);
typedef u32 (*GetBoxMonDataAtFn)(u8 box, u8 position, int field);
typedef void (*ZeroBoxMonAtFn)(u8 box, u8 position);
typedef u8 (*TryWriteSectorFn)(u16 sector, const void *source);
typedef u8 (*TrySavingDataFn)(u8 save_type);
typedef u16 (*RandomFn)(void);
typedef u16 (*VarGetFn)(u16 variable);
typedef u8 (*VarSetFn)(u16 variable, u16 value);
typedef u8 (*CalculatePartyCountFn)(void);

#define G_SPECIAL_RESULT PTR(volatile u16 *, 0x02037004u)
#define G_PLAYER_PARTY PTR(u8 *, 0x020241E4u)
#define G_PLAYER_PARTY_COUNT PTR(volatile u8 *, 0x02023F89u)
#define G_SPECIAL_MON_BOX_ID PTR(volatile u16 *, 0x0203700Au)
#define G_SPECIAL_MON_BOX_POS PTR(volatile u16 *, 0x0203700Cu)
#define G_SAVE_BLOCK1_PTR PTR(u8 * volatile *, 0x03005048u)
#define G_SAVE_BLOCK2_PTR PTR(u8 * volatile *, 0x0300504Cu)
#define FACTORY_SHINY_SAVE_BUFFER PTR(u8 *, 0x020399B0u)
#define FACTORY_SHINY_SECTOR31_IMAGE PTR(const u8 *, 0x0203CF9Cu)

#define FN_STAGE30_COMPLETE PTR(CompleteFn, VEGA_STAGE30_COMPLETE_ADDRESS)
#define FN_ACQ_GET_PENDING PTR(GetPendingFn, VEGA_ACQ_GET_PENDING_ADDRESS)
#define FN_ACQ_IS_REGISTERED \
    PTR(SpeciesRegisteredFn, VEGA_ACQ_IS_SPECIES_REGISTERED_ADDRESS)
#define FN_ACQ_SET_REGISTERED \
    PTR(SetSpeciesRegisteredFn, VEGA_ACQ_SET_SPECIES_REGISTERED_ADDRESS)
#define FN_ACQ_FINALIZE \
    PTR(FinalizeInMemoryFn, VEGA_ACQ_FINALIZE_IN_MEMORY_ADDRESS)
#define FN_GET_SET_DEX PTR(GetSetPokedexFlagFn, 0x08088A51u)
#define FN_CREATE_MON PTR(CreateMonFn, 0x0803D1C1u)
#define FN_GIVE_MON PTR(GiveMonFn, VEGA_ACQ_GIVE_MON_ADDRESS)
#define FN_GET_MON_DATA PTR(GetMonDataFn, 0x0803F355u)
#define FN_GET_BOX_MON_DATA \
    PTR(GetBoxMonDataAtFn, VEGA_ACQ_GET_BOX_MON_DATA_ADDRESS)
#define FN_ZERO_BOX_MON_AT \
    PTR(ZeroBoxMonAtFn, VEGA_ACQ_ZERO_BOX_MON_AT_ADDRESS)
#define FN_TRY_WRITE_SECTOR PTR(TryWriteSectorFn, 0x080DA9C1u)
#define FN_TRY_SAVING_DATA PTR(TrySavingDataFn, 0x080DB34Du)
#define FN_RANDOM PTR(RandomFn, 0x0804448Du)
#define FN_VAR_GET PTR(VarGetFn, 0x0806DD5Du)
#define FN_VAR_SET PTR(VarSetFn, 0x0806DD79u)
#define FN_CALCULATE_PARTY_COUNT PTR(CalculatePartyCountFn, 0x08040331u)

_Static_assert(FACTORY_SHINY_MEMORIAL_STREAK_THRESHOLD == 100u,
               "100-streak threshold ABI changed");
_Static_assert(FACTORY_SHINY_MEMORIAL_CLAIM_BIT == 9u,
               "100-streak claim bit ABI changed");
_Static_assert(FACTORY_SHINY_MEMORIAL_CLAIM_MASK == 0x00000200u,
               "100-streak claim mask ABI changed");
_Static_assert(FACTORY_SHINY_MEMORIAL_POOL_COUNT > 0u,
               "shiny memorial pool is empty");
_Static_assert(FACTORY_SHINY_MEMORIAL_POOL_COUNT <= 256u,
               "personality marker only encodes one byte of pool index");
_Static_assert(sizeof(VegaAcqPendingTransaction) == 20u,
               "acquisition pending ABI changed");

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

static u32 read_u32(const u8 *source)
{
    return (u32)source[0]
        | ((u32)source[1] << 8)
        | ((u32)source[2] << 16)
        | ((u32)source[3] << 24);
}

static u32 trainer_id(void)
{
    const u8 *save_block2 = *G_SAVE_BLOCK2_PTR;
    if (save_block2 == NULL)
        return 0u;
    return read_u32(save_block2 + FACTORY_SHINY_SAVE_BLOCK2_TRAINER_ID_OFFSET);
}

static void set_result(u16 result)
{
    *G_SPECIAL_RESULT = result;
}

static u8 persist_sector(void)
{
    clear_bytes(FACTORY_SHINY_SAVE_BUFFER,
                FACTORY_SHINY_SAVE_SECTOR_SIZE);
    copy_bytes(FACTORY_SHINY_SAVE_BUFFER,
               FACTORY_SHINY_SECTOR31_IMAGE,
               FACTORY_SHINY_SAVE_SECTOR_DATA_SIZE);
    return (u8)(FN_TRY_WRITE_SECTOR(FACTORY_SHINY_SAVE_SECTOR,
                                    FACTORY_SHINY_SAVE_BUFFER) == 1u);
}

static u8 persist_finalized_sector(void)
{
    FN_ACQ_FINALIZE();
    return persist_sector();
}

static u8 persist_standard(void)
{
    return (u8)(FN_TRY_SAVING_DATA(0u) == 1u);
}

static u16 pending_checksum(const VegaAcqPendingTransaction *pending)
{
    u32 token = pending->transaction_token;
    u16 value = 0x31A5u;
    value ^= pending->event_index;
    value ^= pending->species_id;
    value ^= (u16)((u16)pending->mode << 8);
    value ^= (u16)pending->phase;
    value ^= (u16)((u16)pending->reserved0 << 8);
    value ^= (u16)pending->reserved1;
    value ^= (u16)token;
    value ^= (u16)(token >> 16);
    return value;
}

static u8 pending_is_custom(const VegaAcqPendingTransaction *pending)
{
    return (u8)(pending != NULL
                && pending->magic == VEGA_ACQ_PENDING_MAGIC
                && pending->mode == FACTORY_SHINY_PENDING_MODE
                && pending->reserved0 == FACTORY_SHINY_PENDING_RESERVED0
                && pending->reserved1 == FACTORY_SHINY_PENDING_RESERVED1);
}

static u8 pending_pool_index(const VegaAcqPendingTransaction *pending,
                             u16 *pool_index)
{
    u16 encoded;
    u16 index;
    if (!pending_is_custom(pending))
        return 0u;
    encoded = pending->event_index;
    if ((encoded & FACTORY_SHINY_PENDING_INDEX_FLAG) == 0u)
        return 0u;
    index = (u16)(encoded & (u16)~FACTORY_SHINY_PENDING_INDEX_FLAG);
    if (index >= FACTORY_SHINY_MEMORIAL_POOL_COUNT
        || pending->species_id != gFactoryShinyMemorialSpecies[index])
        return 0u;
    *pool_index = index;
    return 1u;
}

static u8 pending_valid(const VegaAcqPendingTransaction *pending,
                        u16 *pool_index)
{
    if (!pending_pool_index(pending, pool_index))
        return 0u;
    if (pending->phase != FACTORY_SHINY_PHASE_PREPARED
        && pending->phase != FACTORY_SHINY_PHASE_STAGED)
        return 0u;
    return (u8)(pending->checksum == pending_checksum(pending));
}

static void prepare_pending(VegaAcqPendingTransaction *pending,
                            u16 pool_index, u16 species, u8 phase,
                            u32 token)
{
    clear_bytes(pending, sizeof(*pending));
    pending->magic = VEGA_ACQ_PENDING_MAGIC;
    pending->transaction_token = token;
    pending->event_index = (u16)(FACTORY_SHINY_PENDING_INDEX_FLAG | pool_index);
    pending->species_id = species;
    pending->mode = FACTORY_SHINY_PENDING_MODE;
    pending->phase = phase;
    pending->reserved0 = FACTORY_SHINY_PENDING_RESERVED0;
    pending->reserved1 = FACTORY_SHINY_PENDING_RESERVED1;
    pending->checksum = pending_checksum(pending);
}

static u8 eligible(void)
{
    if (!gVegaModernSaveData->league_ii_cleared)
        return 0u;
    if (gVegaModernSaveData->factory
            .current_streak[FACTORY_SHINY_MODE_TRIAL]
        < FACTORY_SHINY_MEMORIAL_STREAK_THRESHOLD)
        return 0u;
    return (u8)((gVegaModernSaveData->factory.reward_claim_bits
                 & FACTORY_SHINY_MEMORIAL_CLAIM_MASK) == 0u);
}

static u8 storage_available(void)
{
    u8 box;
    u8 position;
    if (*G_PLAYER_PARTY_COUNT < FACTORY_SHINY_PARTY_SIZE)
        return 1u;
    for (box = 0u; box < FACTORY_SHINY_BOX_COUNT; ++box) {
        for (position = 0u; position < FACTORY_SHINY_BOX_CAPACITY;
             ++position) {
            if (FN_GET_BOX_MON_DATA(
                    box, position, FACTORY_SHINY_MON_DATA_SPECIES) == 0u)
                return 1u;
        }
    }
    return 0u;
}

static u16 destination_species(u32 token)
{
    u32 kind = token & FACTORY_SHINY_TOKEN_KIND_MASK;
    if (kind == FACTORY_SHINY_TOKEN_PARTY) {
        u8 slot = (u8)token;
        if (slot < FACTORY_SHINY_PARTY_SIZE) {
            return (u16)FN_GET_MON_DATA(
                G_PLAYER_PARTY + (u32)slot * FACTORY_SHINY_MON_SIZE,
                FACTORY_SHINY_MON_DATA_SPECIES, NULL);
        }
    } else if (kind == FACTORY_SHINY_TOKEN_BOX) {
        u8 box = (u8)(token >> 8);
        u8 position = (u8)token;
        if (box < FACTORY_SHINY_BOX_COUNT
            && position < FACTORY_SHINY_BOX_CAPACITY) {
            return (u16)FN_GET_BOX_MON_DATA(
                box, position, FACTORY_SHINY_MON_DATA_SPECIES);
        }
    }
    return 0u;
}

static void rollback_destination(u32 token)
{
    u32 kind = token & FACTORY_SHINY_TOKEN_KIND_MASK;
    if (kind == FACTORY_SHINY_TOKEN_PARTY) {
        u8 slot = (u8)token;
        if (slot < FACTORY_SHINY_PARTY_SIZE) {
            clear_bytes(G_PLAYER_PARTY + (u32)slot * FACTORY_SHINY_MON_SIZE,
                        FACTORY_SHINY_MON_SIZE);
            *G_PLAYER_PARTY_COUNT = FN_CALCULATE_PARTY_COUNT();
        }
    } else if (kind == FACTORY_SHINY_TOKEN_BOX) {
        u8 box = (u8)(token >> 8);
        u8 position = (u8)token;
        if (box < FACTORY_SHINY_BOX_COUNT
            && position < FACTORY_SHINY_BOX_CAPACITY)
            FN_ZERO_BOX_MON_AT(box, position);
    }
}

static u8 marker_matches(u16 species, u32 personality, u32 ot_id,
                         u16 *pool_index)
{
    u16 high = (u16)(personality >> 16);
    u16 low = (u16)personality;
    u16 index = (u16)(high & 0x00FFu);
    u32 owner = trainer_id();
    if ((high & FACTORY_SHINY_PERSONALITY_PREFIX_MASK)
            != FACTORY_SHINY_PERSONALITY_PREFIX
        || index >= FACTORY_SHINY_MEMORIAL_POOL_COUNT
        || species != gFactoryShinyMemorialSpecies[index]
        || ot_id != owner
        || (((u16)owner ^ (u16)(owner >> 16) ^ high ^ low) >= 8u))
        return 0u;
    *pool_index = index;
    return 1u;
}

static u8 find_marker(u32 *token, u16 *pool_index, u16 *species)
{
    u8 slot;
    u8 box;
    u8 position;
    u8 party_count = *G_PLAYER_PARTY_COUNT;
    if (party_count > FACTORY_SHINY_PARTY_SIZE)
        party_count = FACTORY_SHINY_PARTY_SIZE;
    for (slot = 0u; slot < party_count; ++slot) {
        const u8 *mon = G_PLAYER_PARTY + (u32)slot * FACTORY_SHINY_MON_SIZE;
        u16 found_species = (u16)FN_GET_MON_DATA(
            mon, FACTORY_SHINY_MON_DATA_SPECIES, NULL);
        u32 personality = FN_GET_MON_DATA(
            mon, FACTORY_SHINY_MON_DATA_PERSONALITY, NULL);
        u32 ot_id = FN_GET_MON_DATA(mon, FACTORY_SHINY_MON_DATA_OT_ID, NULL);
        if (marker_matches(found_species, personality, ot_id, pool_index)) {
            *token = FACTORY_SHINY_TOKEN_PARTY | slot;
            *species = found_species;
            return 1u;
        }
    }
    for (box = 0u; box < FACTORY_SHINY_BOX_COUNT; ++box) {
        for (position = 0u; position < FACTORY_SHINY_BOX_CAPACITY;
             ++position) {
            u16 found_species = (u16)FN_GET_BOX_MON_DATA(
                box, position, FACTORY_SHINY_MON_DATA_SPECIES);
            u32 personality;
            u32 ot_id;
            if (found_species == 0u)
                continue;
            personality = FN_GET_BOX_MON_DATA(
                box, position, FACTORY_SHINY_MON_DATA_PERSONALITY);
            ot_id = FN_GET_BOX_MON_DATA(
                box, position, FACTORY_SHINY_MON_DATA_OT_ID);
            if (marker_matches(found_species, personality, ot_id, pool_index)) {
                *token = FACTORY_SHINY_TOKEN_BOX
                    | ((u32)box << 8) | position;
                *species = found_species;
                return 1u;
            }
        }
    }
    return 0u;
}

static u8 create_shiny(u16 pool_index, u16 species)
{
    u8 *mon = gVegaSaveTransactionScratch;
    u32 owner = trainer_id();
    u16 high = (u16)(FACTORY_SHINY_PERSONALITY_PREFIX | pool_index);
    u16 low = (u16)owner ^ (u16)(owner >> 16) ^ high;
    u32 personality = ((u32)high << 16) | low;
    clear_bytes(mon, FACTORY_SHINY_MON_SIZE);
    FN_CREATE_MON(mon, species, FACTORY_SHINY_LEVEL, 32u, 1u,
                  personality, 0u, 0u);
    return (u8)(FN_GET_MON_DATA(mon, FACTORY_SHINY_MON_DATA_SPECIES, NULL)
                    == species
                && FN_GET_MON_DATA(mon, FACTORY_SHINY_MON_DATA_PERSONALITY, NULL)
                    == personality
                && FN_GET_MON_DATA(mon, FACTORY_SHINY_MON_DATA_OT_ID, NULL)
                    == owner);
}

static u8 deliver_shiny(u16 species, u32 *token)
{
    u8 party_before = *G_PLAYER_PARTY_COUNT;
    u16 previous_box = 0u;
    u8 outcome;
    if (party_before >= FACTORY_SHINY_PARTY_SIZE) {
        previous_box = FN_VAR_GET(FACTORY_SHINY_PC_BOX_VAR);
        (void)FN_VAR_SET(FACTORY_SHINY_PC_BOX_VAR, 0u);
    }
    outcome = FN_GIVE_MON(gVegaSaveTransactionScratch);
    if (party_before >= FACTORY_SHINY_PARTY_SIZE)
        (void)FN_VAR_SET(FACTORY_SHINY_PC_BOX_VAR, previous_box);
    if (outcome == 0u && party_before < FACTORY_SHINY_PARTY_SIZE) {
        *token = FACTORY_SHINY_TOKEN_PARTY | party_before;
    } else if (outcome == 1u
               && *G_SPECIAL_MON_BOX_ID < FACTORY_SHINY_BOX_COUNT
               && *G_SPECIAL_MON_BOX_POS < FACTORY_SHINY_BOX_CAPACITY) {
        *token = FACTORY_SHINY_TOKEN_BOX
            | ((u32)*G_SPECIAL_MON_BOX_ID << 8)
            | (u32)*G_SPECIAL_MON_BOX_POS;
    } else {
        *token = 0u;
        return 0u;
    }
    if (destination_species(*token) != species) {
        rollback_destination(*token);
        *token = 0u;
        return 0u;
    }
    return 1u;
}

static VegaAcqSaveBlock *acquisition_save_block(void)
{
    return (VegaAcqSaveBlock *)(void *)
        gVegaModernSaveData->acquisition_save_block;
}

static void set_collection_bit(u16 bit, u8 value)
{
    VegaAcqSaveBlock *block = acquisition_save_block();
    u8 mask = (u8)(1u << (bit & 7u));
    if (value)
        block->collection_bits[bit >> 3] |= mask;
    else
        block->collection_bits[bit >> 3] &= (u8)~mask;
}

static u8 register_memorial(u16 pool_index, u16 national)
{
    u16 ledger_bit = gFactoryShinyMemorialLedgerBits[pool_index];
    if (ledger_bit >= FACTORY_SHINY_COLLECTION_BITS
        || national == 0u || national > 386u)
        return 0u;
    set_collection_bit(ledger_bit, 1u);
    (void)FN_GET_SET_DEX(national, FACTORY_SHINY_DEX_SET_SEEN);
    (void)FN_GET_SET_DEX(national, FACTORY_SHINY_DEX_SET_CAUGHT);
    return 1u;
}

typedef struct DexSnapshot {
    u8 *owned;
    u8 *seen0;
    u8 *seen1;
    u8 *seen2;
    u8 owned_value;
    u8 seen0_value;
    u8 seen1_value;
    u8 seen2_value;
} DexSnapshot;

static u8 snapshot_dex(u16 national, DexSnapshot *snapshot)
{
    u8 *save_block1 = *G_SAVE_BLOCK1_PTR;
    u8 *save_block2 = *G_SAVE_BLOCK2_PTR;
    u16 byte_index;
    if (national == 0u || national > 386u
        || save_block1 == NULL || save_block2 == NULL)
        return 0u;
    byte_index = (u16)((national - 1u) >> 3);
    snapshot->owned = save_block2
        + FACTORY_SHINY_SAVE_BLOCK2_OWNED_OFFSET + byte_index;
    snapshot->seen0 = save_block2
        + FACTORY_SHINY_SAVE_BLOCK2_SEEN_OFFSET + byte_index;
    snapshot->seen1 = save_block1
        + FACTORY_SHINY_SAVE_BLOCK1_SEEN1_OFFSET + byte_index;
    snapshot->seen2 = save_block1
        + FACTORY_SHINY_SAVE_BLOCK1_SEEN2_OFFSET + byte_index;
    snapshot->owned_value = *snapshot->owned;
    snapshot->seen0_value = *snapshot->seen0;
    snapshot->seen1_value = *snapshot->seen1;
    snapshot->seen2_value = *snapshot->seen2;
    return 1u;
}

static void restore_dex(const DexSnapshot *snapshot)
{
    *snapshot->owned = snapshot->owned_value;
    *snapshot->seen0 = snapshot->seen0_value;
    *snapshot->seen1 = snapshot->seen1_value;
    *snapshot->seen2 = snapshot->seen2_value;
}

static u16 commit_staged(VegaAcqPendingTransaction *pending,
                         u16 pool_index, u16 species, u32 token,
                         u16 success_result)
{
    DexSnapshot dex;
    u16 national = gFactoryShinyMemorialNational[pool_index];
    if (destination_species(token) != species
        || !snapshot_dex(national, &dex))
        return VEGA_FACTORY_SHINY_MEMORIAL_ENGINE_REJECTED;

    copy_bytes(gVegaSaveRollbackData, gVegaModernSaveData,
               VEGA_SAVE_LEDGER_SIZE);
    if (!register_memorial(pool_index, national))
        return VEGA_FACTORY_SHINY_MEMORIAL_ENGINE_REJECTED;
    gVegaModernSaveData->factory.reward_claim_bits |=
        FACTORY_SHINY_MEMORIAL_CLAIM_MASK;
    gVegaModernSaveData->factory.transaction_id++;
    clear_bytes(pending, sizeof(*pending));
    FN_ACQ_FINALIZE();

    if (!persist_standard()) {
        copy_bytes(gVegaModernSaveData, gVegaSaveRollbackData,
                   VEGA_SAVE_LEDGER_SIZE);
        restore_dex(&dex);
        (void)persist_finalized_sector();
        return VEGA_FACTORY_SHINY_MEMORIAL_PERSIST_FAILED;
    }
    if (!persist_sector()) {
        copy_bytes(gVegaModernSaveData, gVegaSaveRollbackData,
                   VEGA_SAVE_LEDGER_SIZE);
        (void)persist_finalized_sector();
        return VEGA_FACTORY_SHINY_MEMORIAL_PERSIST_FAILED;
    }
    return success_result;
}

static u16 clear_pending_for_retry(VegaAcqPendingTransaction *pending,
                                   u16 result)
{
    clear_bytes(pending, sizeof(*pending));
    if (!persist_finalized_sector())
        return VEGA_FACTORY_SHINY_MEMORIAL_PERSIST_FAILED;
    return result;
}

static u16 recover_custom(VegaAcqPendingTransaction *pending)
{
    u16 pool_index = 0u;
    u16 species;
    u32 token;
    if (!pending_valid(pending, &pool_index))
        return clear_pending_for_retry(
            pending, VEGA_FACTORY_SHINY_MEMORIAL_CORRUPT_PENDING);
    species = pending->species_id;
    token = pending->transaction_token;
    if (pending->phase == FACTORY_SHINY_PHASE_PREPARED)
        return clear_pending_for_retry(
            pending, VEGA_FACTORY_SHINY_MEMORIAL_RECOVERED_RETRY);
    if (destination_species(token) != species)
        return clear_pending_for_retry(
            pending, VEGA_FACTORY_SHINY_MEMORIAL_RECOVERED_RETRY);
    return commit_staged(pending, pool_index, species, token,
                         VEGA_FACTORY_SHINY_MEMORIAL_RECOVERED_COMMIT);
}

/* Reproduce the eight overwritten bytes of VegaAcq_RecoverPending, then enter
 * its original body at +8.  The original epilogue returns to our caller. */
__attribute__((naked, noinline, used))
static u16 call_original_recover(void)
{
    __asm__ volatile(
        "push {r4, r5, r6, r7, lr}\n"
        "sub sp, #28\n"
        "ldr r3, 1f\n"
        "bl 2f\n"
        "ldr r3, 3f\n"
        "bx r3\n"
        "2:\n"
        "bx r3\n"
        ".align 2\n"
        "1:\n"
        ".word " VEGA_STRINGIFY(VEGA_ACQ_GET_PENDING_THUMB_LITERAL) "\n"
        "3:\n"
        ".word " VEGA_STRINGIFY(VEGA_ACQ_RECOVER_CONTINUATION_THUMB_LITERAL) "\n");
}

FACTORY_SHINY_EXPORT(FactoryShinyMemorialRuntime_RecoverDispatch)
u16 FactoryShinyMemorialRuntime_RecoverDispatch(void)
{
    VegaAcqPendingTransaction *pending = FN_ACQ_GET_PENDING();
    if (pending_is_custom(pending))
        return recover_custom(pending);
    return call_original_recover();
}

FACTORY_SHINY_EXPORT(FactoryShinyMemorialRuntime_ClaimPending)
u16 FactoryShinyMemorialRuntime_ClaimPending(void)
{
    VegaAcqPendingTransaction *pending = FN_ACQ_GET_PENDING();
    VegaAcqPendingTransaction prepared;
    u16 pool_index;
    u16 species;
    u32 token;
    u16 result;

    if (pending == NULL) {
        result = VEGA_FACTORY_SHINY_MEMORIAL_ENGINE_REJECTED;
        set_result(result);
        return result;
    }
    if (pending_is_custom(pending)) {
        result = recover_custom(pending);
        if (result != VEGA_FACTORY_SHINY_MEMORIAL_RECOVERED_RETRY) {
            set_result(result);
            return result;
        }
    } else if (pending->magic != 0u) {
        result = VEGA_FACTORY_SHINY_MEMORIAL_BUSY;
        set_result(result);
        return result;
    }
    if (!eligible()) {
        result = VEGA_FACTORY_SHINY_MEMORIAL_NOT_ELIGIBLE;
        set_result(result);
        return result;
    }

    if (find_marker(&token, &pool_index, &species)) {
        prepare_pending(pending, pool_index, species,
                        FACTORY_SHINY_PHASE_STAGED, token);
        if (!persist_finalized_sector()) {
            clear_bytes(pending, sizeof(*pending));
            FN_ACQ_FINALIZE();
            result = VEGA_FACTORY_SHINY_MEMORIAL_PERSIST_FAILED;
        } else {
            result = commit_staged(
                pending, pool_index, species, token,
                VEGA_FACTORY_SHINY_MEMORIAL_RECOVERED_COMMIT);
        }
        set_result(result);
        return result;
    }
    if (!storage_available()) {
        result = VEGA_FACTORY_SHINY_MEMORIAL_NO_CAPACITY;
        set_result(result);
        return result;
    }

    pool_index = (u16)(((u32)FN_RANDOM()
                        * FACTORY_SHINY_MEMORIAL_POOL_COUNT) >> 16);
    species = gFactoryShinyMemorialSpecies[pool_index];
    prepare_pending(pending, pool_index, species,
                    FACTORY_SHINY_PHASE_PREPARED, 0u);
    if (!persist_finalized_sector()) {
        clear_bytes(pending, sizeof(*pending));
        FN_ACQ_FINALIZE();
        result = VEGA_FACTORY_SHINY_MEMORIAL_PERSIST_FAILED;
        set_result(result);
        return result;
    }
    prepared = *pending;
    if (!create_shiny(pool_index, species)
        || !deliver_shiny(species, &token)) {
        *pending = prepared;
        result = clear_pending_for_retry(
            pending, VEGA_FACTORY_SHINY_MEMORIAL_ENGINE_REJECTED);
        set_result(result);
        return result;
    }

    prepare_pending(pending, pool_index, species,
                    FACTORY_SHINY_PHASE_STAGED, token);
    if (!persist_finalized_sector()) {
        rollback_destination(token);
        *pending = prepared;
        FN_ACQ_FINALIZE();
        result = VEGA_FACTORY_SHINY_MEMORIAL_PERSIST_FAILED;
        set_result(result);
        return result;
    }
    if (!persist_standard() || !persist_finalized_sector()) {
        /* Keep the marker mon and STAGED journal in RAM.  A later call either
         * verifies the token or reconstructs it by scanning party/PC. */
        result = VEGA_FACTORY_SHINY_MEMORIAL_PERSIST_FAILED;
        set_result(result);
        return result;
    }

    result = commit_staged(pending, pool_index, species, token,
                           VEGA_FACTORY_SHINY_MEMORIAL_CLAIMED);
    set_result(result);
    return result;
}

FACTORY_SHINY_EXPORT(FactoryShinyMemorialRuntime_Probe)
u16 FactoryShinyMemorialRuntime_Probe(void)
{
    set_result(VEGA_FACTORY_SHINY_MEMORIAL_ABI_VERSION);
    return VEGA_FACTORY_SHINY_MEMORIAL_ABI_VERSION;
}

FACTORY_SHINY_EXPORT(FactoryShinyMemorialRuntime_Complete)
u16 FactoryShinyMemorialRuntime_Complete(void)
{
    u16 base_result = FN_STAGE30_COMPLETE();
    if (base_result == FACTORY_SHINY_BASE_RESULT)
        (void)FactoryShinyMemorialRuntime_ClaimPending();
    set_result(base_result);
    return base_result;
}
