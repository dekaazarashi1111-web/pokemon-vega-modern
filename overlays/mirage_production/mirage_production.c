#include "mirage_production.h"

#include <stddef.h>
#include <stdint.h>

#include "mirage_production_generated.h"

#ifndef MIRAGE_CHANGEKIT_LOAD_PROPER_ABILITY_ADAPTER_ADDRESS
#error "MIRAGE_CHANGEKIT_LOAD_PROPER_ABILITY_ADAPTER_ADDRESS is required"
#endif
#ifndef MIRAGE_BATTLERS_COUNT_ADDRESS
#error "MIRAGE_BATTLERS_COUNT_ADDRESS is required"
#endif
#ifndef MIRAGE_ACTIVE_BATTLER_ADDRESS
#error "MIRAGE_ACTIVE_BATTLER_ADDRESS is required"
#endif
#ifndef MIRAGE_BATTLER_PARTY_INDEXES_ADDRESS
#error "MIRAGE_BATTLER_PARTY_INDEXES_ADDRESS is required"
#endif
#ifndef MIRAGE_BATTLE_MONS_ADDRESS
#error "MIRAGE_BATTLE_MONS_ADDRESS is required"
#endif
#ifndef MIRAGE_ABSENT_BATTLER_FLAGS_ADDRESS
#error "MIRAGE_ABSENT_BATTLER_FLAGS_ADDRESS is required"
#endif
#ifndef MIRAGE_BATTLE_MON_SIZE
#error "MIRAGE_BATTLE_MON_SIZE is required"
#endif
#ifndef MIRAGE_BATTLE_MON_ABILITY_OFFSET
#error "MIRAGE_BATTLE_MON_ABILITY_OFFSET is required"
#endif
#ifndef MIRAGE_SET_WARP_DESTINATION_ADDRESS
#error "MIRAGE_SET_WARP_DESTINATION_ADDRESS is required"
#endif
#ifndef MIRAGE_RESET_INITIAL_AVATAR_ADDRESS
#error "MIRAGE_RESET_INITIAL_AVATAR_ADDRESS is required"
#endif
#ifndef MIRAGE_WARP_INTO_MAP_ADDRESS
#error "MIRAGE_WARP_INTO_MAP_ADDRESS is required"
#endif
#ifndef MIRAGE_FIELD_CALLBACK_ADDRESS
#error "MIRAGE_FIELD_CALLBACK_ADDRESS is required"
#endif
#ifndef MIRAGE_DEFAULT_WARP_EXIT_ADDRESS
#error "MIRAGE_DEFAULT_WARP_EXIT_ADDRESS is required"
#endif
#ifndef MIRAGE_SET_MAIN_CALLBACK2_ADDRESS
#error "MIRAGE_SET_MAIN_CALLBACK2_ADDRESS is required"
#endif
#ifndef MIRAGE_CB2_LOAD_MAP_ADDRESS
#error "MIRAGE_CB2_LOAD_MAP_ADDRESS is required"
#endif

typedef uint8_t u8;
typedef int8_t s8;
typedef uint16_t u16;
typedef uint32_t u32;

#define PTR(type, address) ((type)(uintptr_t)(address))
#define MIRAGE_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))

enum {
    MIRAGE_STATE_MAGIC = 0x4D505331u, /* MPS1 */
    MIRAGE_JOURNAL_MARKER = 0x4D50u,
    MIRAGE_LEDGER_ADDRESS = 0x0203D000u,
    MIRAGE_LEDGER_SIZE = 0x800u,
    MIRAGE_LEDGER_CHECKSUM_OFFSET = 8u,
    MIRAGE_FACTORY_OFFSET = 0x392u,
    MIRAGE_FACTORY_SIZE = 714u,
    MIRAGE_SAVE_STATE_OFFSET = 0x65Cu,
    MIRAGE_SAVE_STATE_SIZE = 40u,
    MIRAGE_ROLLBACK_ADDRESS = 0x0203E400u,
    MIRAGE_SECTOR_SIZE = 0x1000u,
    MIRAGE_SECTOR_DATA_SIZE = 0x0FF0u,
    MIRAGE_SECTOR_NUMBER = 31u,
    MIRAGE_FLAG_HALL_OF_FAME = 0x082Cu,
    MIRAGE_FLAG_BADGE_FIRST = 0x0820u,
    MIRAGE_FLAG_LEAGUE_CLEAR = 0x13FAu,
    MIRAGE_MON_DATA_SPECIES = 11u,
    MIRAGE_MON_DATA_HELD_ITEM = 12u,
    MIRAGE_MON_DATA_MOVE1 = 13u,
    MIRAGE_MON_DATA_PP1 = 17u,
    MIRAGE_MON_DATA_PP_BONUSES = 21u,
    MIRAGE_MON_DATA_EXP = 25u,
    MIRAGE_MON_DATA_HP_EV = 26u,
    MIRAGE_MON_DATA_HP_IV = 39u,
    MIRAGE_MON_DATA_IS_EGG = 45u,
    MIRAGE_MON_DATA_LEVEL = 56u,
    MIRAGE_MON_DATA_HP = 57u,
    MIRAGE_LEVEL_100_EXP = 1640000u,
    MIRAGE_NATURE_SERIOUS = 12u,
    MIRAGE_NATURE_MINT_OFFSET = 0x0Fu,
    MIRAGE_MET_BITS_OFFSET = 0x46u,
    MIRAGE_IV_BITS_OFFSET = 0x48u,
    MIRAGE_HP_OFFSET = 0x56u,
    MIRAGE_MAX_HP_OFFSET = 0x58u,
    MIRAGE_HIDDEN_ABILITY_MASK = 0x1000u,
    MIRAGE_ABILITY_NUM_MASK = 0x80000000u,
    MIRAGE_PHASE_IDLE = 0u,
    MIRAGE_PHASE_SELECTION = 1u,
    MIRAGE_PHASE_ACTIVE = 2u,
    MIRAGE_PHASE_PREPARED = 3u,
    MIRAGE_PHASE_BATTLE = 4u,
    MIRAGE_CLEANUP_NONE = 0u,
    MIRAGE_CLEANUP_COMPLETE = 1u,
    MIRAGE_CLEANUP_LOSS = 2u,
    MIRAGE_CLEANUP_ABORT = 3u,
    MIRAGE_CLEANUP_RECOVER = 4u,
    MIRAGE_SAVE_OK = 0u,
    MIRAGE_BATTLE_OUTCOME_WON = 1u
};

typedef struct MiragePokemon {
    u8 bytes[MIRAGE_PRODUCTION_MON_SIZE];
} MiragePokemon;

typedef struct __attribute__((packed)) MirageLedgerState {
    u16 current_record[8];
    u16 best_record[8];
    u32 reward_claim_bits;
    u32 item_reward_transaction_id;
} MirageLedgerState;

typedef u8 (*FlagGetFn)(u16);
typedef void (*FlagChangeFn)(u16);
typedef u32 (*GetMonDataFn)(const void *, int, u8 *);
typedef void (*SetMonDataFn)(void *, int, const void *);
typedef void (*CreateMonFn)(void *, u16, u8, u8, u8, u32, u8, u32);
typedef u16 (*GetMonAbilityFn)(const void *);
typedef void (*CalculateMonStatsFn)(void *);
typedef u8 (*CalculatePpFn)(u16, u8, u8);
typedef void (*VoidFn)(void);
typedef u16 (*RandomFn)(void);
typedef u8 (*ConfigurePolicyFn)(u8, u8);
typedef u8 (*ConfigureVirtualItemFn)(u8, u16);
typedef u32 (*SaveValidateFn)(const void *, u32);
typedef void (*SaveFinalizeFn)(void *);
typedef u8 (*TrySavingDataFn)(u8);
typedef u8 (*TryWriteSectorFn)(u16, const void *);
typedef void (*BuildTrainerPartyFn)(void);
typedef void (*SetWarpDestinationFn)(s8, s8, s8, s8, s8);
typedef void (*SetMainCallback2Fn)(VoidFn);

#define FN_FLAG_GET PTR(FlagGetFn, MIRAGE_FLAG_GET_ADDRESS)
#define FN_FLAG_SET PTR(FlagChangeFn, MIRAGE_ORIGINAL_FLAG_SET_ADDRESS)
#define FN_FLAG_CLEAR PTR(FlagChangeFn, MIRAGE_ORIGINAL_FLAG_CLEAR_ADDRESS)
#define FN_GET_MON_DATA PTR(GetMonDataFn, MIRAGE_GET_MON_DATA_ADDRESS)
#define FN_SET_MON_DATA PTR(SetMonDataFn, MIRAGE_SET_MON_DATA_ADDRESS)
#define FN_CREATE_MON PTR(CreateMonFn, MIRAGE_CREATE_MON_ADDRESS)
#define FN_GET_MON_ABILITY PTR(GetMonAbilityFn, MIRAGE_GET_MON_ABILITY_ADDRESS)
#define FN_CALCULATE_MON_STATS \
    PTR(CalculateMonStatsFn, MIRAGE_CALCULATE_MON_STATS_ADDRESS)
#define FN_CALCULATE_PP PTR(CalculatePpFn, MIRAGE_CALCULATE_PP_ADDRESS)
#define FN_HEAL_PLAYER_PARTY PTR(VoidFn, MIRAGE_HEAL_PLAYER_PARTY_ADDRESS)
#define FN_RANDOM PTR(RandomFn, MIRAGE_RANDOM_ADDRESS)
#define FN_CONFIGURE_POLICY \
    PTR(ConfigurePolicyFn, MIRAGE_CONFIGURE_BATTLE_POLICY_ADDRESS)
#define FN_CONFIGURE_VIRTUAL_ITEM \
    PTR(ConfigureVirtualItemFn, MIRAGE_CONFIGURE_VIRTUAL_ITEM_ADDRESS)
#define FN_PENDING_CLEAR PTR(VoidFn, MIRAGE_CFRU_PENDING_CLEAR_ADDRESS)
#define FN_SAVE_VALIDATE PTR(SaveValidateFn, MIRAGE_SAVE_VALIDATE_ADDRESS)
#define FN_SAVE_FINALIZE PTR(SaveFinalizeFn, MIRAGE_SAVE_FINALIZE_ADDRESS)
#define FN_ORIGINAL_TRY_SAVING_DATA \
    PTR(TrySavingDataFn, MIRAGE_ORIGINAL_TRY_SAVING_DATA_ADDRESS)
#define FN_TRY_WRITE_SECTOR \
    PTR(TryWriteSectorFn, MIRAGE_TRY_WRITE_SECTOR_ADDRESS)
#define FN_QOL_SAVE_LOAD \
    PTR(TrySavingDataFn, MIRAGE_QOL_SAVE_LOAD_ADAPTER_ADDRESS)
#define FN_CHANGEKIT_BUILD_TRAINER_PARTY \
    PTR(BuildTrainerPartyFn, MIRAGE_CHANGEKIT_BUILD_TRAINER_PARTY_ADDRESS)
#define FN_CHANGEKIT_LOAD_PROPER_ABILITY \
    PTR(VoidFn, MIRAGE_CHANGEKIT_LOAD_PROPER_ABILITY_ADAPTER_ADDRESS)
#define FN_SET_WARP_DESTINATION \
    PTR(SetWarpDestinationFn, MIRAGE_SET_WARP_DESTINATION_ADDRESS)
#define FN_RESET_INITIAL_AVATAR \
    PTR(VoidFn, MIRAGE_RESET_INITIAL_AVATAR_ADDRESS)
#define FN_WARP_INTO_MAP PTR(VoidFn, MIRAGE_WARP_INTO_MAP_ADDRESS)
#define FN_SET_MAIN_CALLBACK2 \
    PTR(SetMainCallback2Fn, MIRAGE_SET_MAIN_CALLBACK2_ADDRESS)

#define G_LEDGER PTR(u8 *, MIRAGE_LEDGER_ADDRESS)
#define G_MIRAGE_LEDGER \
    PTR(MirageLedgerState *, MIRAGE_LEDGER_ADDRESS + MIRAGE_SAVE_STATE_OFFSET)
#define G_ROLLBACK PTR(u8 *, MIRAGE_ROLLBACK_ADDRESS)
#define G_PLAYER_PARTY PTR(MiragePokemon *, MIRAGE_PLAYER_PARTY_ADDRESS)
#define G_ENEMY_PARTY PTR(MiragePokemon *, MIRAGE_ENEMY_PARTY_ADDRESS)
#define G_SELECTED_ORDER PTR(volatile u8 *, MIRAGE_SELECTED_ORDER_ADDRESS)
#define G_PLAYER_PARTY_COUNT \
    (*PTR(volatile u8 *, MIRAGE_PLAYER_PARTY_COUNT_ADDRESS))
#define G_ENEMY_PARTY_COUNT \
    (*PTR(volatile u8 *, MIRAGE_ENEMY_PARTY_COUNT_ADDRESS))
#define G_BATTLE_OUTCOME (*PTR(volatile u8 *, MIRAGE_BATTLE_OUTCOME_ADDRESS))
#define G_TRAINER_OPPONENT_A \
    (*PTR(volatile u16 *, MIRAGE_TRAINER_OPPONENT_A_ADDRESS))
#define G_SPECIAL_RESULT \
    (*PTR(volatile u16 *, MIRAGE_PRODUCTION_SPECIAL_VAR_RESULT))
#define G_SPECIAL_ARG0 \
    (*PTR(volatile u16 *, MIRAGE_PRODUCTION_SPECIAL_VAR_ARG0))
#define G_ACTIVE_BATTLER \
    (*PTR(volatile u8 *, MIRAGE_ACTIVE_BATTLER_ADDRESS))
#define G_BATTLERS_COUNT \
    (*PTR(volatile u8 *, MIRAGE_BATTLERS_COUNT_ADDRESS))
#define G_ABSENT_BATTLER_FLAGS \
    (*PTR(volatile u8 *, MIRAGE_ABSENT_BATTLER_FLAGS_ADDRESS))
#define G_BATTLER_PARTY_INDEXES \
    PTR(volatile u16 *, MIRAGE_BATTLER_PARTY_INDEXES_ADDRESS)
#define G_BATTLE_MONS PTR(u8 *, MIRAGE_BATTLE_MONS_ADDRESS)
#define G_FIELD_CALLBACK \
    (*PTR(VoidFn volatile *, MIRAGE_FIELD_CALLBACK_ADDRESS))
#define G_SAVE_BUFFER PTR(u8 *, MIRAGE_SAVE_BUFFER_ADDRESS)
#define G_SECTOR31_IMAGE PTR(const u8 *, MIRAGE_SECTOR31_IMAGE_ADDRESS)

_Static_assert(sizeof(MiragePokemon) == 100u, "Pokemon ABI changed");
_Static_assert(sizeof(MirageLedgerState) == MIRAGE_SAVE_STATE_SIZE,
               "Mirage ledger ABI changed");
_Static_assert(sizeof(MirageProductionState) == MIRAGE_PRODUCTION_STATE_SIZE,
               "Mirage volatile ABI changed");
_Static_assert(offsetof(MirageProductionState, party_snapshot) == 0x40u,
               "Mirage party snapshot offset changed");
_Static_assert(offsetof(MirageProductionState, party_snapshot)
                       + MIRAGE_PRODUCTION_PARTY_SIZE
                             * MIRAGE_PRODUCTION_MON_SIZE
                   == MIRAGE_PRODUCTION_STATE_SIZE,
               "Mirage volatile ABI end changed");
_Static_assert(MIRAGE_PRODUCTION_JOURNAL_FIRST_RECORD == 4u
                   && MIRAGE_PRODUCTION_JOURNAL_RECORD_COUNT == 4u,
               "Mirage journal record contract changed");

/* GCC may recognize fixed-size byte loops as memcpy even in freestanding
 * mode.  Keep the payload self-contained and make the implementation
 * intentionally volatile so it cannot fold back into a recursive builtin. */
void *memcpy(void *destination, const void *source, size_t size)
{
    volatile u8 *out = (volatile u8 *)destination;
    const volatile u8 *in = (const volatile u8 *)source;
    size_t index;
    for (index = 0u; index < size; ++index)
        out[index] = in[index];
    return destination;
}

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

static u16 read_u16(const u8 *source)
{
    return (u16)((u16)source[0] | ((u16)source[1] << 8));
}

static u32 read_u32(const u8 *source)
{
    return (u32)source[0] | ((u32)source[1] << 8)
        | ((u32)source[2] << 16) | ((u32)source[3] << 24);
}

static void write_u16(u8 *destination, u16 value)
{
    destination[0] = (u8)value;
    destination[1] = (u8)(value >> 8);
}

static void write_u32(u8 *destination, u32 value)
{
    destination[0] = (u8)value;
    destination[1] = (u8)(value >> 8);
    destination[2] = (u8)(value >> 16);
    destination[3] = (u8)(value >> 24);
}

static u32 fnv32(const u8 *bytes, u32 size)
{
    u32 hash = 2166136261u;
    u32 index;
    for (index = 0u; index < size; ++index) {
        hash ^= bytes[index];
        hash *= 16777619u;
    }
    return hash;
}

static void initialize_state(void)
{
    clear_bytes(gMirageProductionState, MIRAGE_PRODUCTION_STATE_SIZE);
    gMirageProductionState->magic = MIRAGE_STATE_MAGIC;
    gMirageProductionState->magic_inverse = ~MIRAGE_STATE_MAGIC;
    gMirageProductionState->virtual_tier = 0xFFu;
}

static u8 state_valid(void)
{
    return (u8)(gMirageProductionState->magic == MIRAGE_STATE_MAGIC
                && gMirageProductionState->magic_inverse
                    == ~MIRAGE_STATE_MAGIC);
}

static void ensure_state(void)
{
    if (!state_valid())
        initialize_state();
}

static u16 set_status(u16 status)
{
    ensure_state();
    gMirageProductionState->last_status = status;
    G_SPECIAL_RESULT = status;
    return status;
}

static u8 ledger_valid(void)
{
    return (u8)(FN_SAVE_VALIDATE(G_LEDGER, MIRAGE_LEDGER_SIZE)
                == MIRAGE_SAVE_OK);
}

static u8 badge_mask(void)
{
    u8 mask = 0u;
    u8 index;
    for (index = 0u; index < 8u; ++index) {
        if (FN_FLAG_GET((u16)(MIRAGE_FLAG_BADGE_FIRST + index)))
            mask |= (u8)(1u << index);
    }
    return mask;
}

static void write_badges(u8 mask)
{
    u8 index;
    for (index = 0u; index < 8u; ++index) {
        if (mask & (u8)(1u << index))
            (void)FN_FLAG_SET((u16)(MIRAGE_FLAG_BADGE_FIRST + index));
        else
            (void)FN_FLAG_CLEAR((u16)(MIRAGE_FLAG_BADGE_FIRST + index));
    }
}

static void restore_party(void)
{
    if (!gMirageProductionState->party_snapshot_valid)
        return;
    copy_bytes(G_PLAYER_PARTY, gMirageProductionState->party_snapshot, 600u);
    G_PLAYER_PARTY_COUNT = gMirageProductionState->original_party_count;
    gMirageProductionState->party_hash_after =
        fnv32((const u8 *)G_PLAYER_PARTY, 600u);
}

static void restore_runtime_originals(void)
{
    restore_party();
    if (gMirageProductionState->badge_snapshot_valid)
        write_badges(gMirageProductionState->badge_snapshot);
}

static void journal_clear(void)
{
    u8 index;
    for (index = 4u; index < 8u; ++index)
        G_MIRAGE_LEDGER->current_record[index] = 0u;
}

static u16 journal_payload(void)
{
    return (u16)((u16)gMirageProductionState->badge_snapshot
        | ((u16)(gMirageProductionState->round & 3u) << 8)
        | ((u16)(gMirageProductionState->gimmick & 7u) << 10));
}

static void journal_write_active(void)
{
    u16 payload = journal_payload();
    G_MIRAGE_LEDGER->current_record[4] = MIRAGE_JOURNAL_MARKER;
    G_MIRAGE_LEDGER->current_record[5] = (u16)~MIRAGE_JOURNAL_MARKER;
    G_MIRAGE_LEDGER->current_record[6] = payload;
    G_MIRAGE_LEDGER->current_record[7] = (u16)~payload;
}

static u8 journal_is_active(void)
{
    return (u8)(G_MIRAGE_LEDGER->current_record[4]
                    == MIRAGE_JOURNAL_MARKER
                && G_MIRAGE_LEDGER->current_record[5]
                    == (u16)~MIRAGE_JOURNAL_MARKER
                && G_MIRAGE_LEDGER->current_record[7]
                    == (u16)~G_MIRAGE_LEDGER->current_record[6]);
}

static u8 journal_has_bytes(void)
{
    return (u8)(G_MIRAGE_LEDGER->current_record[4]
        | G_MIRAGE_LEDGER->current_record[5]
        | G_MIRAGE_LEDGER->current_record[6]
        | G_MIRAGE_LEDGER->current_record[7]);
}

static void transaction_begin(void)
{
    copy_bytes(G_ROLLBACK, G_LEDGER, MIRAGE_LEDGER_SIZE);
}

static u8 write_sector31(void)
{
    if (gMirageProductionState->fault_armed
        && gMirageProductionState->fault_mode == 2u) {
        gMirageProductionState->fault_armed = 0u;
        return 0u;
    }
    clear_bytes(G_SAVE_BUFFER, MIRAGE_SECTOR_SIZE);
    copy_bytes(G_SAVE_BUFFER, G_SECTOR31_IMAGE, MIRAGE_SECTOR_DATA_SIZE);
    return (u8)(FN_TRY_WRITE_SECTOR(MIRAGE_SECTOR_NUMBER, G_SAVE_BUFFER)
                == 1u);
}

static u8 write_standard_save(void)
{
    if (gMirageProductionState->fault_armed
        && gMirageProductionState->fault_mode == 1u) {
        gMirageProductionState->fault_armed = 0u;
        return 0u;
    }
    return (u8)(FN_ORIGINAL_TRY_SAVING_DATA(0u) == 1u);
}

static void compensate_after_failure(void)
{
    copy_bytes(G_LEDGER, G_ROLLBACK, MIRAGE_LEDGER_SIZE);
    journal_clear();
    FN_SAVE_FINALIZE(G_LEDGER);
    restore_runtime_originals();
    (void)write_standard_save();
    (void)write_sector31();
}

static u8 transaction_commit(u8 continue_active)
{
    write_u32(G_LEDGER + 12u, read_u32(G_LEDGER + 12u) + 1u);
    FN_SAVE_FINALIZE(G_LEDGER);
    restore_runtime_originals();
    if (!write_standard_save() || !write_sector31()) {
        compensate_after_failure();
        return 0u;
    }
    if (continue_active)
        write_badges(0u);
    return 1u;
}

static void clear_challenge_state(u8 reason)
{
    u32 transaction = G_MIRAGE_LEDGER->item_reward_transaction_id;
    u16 last = gMirageProductionState->last_status;
    FN_PENDING_CLEAR();
    initialize_state();
    gMirageProductionState->cleanup_reason = reason;
    gMirageProductionState->last_transaction = transaction;
    gMirageProductionState->last_status = last;
}

static u16 current_total(void)
{
    u32 total = 0u;
    u8 index;
    for (index = 0u; index < 4u; ++index)
        total += G_MIRAGE_LEDGER->current_record[index];
    return total > 0xFFFFu ? 0xFFFFu : (u16)total;
}

static u8 hall_of_fame_unlocked(void)
{
    return (u8)(FN_FLAG_GET(MIRAGE_FLAG_HALL_OF_FAME)
                || G_LEDGER[18u] != 0u);
}

static u8 cert4_unlocked(void)
{
    return (u8)((G_LEDGER[24u] & 0x08u) != 0u);
}

static u8 league_unlocked(void)
{
    return (u8)(FN_FLAG_GET(MIRAGE_FLAG_LEAGUE_CLEAR)
                || G_LEDGER[21u] != 0u);
}

static u8 reward_unlocked(const MirageProductionRewardRow *reward)
{
    if (reward->unlock_kind == 0u)
        return 1u;
    if (reward->unlock_value == 0x082Cu)
        return hall_of_fame_unlocked();
    if (reward->unlock_value == 0x1403u)
        return cert4_unlocked();
    if (reward->unlock_value == 0x13FAu)
        return league_unlocked();
    return (u8)FN_FLAG_GET(reward->unlock_value);
}

static u8 choose_virtual_tier(u16 achieved_streak)
{
    u8 index;
    u8 selected = 0xFFu;
    for (index = 0u; index < MIRAGE_PRODUCTION_REWARD_COUNT; ++index) {
        if (!reward_unlocked(&gMirageProductionRewards[index]))
            continue;
        if (achieved_streak >= gMirageProductionRewards[index].streak)
            selected = index;
    }
    return selected;
}

static u8 reduce_random(u8 value, u8 count)
{
    while (value >= count)
        value = (u8)(value - count);
    return value;
}

static void choose_opponents(void)
{
    u8 pool[6] = {0u, 1u, 2u, 3u, 4u, 5u};
    u8 index;
    for (index = 0u; index < 3u; ++index) {
        u16 random = FN_RANDOM();
        u8 chosen = (u8)(index + reduce_random((u8)random,
                                                (u8)(6u - index)));
        u8 swap = pool[index];
        if (index == 0u)
            gMirageProductionState->rng_before = random;
        gMirageProductionState->rng_after = random;
        pool[index] = pool[chosen];
        pool[chosen] = swap;
        gMirageProductionState->opponent_slots[index] = pool[index];
    }
}

static u8 set_exact_ability(MiragePokemon *mon, u16 ability)
{
    u8 mode;
    for (mode = 0u; mode < 3u; ++mode) {
        u16 met = read_u16(mon->bytes + MIRAGE_MET_BITS_OFFSET);
        u32 iv = read_u32(mon->bytes + MIRAGE_IV_BITS_OFFSET);
        met &= (u16)~MIRAGE_HIDDEN_ABILITY_MASK;
        iv &= ~MIRAGE_ABILITY_NUM_MASK;
        if (mode == 1u)
            iv |= MIRAGE_ABILITY_NUM_MASK;
        else if (mode == 2u)
            met |= MIRAGE_HIDDEN_ABILITY_MASK;
        write_u16(mon->bytes + MIRAGE_MET_BITS_OFFSET, met);
        write_u32(mon->bytes + MIRAGE_IV_BITS_OFFSET, iv);
        if (FN_GET_MON_ABILITY(mon) == ability)
            return 1u;
    }

    /* A manifest-authored ability need not exist in the persistent species
     * table (SPECIAL6 Ninetales and Cloyster are deliberate examples).  A
     * party Pokemon can only encode the table's primary/secondary/hidden
     * selector, so retain the primary selector here.  The battle-data adapter
     * below writes the authored ID after the engine and ChangeKit have created
     * the active BattlePokemon. */
    {
        u16 met = read_u16(mon->bytes + MIRAGE_MET_BITS_OFFSET);
        u32 iv = read_u32(mon->bytes + MIRAGE_IV_BITS_OFFSET);
        met &= (u16)~MIRAGE_HIDDEN_ABILITY_MASK;
        iv &= ~MIRAGE_ABILITY_NUM_MASK;
        write_u16(mon->bytes + MIRAGE_MET_BITS_OFFSET, met);
        write_u32(mon->bytes + MIRAGE_IV_BITS_OFFSET, iv);
    }
    return 1u;
}

static u8 build_rental(MiragePokemon *mon,
                       const MirageProductionRentalRow *row,
                       u16 held_item)
{
    u8 index;
    u32 value;
    clear_bytes(mon, sizeof(*mon));
    FN_CREATE_MON(mon, row->species, 100u, 31u, 1u,
                  MIRAGE_NATURE_SERIOUS, 0u, 0u);
    value = held_item;
    FN_SET_MON_DATA(mon, MIRAGE_MON_DATA_HELD_ITEM, &value);
    value = 0u;
    FN_SET_MON_DATA(mon, MIRAGE_MON_DATA_PP_BONUSES, &value);
    for (index = 0u; index < 4u; ++index) {
        value = row->moves[index];
        FN_SET_MON_DATA(mon, MIRAGE_MON_DATA_MOVE1 + index, &value);
        value = FN_CALCULATE_PP(row->moves[index], 0u, index);
        FN_SET_MON_DATA(mon, MIRAGE_MON_DATA_PP1 + index, &value);
    }
    for (index = 0u; index < 6u; ++index) {
        value = MIRAGE_PRODUCTION_EV_ROLE_510_VALUE;
        FN_SET_MON_DATA(mon, MIRAGE_MON_DATA_HP_EV + index, &value);
        value = 31u;
        FN_SET_MON_DATA(mon, MIRAGE_MON_DATA_HP_IV + index, &value);
    }
    mon->bytes[MIRAGE_NATURE_MINT_OFFSET] =
        (u8)(row->nature + 1u);
    if (!set_exact_ability(mon, row->ability))
        return 0u;
    FN_CALCULATE_MON_STATS(mon);
    write_u16(mon->bytes + MIRAGE_HP_OFFSET,
              read_u16(mon->bytes + MIRAGE_MAX_HP_OFFSET));
    return (u8)(FN_GET_MON_DATA(mon, MIRAGE_MON_DATA_SPECIES, NULL)
                    == row->species
                && FN_GET_MON_DATA(mon, MIRAGE_MON_DATA_LEVEL, NULL) == 100u);
}

static u8 build_selected_enemy(u8 virtual_items)
{
    u8 index;
    for (index = 0u; index < 3u; ++index) {
        u8 source = gMirageProductionState->opponent_slots[index];
        u16 item;
        if (source >= MIRAGE_PRODUCTION_RENTAL_COUNT)
            return 0u;
        item = virtual_items ? gMirageProductionState->virtual_items[index]
                             : gMirageProductionRentals[source].item;
        if (!build_rental(&G_ENEMY_PARTY[index],
                          &gMirageProductionRentals[source], item))
            return 0u;
    }
    clear_bytes(&G_ENEMY_PARTY[3], 3u * sizeof(MiragePokemon));
    G_ENEMY_PARTY_COUNT = 3u;
    return 1u;
}

static u8 build_selected_player(void)
{
    u8 index;
    u32 experience = MIRAGE_LEVEL_100_EXP;
    if (!gMirageProductionState->party_snapshot_valid)
        return 0u;
    for (index = 0u; index < 3u; ++index) {
        u8 slot = gMirageProductionState->selected_slots[index];
        if (slot < 1u || slot > 6u)
            return 0u;
        copy_bytes(&G_PLAYER_PARTY[index],
                   gMirageProductionState->party_snapshot
                       + (u32)(slot - 1u) * sizeof(MiragePokemon),
                   sizeof(MiragePokemon));
        FN_SET_MON_DATA(&G_PLAYER_PARTY[index], MIRAGE_MON_DATA_EXP,
                        &experience);
        FN_CALCULATE_MON_STATS(&G_PLAYER_PARTY[index]);
    }
    clear_bytes(&G_PLAYER_PARTY[3], 3u * sizeof(MiragePokemon));
    G_PLAYER_PARTY_COUNT = 3u;
    FN_HEAL_PLAYER_PARTY();
    return 1u;
}

static u8 persist_exit(u8 reset_streak)
{
    u8 index;
    transaction_begin();
    if (reset_streak) {
        for (index = 0u; index < 4u; ++index)
            G_MIRAGE_LEDGER->current_record[index] = 0u;
    }
    journal_clear();
    ++G_MIRAGE_LEDGER->item_reward_transaction_id;
    gMirageProductionState->last_transaction =
        G_MIRAGE_LEDGER->item_reward_transaction_id;
    return transaction_commit(0u);
}

MIRAGE_EXPORT(MirageProduction_Probe)
__attribute__((optimize("no-jump-tables")))
u32 MirageProduction_Probe(u32 selector)
{
    u32 index;
    ensure_state();
    if (selector == MIRAGE_PROBE_ABI_VERSION)
        return MIRAGE_PRODUCTION_ABI_VERSION;
    if (selector == MIRAGE_PROBE_STATE_VALID)
        return state_valid();
    if (selector == MIRAGE_PROBE_ACTIVE)
        return gMirageProductionState->active;
    if (selector == MIRAGE_PROBE_ROUND)
        return gMirageProductionState->round;
    if (selector == MIRAGE_PROBE_BATTLE_IN_ROUND)
        return gMirageProductionState->battle_in_round;
    if (selector == MIRAGE_PROBE_GIMMICK)
        return gMirageProductionState->gimmick;
    if (selector == MIRAGE_PROBE_BADGE_SNAPSHOT)
        return gMirageProductionState->badge_snapshot;
    if (selector == MIRAGE_PROBE_SELECTED_PACKED)
        return (u32)gMirageProductionState->selected_slots[0]
            | ((u32)gMirageProductionState->selected_slots[1] << 8)
            | ((u32)gMirageProductionState->selected_slots[2] << 16);
    if (selector == MIRAGE_PROBE_LAST_STATUS)
        return gMirageProductionState->last_status;
    if (selector == MIRAGE_PROBE_VIRTUAL_PACKED)
        return (u32)(gMirageProductionState->virtual_items[0] & 0x3FFu)
            | ((u32)(gMirageProductionState->virtual_items[1] & 0x3FFu) << 10)
            | ((u32)(gMirageProductionState->virtual_items[2] & 0x3FFu) << 20);
    if (selector == MIRAGE_PROBE_PENDING_CONFIGURED)
        return gMirageProductionState->pending_configured;
    if (selector == MIRAGE_PROBE_RNG_STATE)
        return gMirageProductionState->rng_after;
    if (selector == MIRAGE_PROBE_OPPONENT_PACKED)
        return (u32)gMirageProductionState->opponent_slots[0]
            | ((u32)gMirageProductionState->opponent_slots[1] << 8)
            | ((u32)gMirageProductionState->opponent_slots[2] << 16);
    if (selector == MIRAGE_PROBE_CLAIM_BITS)
        return G_MIRAGE_LEDGER->reward_claim_bits;
    if (selector == MIRAGE_PROBE_TRANSACTION_ID)
        return G_MIRAGE_LEDGER->item_reward_transaction_id;
    if (selector == MIRAGE_PROBE_JOURNAL_MARKER_PAIR)
        return (u32)G_MIRAGE_LEDGER->current_record[4]
            | ((u32)G_MIRAGE_LEDGER->current_record[5] << 16);
    if (selector == MIRAGE_PROBE_JOURNAL_PAYLOAD_PAIR)
        return (u32)G_MIRAGE_LEDGER->current_record[6]
            | ((u32)G_MIRAGE_LEDGER->current_record[7] << 16);
    if (selector >= MIRAGE_PROBE_CURRENT_RECORD_0
        && selector <= MIRAGE_PROBE_CURRENT_RECORD_3)
        return G_MIRAGE_LEDGER->current_record[
            selector - MIRAGE_PROBE_CURRENT_RECORD_0];
    if (selector >= MIRAGE_PROBE_BEST_RECORD_0
        && selector <= MIRAGE_PROBE_BEST_RECORD_3)
        return G_MIRAGE_LEDGER->best_record[
            selector - MIRAGE_PROBE_BEST_RECORD_0];
    if (selector >= MIRAGE_PROBE_SELECTED_SLOT_0
        && selector <= MIRAGE_PROBE_SELECTED_SLOT_2)
        return gMirageProductionState->selected_slots[
            selector - MIRAGE_PROBE_SELECTED_SLOT_0];
    if (selector >= MIRAGE_PROBE_VIRTUAL_ITEM_0
        && selector <= MIRAGE_PROBE_VIRTUAL_ITEM_2)
        return gMirageProductionState->virtual_items[
            selector - MIRAGE_PROBE_VIRTUAL_ITEM_0];
    if (selector == MIRAGE_PROBE_FACTORY_SENTINEL_HASH)
        return fnv32(G_LEDGER + MIRAGE_FACTORY_OFFSET, MIRAGE_FACTORY_SIZE);
    if (selector == MIRAGE_PROBE_UPSTREAM_SENTINEL_HASH) {
        u32 hash = 2166136261u;
        for (index = 0u; index < MIRAGE_LEDGER_SIZE; ++index) {
            if ((index >= MIRAGE_LEDGER_CHECKSUM_OFFSET && index < 16u)
                || (index >= MIRAGE_SAVE_STATE_OFFSET
                    && index < MIRAGE_SAVE_STATE_OFFSET
                        + MIRAGE_SAVE_STATE_SIZE))
                continue;
            hash ^= G_LEDGER[index];
            hash *= 16777619u;
        }
        return hash;
    }
    if (selector == MIRAGE_PROBE_BATTLE_LOCAL_ACTIVE_COUNT)
        return gMirageProductionState->battle_local_active ? 3u : 0u;
    if (selector == MIRAGE_PROBE_BADGE_CURRENT_MASK)
        return badge_mask();
    return 0u;
}

MIRAGE_EXPORT(MirageProduction_FieldEnter)
u16 MirageProduction_FieldEnter(void)
{
    u16 recovered;
    ensure_state();
    if (!ledger_valid())
        return set_status(MIRAGE_STATUS_SAVE_INVALID);
    if (journal_is_active() || gMirageProductionState->active) {
        recovered = MirageProduction_Recover();
        if (recovered != MIRAGE_STATUS_RECOVERED
            && recovered != MIRAGE_STATUS_NOT_ACTIVE)
            return recovered;
    } else if (journal_has_bytes()) {
        return set_status(MIRAGE_STATUS_SAVE_INVALID);
    }
    if (!hall_of_fame_unlocked())
        return set_status(MIRAGE_STATUS_NOT_UNLOCKED);
    initialize_state();
    copy_bytes(gMirageProductionState->party_snapshot, G_PLAYER_PARTY, 600u);
    gMirageProductionState->party_snapshot_valid = 1u;
    gMirageProductionState->original_party_count = G_PLAYER_PARTY_COUNT;
    gMirageProductionState->party_hash_before =
        fnv32(gMirageProductionState->party_snapshot, 600u);
    gMirageProductionState->badge_snapshot = badge_mask();
    gMirageProductionState->badge_snapshot_valid = 1u;
    gMirageProductionState->phase = MIRAGE_PHASE_SELECTION;
    return set_status(MIRAGE_STATUS_OK);
}

MIRAGE_EXPORT(MirageProduction_CommitSelection)
u16 MirageProduction_CommitSelection(void)
{
    u8 index;
    ensure_state();
    if (gMirageProductionState->phase != MIRAGE_PHASE_SELECTION
        || !gMirageProductionState->party_snapshot_valid)
        return set_status(MIRAGE_STATUS_NOT_ACTIVE);
    if (G_SELECTED_ORDER[0] == 0u && G_SELECTED_ORDER[1] == 0u
        && G_SELECTED_ORDER[2] == 0u) {
        clear_challenge_state(MIRAGE_CLEANUP_ABORT);
        return set_status(MIRAGE_STATUS_CANCELLED);
    }
    for (index = 0u; index < 3u; ++index) {
        u8 value = G_SELECTED_ORDER[index];
        MiragePokemon *mon;
        if (value < 1u || value > 6u)
            return set_status(MIRAGE_STATUS_INVALID_SELECTION);
        gMirageProductionState->selected_slots[index] = value;
        if ((index > 0u && gMirageProductionState->selected_slots[index]
                == gMirageProductionState->selected_slots[0])
            || (index > 1u && gMirageProductionState->selected_slots[index]
                == gMirageProductionState->selected_slots[1]))
            return set_status(MIRAGE_STATUS_INVALID_SELECTION);
        mon = (MiragePokemon *)(void *)(
            gMirageProductionState->party_snapshot
            + (u32)(value - 1u) * sizeof(MiragePokemon));
        if (FN_GET_MON_DATA(mon, MIRAGE_MON_DATA_SPECIES, NULL) == 0u
            || FN_GET_MON_DATA(mon, MIRAGE_MON_DATA_IS_EGG, NULL) != 0u
            || FN_GET_MON_DATA(mon, MIRAGE_MON_DATA_HP, NULL) == 0u)
            return set_status(MIRAGE_STATUS_INVALID_SELECTION);
    }
    gMirageProductionState->selected_count = 3u;
    gMirageProductionState->active = 1u;
    gMirageProductionState->round = 0u;
    gMirageProductionState->battle_in_round = 0u;
    gMirageProductionState->gimmick = MIRAGE_PRODUCTION_MECHANIC_NONE;
    gMirageProductionState->total_wins = current_total();
    gMirageProductionState->phase = MIRAGE_PHASE_ACTIVE;
    transaction_begin();
    journal_write_active();
    ++G_MIRAGE_LEDGER->item_reward_transaction_id;
    gMirageProductionState->last_transaction =
        G_MIRAGE_LEDGER->item_reward_transaction_id;
    if (!transaction_commit(1u)) {
        clear_challenge_state(MIRAGE_CLEANUP_ABORT);
        return set_status(MIRAGE_STATUS_PERSIST_FAILED);
    }
    return set_status(MIRAGE_STATUS_OK);
}

MIRAGE_EXPORT(MirageProduction_CommitRound4Mechanic)
u16 MirageProduction_CommitRound4Mechanic(void)
{
    u16 mechanic = G_SPECIAL_ARG0;
    ensure_state();
    if (!gMirageProductionState->active)
        return set_status(MIRAGE_STATUS_NOT_ACTIVE);
    if (gMirageProductionState->round != 3u
        || gMirageProductionState->battle_in_round != 0u
        || current_total() < 21u)
        return set_status(MIRAGE_STATUS_BAD_ARGUMENT);
    if (mechanic != MIRAGE_PRODUCTION_MECHANIC_MEGA
        && mechanic != MIRAGE_PRODUCTION_MECHANIC_Z
        && mechanic != MIRAGE_PRODUCTION_MECHANIC_TERA)
        return set_status(MIRAGE_STATUS_BAD_ARGUMENT);
    transaction_begin();
    gMirageProductionState->gimmick = (u8)mechanic;
    journal_write_active();
    ++G_MIRAGE_LEDGER->item_reward_transaction_id;
    gMirageProductionState->last_transaction =
        G_MIRAGE_LEDGER->item_reward_transaction_id;
    if (!transaction_commit(1u)) {
        clear_challenge_state(MIRAGE_CLEANUP_ABORT);
        return set_status(MIRAGE_STATUS_PERSIST_FAILED);
    }
    return set_status(MIRAGE_STATUS_OK);
}

MIRAGE_EXPORT(MirageProduction_PrepareBattle)
u16 MirageProduction_PrepareBattle(void)
{
    u16 expected;
    u8 tier;
    u8 index;
    ensure_state();
    if (!gMirageProductionState->active
        || gMirageProductionState->phase != MIRAGE_PHASE_ACTIVE)
        return set_status(MIRAGE_STATUS_NOT_ACTIVE);
    expected = (u16)((u16)gMirageProductionState->round * 7u
                     + gMirageProductionState->battle_in_round);
    if (G_SPECIAL_ARG0 != expected)
        return set_status(MIRAGE_STATUS_BAD_ARGUMENT);
    if (gMirageProductionState->round == 3u
        && gMirageProductionState->gimmick != MIRAGE_PRODUCTION_MECHANIC_MEGA
        && gMirageProductionState->gimmick != MIRAGE_PRODUCTION_MECHANIC_Z
        && gMirageProductionState->gimmick != MIRAGE_PRODUCTION_MECHANIC_TERA)
        return set_status(MIRAGE_STATUS_BAD_ARGUMENT);
    gMirageProductionState->trainer_id =
        gMirageProductionModes[gMirageProductionState->round].trainer_id;
    G_TRAINER_OPPONENT_A = gMirageProductionState->trainer_id;
    choose_opponents();
    tier = choose_virtual_tier(current_total());
    gMirageProductionState->virtual_tier = tier == 0xFFu
        ? 0xFFu : gMirageProductionRewards[tier].tier;
    for (index = 0u; index < 3u; ++index)
        gMirageProductionState->virtual_items[index] = tier == 0xFFu
            ? 0u : gMirageProductionRewards[tier].item;
    gMirageProductionState->phase = MIRAGE_PHASE_PREPARED;
    return set_status(MIRAGE_STATUS_OK);
}

MIRAGE_EXPORT(MirageProduction_FinalizeBattleCopy)
u16 MirageProduction_FinalizeBattleCopy(void)
{
    u8 index;
    ensure_state();
    if (!gMirageProductionState->active
        || gMirageProductionState->phase != MIRAGE_PHASE_PREPARED)
        return set_status(MIRAGE_STATUS_NOT_ACTIVE);
    restore_party();
    if (!build_selected_player() || !build_selected_enemy(0u)) {
        restore_party();
        return set_status(MIRAGE_STATUS_CONFIG_FAILED);
    }
    gMirageProductionState->battle_local_active = 1u;
    gMirageProductionState->phase = MIRAGE_PHASE_BATTLE;
    if (!FN_CONFIGURE_POLICY(MIRAGE_PRODUCTION_AI_FULL_SMART,
                             gMirageProductionState->gimmick)) {
        gMirageProductionState->battle_local_active = 0u;
        restore_party();
        return set_status(MIRAGE_STATUS_CONFIG_FAILED);
    }
    for (index = 0u; index < 3u; ++index) {
        if (!FN_CONFIGURE_VIRTUAL_ITEM(
                index, gMirageProductionState->virtual_items[index])) {
            FN_PENDING_CLEAR();
            gMirageProductionState->pending_configured = 0u;
            gMirageProductionState->battle_local_active = 0u;
            restore_party();
            return set_status(MIRAGE_STATUS_CONFIG_FAILED);
        }
    }
    gMirageProductionState->pending_configured = 1u;
    return set_status(MIRAGE_STATUS_OK);
}

MIRAGE_EXPORT(MirageProduction_BuildTrainerPartyAdapter)
void MirageProduction_BuildTrainerPartyAdapter(void)
{
    FN_CHANGEKIT_BUILD_TRAINER_PARTY();
    ensure_state();
    if (!gMirageProductionState->active
        || !gMirageProductionState->battle_local_active)
        return;
    if (!build_selected_enemy(1u)) {
        gMirageProductionState->pending_configured = 0u;
        gMirageProductionState->battle_local_active = 0u;
        FN_PENDING_CLEAR();
    }
}

MIRAGE_EXPORT(MirageProduction_LoadProperAbilityBattleDataAdapter)
void MirageProduction_LoadProperAbilityBattleDataAdapter(void)
{
    u8 battler;
    u16 party_slot;
    u8 source;

    /* Preserve the complete Stage35 ChangeKit chain exactly once.  Its own
     * authored trainer handling runs first; Mirage only owns an active
     * opponent selected from the challenge-local SPECIAL6 party. */
    FN_CHANGEKIT_LOAD_PROPER_ABILITY();
    ensure_state();
    if (!gMirageProductionState->active
        || !gMirageProductionState->battle_local_active)
        return;
    battler = G_ACTIVE_BATTLER;
    if (battler >= 4u || battler >= G_BATTLERS_COUNT
        || (battler & 1u) == 0u
        || (G_ABSENT_BATTLER_FLAGS & (1u << battler)) != 0u)
        return;
    party_slot = G_BATTLER_PARTY_INDEXES[battler];
    if (party_slot >= MIRAGE_PRODUCTION_SELECTION_COUNT)
        return;
    source = gMirageProductionState->opponent_slots[party_slot];
    if (source >= MIRAGE_PRODUCTION_RENTAL_COUNT)
        return;
    write_u16(G_BATTLE_MONS
                  + (u32)battler * MIRAGE_BATTLE_MON_SIZE
                  + MIRAGE_BATTLE_MON_ABILITY_OFFSET,
              gMirageProductionRentals[source].ability);
}

MIRAGE_EXPORT(MirageProduction_AfterBattle)
u16 MirageProduction_AfterBattle(void)
{
    u8 round;
    u8 boundary;
    u8 terminal = 0u;
    u8 index;
    u16 status;
    ensure_state();
    if (!gMirageProductionState->active)
        return set_status(MIRAGE_STATUS_NOT_ACTIVE);
    restore_party();
    FN_PENDING_CLEAR();
    gMirageProductionState->pending_configured = 0u;
    gMirageProductionState->battle_local_active = 0u;
    if ((G_BATTLE_OUTCOME & 0x7Fu) != MIRAGE_BATTLE_OUTCOME_WON) {
        if (!persist_exit(1u)) {
            clear_challenge_state(MIRAGE_CLEANUP_LOSS);
            return set_status(MIRAGE_STATUS_PERSIST_FAILED);
        }
        clear_challenge_state(MIRAGE_CLEANUP_LOSS);
        return set_status(MIRAGE_STATUS_LOST);
    }
    round = gMirageProductionState->round;
    boundary = (u8)(gMirageProductionState->battle_in_round == 6u);
    transaction_begin();
    ++G_MIRAGE_LEDGER->current_record[round];
    if (G_MIRAGE_LEDGER->best_record[round]
        < G_MIRAGE_LEDGER->current_record[round])
        G_MIRAGE_LEDGER->best_record[round]
            = G_MIRAGE_LEDGER->current_record[round];
    gMirageProductionState->total_wins = current_total();
    for (index = 0u; index < MIRAGE_PRODUCTION_REWARD_COUNT; ++index) {
        const MirageProductionRewardRow *reward =
            &gMirageProductionRewards[index];
        if (reward->claim_mask != 0u
            && reward->streak == gMirageProductionState->total_wins
            && (G_MIRAGE_LEDGER->reward_claim_bits
                & reward->claim_mask) == 0u
            && reward_unlocked(reward))
            G_MIRAGE_LEDGER->reward_claim_bits |= reward->claim_mask;
    }
    if (boundary) {
        if ((round == 0u && !cert4_unlocked()) || round == 3u)
            terminal = 1u;
        else {
            ++gMirageProductionState->round;
            gMirageProductionState->battle_in_round = 0u;
            gMirageProductionState->gimmick =
                gMirageProductionState->round == 1u
                    ? MIRAGE_PRODUCTION_MECHANIC_MEGA
                    : gMirageProductionState->round == 2u
                        ? MIRAGE_PRODUCTION_MECHANIC_Z : 0u;
        }
    } else {
        ++gMirageProductionState->battle_in_round;
    }
    if (terminal)
        journal_clear();
    else
        journal_write_active();
    ++G_MIRAGE_LEDGER->item_reward_transaction_id;
    gMirageProductionState->last_transaction =
        G_MIRAGE_LEDGER->item_reward_transaction_id;
    if (!transaction_commit((u8)!terminal)) {
        clear_challenge_state(MIRAGE_CLEANUP_ABORT);
        return set_status(MIRAGE_STATUS_PERSIST_FAILED);
    }
    if (terminal) {
        clear_challenge_state(MIRAGE_CLEANUP_COMPLETE);
        return set_status(MIRAGE_STATUS_CHALLENGE_COMPLETE);
    }
    gMirageProductionState->phase = MIRAGE_PHASE_ACTIVE;
    status = boundary ? MIRAGE_STATUS_ROUND_COMPLETE
                      : MIRAGE_STATUS_BATTLE_CONTINUE;
    return set_status(status);
}

MIRAGE_EXPORT(MirageProduction_Complete)
u16 MirageProduction_Complete(void)
{
    ensure_state();
    if (!gMirageProductionState->active)
        return set_status(MIRAGE_STATUS_NOT_ACTIVE);
    restore_runtime_originals();
    if (!persist_exit(0u)) {
        clear_challenge_state(MIRAGE_CLEANUP_COMPLETE);
        return set_status(MIRAGE_STATUS_PERSIST_FAILED);
    }
    clear_challenge_state(MIRAGE_CLEANUP_COMPLETE);
    return set_status(MIRAGE_STATUS_OK);
}

MIRAGE_EXPORT(MirageProduction_Abort)
u16 MirageProduction_Abort(void)
{
    ensure_state();
    restore_runtime_originals();
    if (!gMirageProductionState->active) {
        clear_challenge_state(MIRAGE_CLEANUP_ABORT);
        return set_status(MIRAGE_STATUS_OK);
    }
    if (!persist_exit(1u)) {
        clear_challenge_state(MIRAGE_CLEANUP_ABORT);
        return set_status(MIRAGE_STATUS_PERSIST_FAILED);
    }
    clear_challenge_state(MIRAGE_CLEANUP_ABORT);
    return set_status(MIRAGE_STATUS_OK);
}

MIRAGE_EXPORT(MirageProduction_Recover)
u16 MirageProduction_Recover(void)
{
    u16 payload;
    u8 index;
    ensure_state();
    if (!ledger_valid())
        return set_status(MIRAGE_STATUS_SAVE_INVALID);
    if (!journal_is_active()) {
        if (journal_has_bytes())
            return set_status(MIRAGE_STATUS_SAVE_INVALID);
        if (gMirageProductionState->active)
            return MirageProduction_Abort();
        FN_PENDING_CLEAR();
        return set_status(MIRAGE_STATUS_NOT_ACTIVE);
    }
    payload = G_MIRAGE_LEDGER->current_record[6];
    restore_party();
    initialize_state();
    gMirageProductionState->badge_snapshot = (u8)payload;
    gMirageProductionState->badge_snapshot_valid = 1u;
    write_badges((u8)payload);
    transaction_begin();
    for (index = 0u; index < 4u; ++index)
        G_MIRAGE_LEDGER->current_record[index] = 0u;
    journal_clear();
    ++G_MIRAGE_LEDGER->item_reward_transaction_id;
    if (!transaction_commit(0u)) {
        clear_challenge_state(MIRAGE_CLEANUP_RECOVER);
        return set_status(MIRAGE_STATUS_PERSIST_FAILED);
    }
    clear_challenge_state(MIRAGE_CLEANUP_RECOVER);
    return set_status(MIRAGE_STATUS_RECOVERED);
}

MIRAGE_EXPORT(MirageProduction_MapTransitionRecover)
u16 MirageProduction_MapTransitionRecover(void)
{
    ensure_state();
    if (gMirageProductionState->active)
        return set_status(MIRAGE_STATUS_OK);
    return MirageProduction_Recover();
}

MIRAGE_EXPORT(MirageProduction_SaveLoadAdapter)
u8 MirageProduction_SaveLoadAdapter(u8 save_type)
{
    u8 result = FN_QOL_SAVE_LOAD(save_type);
    u16 recovery;
    if (result != 1u) {
        G_SPECIAL_RESULT = result;
        return result;
    }
    recovery = MirageProduction_Recover();
    G_SPECIAL_RESULT = recovery == MIRAGE_STATUS_NOT_ACTIVE
        ? MIRAGE_STATUS_OK : recovery;
    return result;
}

MIRAGE_EXPORT(MirageProduction_TestInjectPersistenceFault)
u16 MirageProduction_TestInjectPersistenceFault(u8 mode)
{
    ensure_state();
    if (mode > 2u)
        return set_status(MIRAGE_STATUS_BAD_ARGUMENT);
    gMirageProductionState->fault_mode = mode;
    gMirageProductionState->fault_armed = (u8)(mode != 0u);
    return set_status(MIRAGE_STATUS_OK);
}

MIRAGE_EXPORT(MirageProduction_TestWarpToReception)
u16 MirageProduction_TestWarpToReception(void)
{
    FN_SET_WARP_DESTINATION(31, 1, -1, 3, 3);
    FN_RESET_INITIAL_AVATAR();
    FN_WARP_INTO_MAP();
    G_FIELD_CALLBACK = PTR(VoidFn, MIRAGE_DEFAULT_WARP_EXIT_ADDRESS);
    FN_SET_MAIN_CALLBACK2(PTR(VoidFn, MIRAGE_CB2_LOAD_MAP_ADDRESS));
    return set_status(MIRAGE_STATUS_OK);
}
