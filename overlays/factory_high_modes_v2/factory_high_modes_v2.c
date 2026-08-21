/*
 * T25 Factory High Modes V2 production runtime.
 *
 * The 714-byte Factory state is the only persistent challenge owner.  Its
 * existing 600-byte party image remains byte-for-byte intact.  T25 packs the
 * active mode into reward_pending and run options into marker while preserving
 * the historical low three bits.  The 1,280-byte T25 RAM block contains only
 * menu/generator/battle-local state and is never serialized.
 */

#include "factory_high_modes_v2.h"

#include <stddef.h>
#include <stdint.h>

#include "../save_migration/save_migration.h"

typedef uint8_t u8;
typedef int8_t s8;
typedef uint16_t u16;
typedef int16_t s16;
typedef uint32_t u32;

typedef struct FactoryHighModeRow {
    u8 tier;
    u8 format;
    u8 selection_count;
    u8 player_count;
    u8 opponent_count;
    u8 round_count;
    u8 max_milestone;
    u8 unlock;
    u8 mechanic_mask;
    u8 selection_policy;
    u8 swap_policy;
    u8 ai_profile;
    u8 rental_pool;
    u8 opponent_pool;
    u8 slot;
    u8 flags;
} FactoryHighModeRow;

typedef struct FactoryHighRentalRow {
    u16 species;
    u16 item;
    u16 moves[4];
    u16 ability;
    u8 nature;
    u8 ev[6];
    u8 tera_type;
    u8 pool;
    u8 origin;
    u8 restricted_class;
    u8 role;
    u8 gimmick;
    u8 monotype_group;
    u8 weight;
    u8 level;
    u8 iv_policy;
    u8 gmax_allowed;
} FactoryHighRentalRow;

typedef struct FactoryHighProfileRow {
    u8 tier;
    u8 pool;
    u8 format;
    u8 ai_profile;
    u8 generation_policy;
    u8 rental_pool;
    u8 min_species;
    u8 min_types;
    u8 clauses;
    u8 gimmick_policy;
    u8 weight;
    u8 unlock;
} FactoryHighProfileRow;

typedef struct FactoryHighRewardRow {
    u8 tier;
    u8 trigger;
    u16 streak;
    u16 bp;
    u16 item;
    u8 quantity;
    u8 once;
    u8 claim_bit;
    u8 unlock;
} FactoryHighRewardRow;

#include "factory_high_modes_v2_generated.h"

#define PTR(type, address) ((type)(uintptr_t)(address))
#define FACTORY_HIGH_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))

_Static_assert(FACTORY_HIGH_GENERATED_SCHEMA_VERSION == 2u,
               "Factory High generated schema differs");
_Static_assert(FACTORY_HIGH_MODE_COUNT == 24u,
               "Factory High mode count differs");
_Static_assert(FACTORY_HIGH_RENTAL_COUNT == 248u,
               "Factory High rental count differs");
_Static_assert(FACTORY_HIGH_PROFILE_COUNT == 55u,
               "Factory High profile count differs");
_Static_assert(FACTORY_HIGH_REWARD_COUNT == 16u,
               "Factory High reward count differs");
_Static_assert(sizeof(VegaFactoryState) == 714u,
               "Factory save ABI differs");
_Static_assert(offsetof(VegaFactoryState, party_snapshot) == 114u,
               "Factory party snapshot offset differs");

enum {
    HIGH_STATE_MAGIC = 0x324D4846u, /* FHM2 */
    HIGH_LEDGER_ADDRESS = 0x0203D000u,
    HIGH_LEDGER_SIZE = 0x800u,
    HIGH_ROLLBACK_ADDRESS = 0x0203E400u,
    HIGH_PLAYER_PARTY_ADDRESS = 0x020241E4u,
    HIGH_ENEMY_PARTY_ADDRESS = 0x02023F8Cu,
    HIGH_PLAYER_COUNT_ADDRESS = 0x02023F89u,
    HIGH_ENEMY_COUNT_ADDRESS = 0x02023F8Au,
    HIGH_SELECTED_ORDER_ADDRESS = 0x0203C6C8u,
    HIGH_SPECIAL_RESULT_ADDRESS = 0x02037004u,
    HIGH_BATTLE_OUTCOME_ADDRESS = 0x02023DEAu,
    HIGH_SPECIAL_VAR_8000 = 0x02036FECu,
    HIGH_SPECIAL_VAR_8001 = 0x02036FEEu,
    HIGH_MIRAGE_ADDRESS = 0x0203EE00u,
    HIGH_MIRAGE_MAGIC = 0x4D505331u,
    HIGH_MIRAGE_ACTIVE_OFFSET = 0x28u,
    HIGH_PENDING_SHADOW_ADDRESS = 0x0203E040u,
    HIGH_PENDING_AI_OFFSET = 6u,
    HIGH_PENDING_MAGIC = 4u,
    HIGH_PARTY_CAPACITY = 6u,
    HIGH_MON_SIZE = 100u,
    HIGH_BATTLE_MON_SIZE = 88u,
    HIGH_BATTLE_MON_ABILITY = 0x38u,
    HIGH_BATTLE_MONS_ADDRESS = 0x02023B44u,
    HIGH_BATTLERS_COUNT_ADDRESS = 0x02023B2Cu,
    HIGH_PARTY_INDEX_ADDRESS = 0x02023B2Eu,
    HIGH_ABSENT_FLAGS_ADDRESS = 0x02023CD0u,
    HIGH_MARKER_BASE_MASK = 0x07u,
    HIGH_MARKER_GIMMICK_SHIFT = 3u,
    HIGH_MARKER_GIMMICK_MASK = 0x38u,
    HIGH_MARKER_UBER = 0x40u,
    HIGH_PENDING_BATTLE_MASK = 0x07u,
    HIGH_PENDING_MODE_SHIFT = 3u,
    HIGH_PHASE_IDLE = 0u,
    HIGH_PHASE_ENTRY = 1u,
    HIGH_PHASE_DRAFT = 2u,
    HIGH_PHASE_ACTIVE = 3u,
    HIGH_PHASE_BATTLE = 4u,
    HIGH_FORMAT_DOUBLE = 1u,
    HIGH_FORMAT_NPC = 2u,
    HIGH_FORMAT_RANDOM = 3u,
    HIGH_FORMAT_LITTLE = 4u,
    HIGH_FORMAT_MONOTYPE = 5u,
    HIGH_FORMAT_OU = 6u,
    HIGH_FORMAT_CAMOMONS = 7u,
    HIGH_FORMAT_UNRESTRICTED = 8u,
    HIGH_FORMAT_GS = 9u,
    HIGH_FORMAT_REGION_MIX = 10u,
    HIGH_FORMAT_ULTIMATE = 11u,
    HIGH_POLICY_RANDOM = 1u,
    HIGH_POLICY_DRAFT8 = 2u,
    HIGH_POLICY_REGION = 3u,
    HIGH_TIER_TRIAL = 0u,
    HIGH_TIER_STANDARD = 1u,
    HIGH_TIER_FULL = 2u,
    HIGH_TIER_MASTER = 3u,
    HIGH_UNLOCK_STANDARD = 1u,
    HIGH_UNLOCK_FULL = 2u,
    HIGH_UNLOCK_MASTER = 3u,
    HIGH_MECHANIC_NONE = 0u,
    HIGH_MECHANIC_MEGA = 1u,
    HIGH_MECHANIC_Z = 2u,
    HIGH_MECHANIC_DYNAMAX = 3u,
    HIGH_MECHANIC_TERA = 4u,
    HIGH_CLAIM_SPECIAL_49 = 8u,
    HIGH_CLAIM_SHINY_100 = 9u,
    HIGH_CLAIM_TRIAL_ORAN = 10u,
    HIGH_CLAIM_SHINY_DUE = 18u,
    HIGH_TRIAL_RESULT = 9u,
    HIGH_BATTLE_WON = 1u,
    HIGH_DEX_SEEN = 2u,
    HIGH_MON_DATA_SPECIES = 11u,
    HIGH_MON_DATA_HELD_ITEM = 12u,
    HIGH_MON_DATA_MOVE1 = 13u,
    HIGH_MON_DATA_PP1 = 17u,
    HIGH_MON_DATA_PP_BONUSES = 21u,
    HIGH_MON_DATA_EV_HP = 26u,
    HIGH_MON_DATA_IV_HP = 39u,
    HIGH_MON_DATA_LEVEL = 56u,
    HIGH_NATURE_MINT_OFFSET = 0x0Fu,
    HIGH_TERA_TYPE_OFFSET = 0x11u,
    HIGH_MET_BITS_OFFSET = 0x46u,
    HIGH_IV_BITS_OFFSET = 0x48u,
    HIGH_HP_OFFSET = 0x56u,
    HIGH_MAX_HP_OFFSET = 0x58u,
    HIGH_HIDDEN_ABILITY_MASK = 0x1000u,
    HIGH_ABILITY_NUM_MASK = 0x80000000u,
    HIGH_WINDOW_INVALID = 0xFFu,
    HIGH_MENU_TIER = 0u,
    HIGH_MENU_MODE = 1u,
    HIGH_MENU_OPTION = 2u,
    HIGH_MENU_CONFIRM = 3u,
    HIGH_MENU_DRAFT = 4u,
    HIGH_MENU_CANCEL = 0xFFu,
    HIGH_MENU_B = -1,
    HIGH_MENU_NOTHING = -2,
    HIGH_NUM_TASKS = 16u,
    HIGH_COPYWIN_BOTH = 3u,
    HIGH_SE_SELECT = 5u,
    HIGH_SHINY_JOURNAL_MAGIC = 0x54534846u /* FHST */
};

typedef struct HighPokemon {
    u8 bytes[HIGH_MON_SIZE];
} HighPokemon;

struct Task {
    void (*func)(u8 task_id);
    u8 is_active;
    u8 prev;
    u8 next;
    u8 priority;
    s16 data[16];
};

struct WindowTemplate {
    u8 bg;
    u8 tilemap_left;
    u8 tilemap_top;
    u8 width;
    u8 height;
    u8 palette_num;
    u16 base_block;
};

typedef u8 (*U8ArgFn)(u8);
typedef u8 (*FlagGetFn)(u16);
typedef u8 (*FlagChangeFn)(u16);
typedef u8 (*VarSetFn)(u16, u16);
typedef u8 (*ConfigureFactoryFn)(u8, u8, u8);
typedef void (*VoidFn)(void);
typedef u32 (*SaveValidateFn)(const void *, u32);
typedef void (*SaveFinalizeFn)(void *);
typedef void (*SaveInitNewFn)(void *, u8);
typedef u32 (*GetMonDataFn)(const void *, int, u8 *);
typedef void (*SetMonDataFn)(void *, int, const void *);
typedef void (*CreateMonFn)(void *, u16, u8, u8, u8, u32, u8, u32);
typedef u16 (*GetMonAbilityFn)(const void *);
typedef void (*CalculateMonStatsFn)(void *);
typedef u8 (*CalculatePpFn)(u16, u8, u8);
typedef u8 (*CalculatePartyCountFn)(void);
typedef u16 (*SpeciesToNationalFn)(u16);
typedef u8 (*GetSetPokedexFn)(u16, u8);
typedef u8 (*BagFn)(u16, u16);
typedef u8 (*CreateTaskFn)(void (*)(u8), u8);
typedef void (*TaskIdFn)(u8);
typedef u16 (*AddWindowFn)(const struct WindowTemplate *);
typedef void (*WindowU8Fn)(u8);
typedef void (*WindowPairFn)(u8, u8);
typedef void (*TextPrinterFn)(u8, u8, const u8 *, u8, u8, u8, void *);
typedef u8 (*MenuInitCursorFn)(u8, u8, u8, u8, u8, u8, u8);
typedef s8 (*MenuInputFn)(void);
typedef u16 (*GetBaseTileFn)(void);
typedef void (*PlaySeFn)(u16);

#define G_LEDGER PTR(VegaModernSaveData *, HIGH_LEDGER_ADDRESS)
#define G_ROLLBACK PTR(VegaModernSaveData *, HIGH_ROLLBACK_ADDRESS)
#define G_PLAYER_PARTY PTR(HighPokemon *, HIGH_PLAYER_PARTY_ADDRESS)
#define G_ENEMY_PARTY PTR(HighPokemon *, HIGH_ENEMY_PARTY_ADDRESS)
#define G_PLAYER_COUNT PTR(volatile u8 *, HIGH_PLAYER_COUNT_ADDRESS)
#define G_ENEMY_COUNT PTR(volatile u8 *, HIGH_ENEMY_COUNT_ADDRESS)
#define G_SELECTED PTR(volatile u8 *, HIGH_SELECTED_ORDER_ADDRESS)
#define G_SPECIAL_RESULT PTR(volatile u16 *, HIGH_SPECIAL_RESULT_ADDRESS)
#define G_BATTLE_OUTCOME PTR(volatile u8 *, HIGH_BATTLE_OUTCOME_ADDRESS)
#define G_VAR_8000 PTR(volatile u16 *, HIGH_SPECIAL_VAR_8000)
#define G_VAR_8001 PTR(volatile u16 *, HIGH_SPECIAL_VAR_8001)
#define G_TASKS PTR(struct Task *, 0x030050D0u)
#define G_BATTLE_MONS PTR(volatile u8 *, HIGH_BATTLE_MONS_ADDRESS)
#define G_BATTLERS_COUNT PTR(volatile u8 *, HIGH_BATTLERS_COUNT_ADDRESS)
#define G_PARTY_INDEX PTR(volatile u8 *, HIGH_PARTY_INDEX_ADDRESS)
#define G_ABSENT_FLAGS PTR(volatile u8 *, HIGH_ABSENT_FLAGS_ADDRESS)

#define FN_TRY_SAVING_DATA PTR(U8ArgFn, FACTORY_HIGH_ENGINE_TRY_SAVING_DATA)
#define FN_SAVE_INIT_NEW PTR(SaveInitNewFn, FACTORY_HIGH_ENGINE_SAVE_INIT_NEW)
#define FN_SAVE_VALIDATE PTR(SaveValidateFn, FACTORY_HIGH_ENGINE_SAVE_VALIDATE)
#define FN_SAVE_FINALIZE PTR(SaveFinalizeFn, FACTORY_HIGH_ENGINE_SAVE_FINALIZE)
#define FN_FLAG_GET PTR(FlagGetFn, FACTORY_HIGH_ENGINE_FLAG_GET)
#define FN_FLAG_SET PTR(FlagChangeFn, FACTORY_HIGH_ENGINE_FLAG_SET)
#define FN_FLAG_CLEAR PTR(FlagChangeFn, FACTORY_HIGH_ENGINE_FLAG_CLEAR)
#define FN_VAR_SET PTR(VarSetFn, FACTORY_HIGH_ENGINE_VAR_SET)
#define FN_CONFIGURE_FACTORY PTR(ConfigureFactoryFn, FACTORY_HIGH_ENGINE_CONFIGURE_FACTORY)
#define FN_CREATE_MON PTR(CreateMonFn, FACTORY_HIGH_ENGINE_CREATE_MON)
#define FN_SET_MON_DATA PTR(SetMonDataFn, FACTORY_HIGH_ENGINE_SET_MON_DATA)
#define FN_GET_MON_DATA PTR(GetMonDataFn, FACTORY_HIGH_ENGINE_GET_MON_DATA)
#define FN_GET_MON_ABILITY PTR(GetMonAbilityFn, FACTORY_HIGH_ENGINE_GET_MON_ABILITY)
#define FN_CALCULATE_STATS PTR(CalculateMonStatsFn, FACTORY_HIGH_ENGINE_CALCULATE_STATS)
#define FN_CALCULATE_PP PTR(CalculatePpFn, FACTORY_HIGH_ENGINE_CALCULATE_PP)
#define FN_HEAL_PLAYER_PARTY PTR(VoidFn, FACTORY_HIGH_ENGINE_HEAL_PARTY)
#define FN_CALCULATE_PARTY_COUNT PTR(CalculatePartyCountFn, FACTORY_HIGH_ENGINE_PARTY_COUNT)
#define FN_SPECIES_TO_NATIONAL PTR(SpeciesToNationalFn, FACTORY_HIGH_ENGINE_SPECIES_TO_NATIONAL)
#define FN_GET_SET_POKEDEX PTR(GetSetPokedexFn, FACTORY_HIGH_ENGINE_GET_SET_POKEDEX)
#define FN_CHECK_BAG_SPACE PTR(BagFn, FACTORY_HIGH_ENGINE_CHECK_BAG_SPACE)
#define FN_ADD_BAG_ITEM PTR(BagFn, FACTORY_HIGH_ENGINE_ADD_BAG_ITEM)
#define FN_REMOVE_BAG_ITEM PTR(BagFn, FACTORY_HIGH_ENGINE_REMOVE_BAG_ITEM)
#define FN_TRAINER_DELEGATE PTR(VoidFn, FACTORY_HIGH_DELEGATE_TRAINER_PARTY)
#define FN_ABILITY_DELEGATE PTR(VoidFn, FACTORY_HIGH_DELEGATE_ABILITY_LOAD)
#define FN_SAVE_DELEGATE PTR(U8ArgFn, FACTORY_HIGH_DELEGATE_SAVE_LOAD)
#define FN_TRIAL_COMPLETE PTR(u16 (*)(void), FACTORY_HIGH_DELEGATE_TRIAL_COMPLETE)
#define FN_SHINY_CLAIM PTR(u16 (*)(void), FACTORY_HIGH_DELEGATE_SHINY_CLAIM)
#define FN_CREATE_TASK PTR(CreateTaskFn, 0x08076BB5u)
#define FN_DESTROY_TASK PTR(TaskIdFn, 0x08076CA1u)
#define FN_SCRIPT_CONTEXT2_ENABLE PTR(VoidFn, 0x08069201u)
#define FN_ENABLE_BOTH_SCRIPT_CONTEXTS PTR(VoidFn, 0x080693F5u)
#define FN_ADD_WINDOW PTR(AddWindowFn, 0x08003CB1u)
#define FN_REMOVE_WINDOW PTR(WindowU8Fn, 0x08003E09u)
#define FN_COPY_WINDOW_TO_VRAM PTR(WindowPairFn, 0x08003EEDu)
#define FN_PUT_WINDOW_TILEMAP PTR(WindowU8Fn, 0x08003F6Du)
#define FN_FILL_WINDOW_PIXEL_BUFFER PTR(WindowPairFn, 0x08004429u)
#define FN_ADD_TEXT_PRINTER PTR(TextPrinterFn, 0x08002C45u)
#define FN_SCHEDULE_BG_COPY PTR(WindowU8Fn, 0x080F77FDu)
#define FN_DRAW_STD_WINDOW_FRAME PTR(WindowPairFn, 0x080F7F7Du)
#define FN_CLEAR_STD_WINDOW_FRAME PTR(WindowPairFn, 0x080F7FFDu)
#define FN_GET_STD_WINDOW_BASE_TILE PTR(GetBaseTileFn, 0x080F89CDu)
#define FN_MENU_INIT_CURSOR PTR(MenuInitCursorFn, 0x0811030Du)
#define FN_MENU_PROCESS_INPUT PTR(MenuInputFn, 0x08110BF9u)
#define FN_PLAY_SE PTR(PlaySeFn, 0x08071A71u)

static void clear_bytes(volatile void *destination, u32 size)
{
    volatile u8 *out = (volatile u8 *)destination;
    u32 index;
    for (index = 0u; index < size; ++index)
        out[index] = 0u;
}

static void copy_bytes(volatile void *destination,
                       const volatile void *source, u32 size)
{
    volatile u8 *out = (volatile u8 *)destination;
    const volatile u8 *in = (const volatile u8 *)source;
    u32 index;
    for (index = 0u; index < size; ++index)
        out[index] = in[index];
}

static u16 read_u16(const volatile u8 *source)
{
    return (u16)source[0] | (u16)((u16)source[1] << 8);
}

static u32 read_u32(const volatile u8 *source)
{
    return (u32)source[0] | ((u32)source[1] << 8)
        | ((u32)source[2] << 16) | ((u32)source[3] << 24);
}

static void write_u16(volatile u8 *destination, u16 value)
{
    destination[0] = (u8)value;
    destination[1] = (u8)(value >> 8);
}

static void write_u32(volatile u8 *destination, u32 value)
{
    destination[0] = (u8)value;
    destination[1] = (u8)(value >> 8);
    destination[2] = (u8)(value >> 16);
    destination[3] = (u8)(value >> 24);
}

static u32 fnv32(const volatile void *source, u32 size)
{
    const volatile u8 *bytes = (const volatile u8 *)source;
    u32 hash = 2166136261u;
    u32 index;
    for (index = 0u; index < size; ++index) {
        hash ^= bytes[index];
        hash *= 16777619u;
    }
    return hash;
}

static u32 mix32(u32 value)
{
    value ^= value >> 16;
    value *= 0x7FEB352Du;
    value ^= value >> 15;
    value *= 0x846CA68Bu;
    return value ^ (value >> 16);
}

static u16 set_status(u16 status)
{
    gFactoryHighModesV2State->last_status = status;
    *G_SPECIAL_RESULT = status;
    return status;
}

static u8 state_valid(void)
{
    return (u8)(gFactoryHighModesV2State->magic == HIGH_STATE_MAGIC
        && gFactoryHighModesV2State->magic_inverse
            == ~(u32)HIGH_STATE_MAGIC);
}

static void initialize_state(void)
{
    clear_bytes(gFactoryHighModesV2State,
                FACTORY_HIGH_MODES_V2_STATE_SIZE);
    gFactoryHighModesV2State->magic = HIGH_STATE_MAGIC;
    gFactoryHighModesV2State->magic_inverse = ~(u32)HIGH_STATE_MAGIC;
    gFactoryHighModesV2State->window_id = HIGH_WINDOW_INVALID;
}

static void ensure_state(void)
{
    if (!state_valid())
        initialize_state();
}

static u8 ledger_valid(void)
{
    return (u8)(FN_SAVE_VALIDATE(G_LEDGER, HIGH_LEDGER_SIZE) == VEGA_SAVE_OK);
}

static void transaction_begin(void)
{
    copy_bytes(G_ROLLBACK, G_LEDGER, HIGH_LEDGER_SIZE);
}

static u8 persist_current(void)
{
    ++G_LEDGER->generation;
    FN_SAVE_FINALIZE(G_LEDGER);
    if (gFactoryHighModesV2State->persistence_fault) {
        copy_bytes(G_LEDGER, G_ROLLBACK, HIGH_LEDGER_SIZE);
        FN_SAVE_FINALIZE(G_LEDGER);
        return 0u;
    }
    if (gFactoryHighModesV2State->test_mode)
        return 1u;
    if (FN_TRY_SAVING_DATA(0u) != 1u) {
        copy_bytes(G_LEDGER, G_ROLLBACK, HIGH_LEDGER_SIZE);
        FN_SAVE_FINALIZE(G_LEDGER);
        return 0u;
    }
    return 1u;
}

static u8 marker_base(void)
{
    return (u8)(G_LEDGER->factory.marker & HIGH_MARKER_BASE_MASK);
}

static u8 packed_marker(u8 base, u8 option, u8 uber)
{
    u8 value = (u8)(base & HIGH_MARKER_BASE_MASK);
    if (option <= HIGH_MECHANIC_TERA)
        value |= (u8)(option << HIGH_MARKER_GIMMICK_SHIFT);
    if (uber)
        value |= HIGH_MARKER_UBER;
    return (u8)(value & 0x7Fu);
}

static u8 packed_pending(u8 mode, u8 battle)
{
    return (u8)((mode << HIGH_PENDING_MODE_SHIFT)
        | (battle & HIGH_PENDING_BATTLE_MASK));
}

static u8 active_mode(void)
{
    return (u8)(G_LEDGER->factory.reward_pending
        >> HIGH_PENDING_MODE_SHIFT);
}

static u8 active_battle(void)
{
    return (u8)(G_LEDGER->factory.reward_pending
        & HIGH_PENDING_BATTLE_MASK);
}

static u8 mirage_active(void)
{
    volatile u8 *state = PTR(volatile u8 *, HIGH_MIRAGE_ADDRESS);
    return (u8)(read_u32(state) == HIGH_MIRAGE_MAGIC
        && read_u32(state + 4u) == ~(u32)HIGH_MIRAGE_MAGIC
        && state[HIGH_MIRAGE_ACTIVE_OFFSET] != 0u);
}

static u8 unlocked(u8 mode)
{
    const FactoryHighModeRow *row;
    if (mode >= FACTORY_HIGH_MODE_COUNT)
        return 0u;
    row = &gFactoryHighModes[mode];
    if (row->unlock == 0u)
        return 1u;
    if (gFactoryHighModesV2State->test_mode)
        return (u8)((G_LEDGER->factory.unlock_bits
            & (1u << (row->unlock - 1u))) != 0u);
    return FN_FLAG_GET(gFactoryHighUnlockFlags[row->unlock]);
}

static u8 active_owned(void)
{
    return (u8)(state_valid() && gFactoryHighModesV2State->active
        && G_LEDGER->factory.snapshot_valid
        && active_mode() == gFactoryHighModesV2State->mode
        && active_mode() > 0u && active_mode() < FACTORY_HIGH_MODE_COUNT);
}

static u8 rental_legal(u8 mode, u8 option,
                       const FactoryHighRentalRow *row)
{
    const FactoryHighModeRow *config = &gFactoryHighModes[mode];
    if (row->pool != config->rental_pool || row->species == 0u)
        return 0u;
    if (mode == 17u && row->monotype_group != option + 1u)
        return 0u;
    if (mode == 23u && row->gimmick != option)
        return 0u;
    return 1u;
}

static u8 unique_with(const u16 *indices, u8 count, u16 candidate)
{
    const FactoryHighRentalRow *row = &gFactoryHighRentals[candidate];
    u8 index;
    for (index = 0u; index < count; ++index) {
        const FactoryHighRentalRow *prior = &gFactoryHighRentals[indices[index]];
        /* The authored Little/Trial pools intentionally repeat core held
         * items.  Species clause is universal; item-clause policy remains
         * compiled on the selected opponent profile for the battle engine. */
        if (prior->species == row->species)
            return 0u;
    }
    return 1u;
}

static u8 fill_partition(u8 mode, u8 option, u8 origin,
                         u32 seed, u16 *out, u8 count, u8 wanted)
{
    u16 attempt;
    for (attempt = 0u; attempt < FACTORY_HIGH_RENTAL_COUNT
         && count < wanted; ++attempt) {
        u16 index = (u16)((seed + (u32)attempt * 73u)
            % FACTORY_HIGH_RENTAL_COUNT);
        const FactoryHighRentalRow *row = &gFactoryHighRentals[index];
        if (rental_legal(mode, option, row)
            && (origin == 0xFFu || row->origin == origin)
            && unique_with(out, count, index))
            out[count++] = index;
    }
    return count;
}

static u8 generate_candidates(u8 mode, u8 option, u32 seed)
{
    const FactoryHighModeRow *config = &gFactoryHighModes[mode];
    u8 wanted = (u8)((config->selection_policy == HIGH_POLICY_DRAFT8
        || mode == 13u || mode == 15u || mode == 20u
        || mode == 21u || mode == 23u) ? 8u : 6u);
    u8 count = 0u;
    u8 index;
    if (mode == 22u) {
        for (index = 0u; index < 3u; ++index)
            count = fill_partition(mode, option, index,
                                   seed + index * 17u,
                                   gFactoryHighModesV2State->candidates,
                                   count, (u8)(count + 1u));
    } else if (mode == 20u && option == 1u) {
        u16 attempt;
        for (attempt = 0u; attempt < FACTORY_HIGH_RENTAL_COUNT; ++attempt) {
            u16 row_index = (u16)((seed + (u32)attempt * 73u)
                % FACTORY_HIGH_RENTAL_COUNT);
            const FactoryHighRentalRow *row = &gFactoryHighRentals[row_index];
            if (rental_legal(mode, option, row)
                && row->restricted_class == 0u) {
                gFactoryHighModesV2State->candidates[count++] = row_index;
                break;
            }
        }
    } else if (mode == 21u) {
        u16 attempt;
        for (attempt = 0u; attempt < FACTORY_HIGH_RENTAL_COUNT; ++attempt) {
            u16 row_index = (u16)((seed + (u32)attempt * 73u)
                % FACTORY_HIGH_RENTAL_COUNT);
            const FactoryHighRentalRow *row = &gFactoryHighRentals[row_index];
            if (rental_legal(mode, option, row) && row->role == 1u) {
                gFactoryHighModesV2State->candidates[count++] = row_index;
                break;
            }
        }
        for (attempt = 0u; attempt < FACTORY_HIGH_RENTAL_COUNT
             && count < 3u; ++attempt) {
            u16 row_index = (u16)((seed + 19u + (u32)attempt * 73u)
                % FACTORY_HIGH_RENTAL_COUNT);
            const FactoryHighRentalRow *row = &gFactoryHighRentals[row_index];
            if (rental_legal(mode, option, row)
                && row->restricted_class == 0u
                && unique_with(gFactoryHighModesV2State->candidates,
                               count, row_index))
                gFactoryHighModesV2State->candidates[count++] = row_index;
        }
    }
    count = fill_partition(mode, option, 0xFFu, seed,
                           gFactoryHighModesV2State->candidates,
                           count, wanted);
    /* Ultimate has six authored rows per gimmick.  The eight-card display
     * repeats deterministic cards, while final teams remain clause-unique. */
    if (count != 0u && mode == 23u) {
        for (index = count; index < wanted; ++index)
            gFactoryHighModesV2State->candidates[index]
                = gFactoryHighModesV2State->candidates[index % count];
        count = wanted;
    }
    gFactoryHighModesV2State->candidate_count = count;
    gFactoryHighModesV2State->candidate_hash = fnv32(
        gFactoryHighModesV2State->candidates,
        (u32)count * sizeof(u16));
    return (u8)(count == wanted);
}

static u8 selected_legal(u8 mode, const u16 *selected, u8 count)
{
    u8 restricted = 0u;
    u8 support = 0u;
    u8 origins = 0u;
    u8 index;
    if (count != gFactoryHighModes[mode].selection_count)
        return 0u;
    for (index = 0u; index < count; ++index) {
        const FactoryHighRentalRow *row;
        if (selected[index] >= FACTORY_HIGH_RENTAL_COUNT
            || !unique_with(selected, index, selected[index]))
            return 0u;
        row = &gFactoryHighRentals[selected[index]];
        if (!rental_legal(mode, gFactoryHighModesV2State->option, row))
            return 0u;
        restricted += (u8)(row->restricted_class != 0u);
        support += (u8)(row->role == 1u);
        if (row->origin < 3u)
            origins |= (u8)(1u << row->origin);
    }
    if ((mode == 20u && gFactoryHighModesV2State->option == 1u
         && restricted > 2u)
        || (mode == 21u && (restricted > 2u || support == 0u))
        || (mode == 22u && origins != 0x07u))
        return 0u;
    return 1u;
}

static u8 auto_select(void)
{
    u8 mode = gFactoryHighModesV2State->mode;
    u8 wanted = gFactoryHighModes[mode].selection_count;
    u8 candidate_count = gFactoryHighModesV2State->candidate_count;
    u16 combination;
    /* Exhaust every subset; at most 2^8 = 256 finite attempts. */
    for (combination = 1u; combination < (u16)(1u << candidate_count);
         ++combination) {
        u16 selected[6];
        u8 count = 0u;
        u8 index;
        for (index = 0u; index < candidate_count && count < 6u; ++index) {
            if (combination & (1u << index))
                selected[count++] = gFactoryHighModesV2State->candidates[index];
        }
        if (count == wanted && selected_legal(mode, selected, count)) {
            copy_bytes(gFactoryHighModesV2State->selected, selected,
                       (u32)count * sizeof(u16));
            gFactoryHighModesV2State->selected_count = count;
            return 1u;
        }
    }
    return 0u;
}

static u8 select_profile(u8 mode, u32 seed)
{
    u16 attempt;
    u8 pool = gFactoryHighModes[mode].opponent_pool;
    for (attempt = 0u; attempt < FACTORY_HIGH_PROFILE_COUNT; ++attempt) {
        u8 index = (u8)((seed + attempt * 17u)
            % FACTORY_HIGH_PROFILE_COUNT);
        if (gFactoryHighProfiles[index].pool == pool) {
            gFactoryHighModesV2State->profile_index = index;
            return 1u;
        }
    }
    return 0u;
}

static u8 generate_opponent(u32 seed)
{
    u8 mode = gFactoryHighModesV2State->mode;
    u8 wanted = gFactoryHighModes[mode].opponent_count;
    u16 generated[6];
    u8 count = 0u;
    u8 restricted = 0u;
    u16 attempt;
    if (!select_profile(mode, seed))
        return 0u;
    if (mode == 22u) {
        u8 origin;
        for (origin = 0u; origin < 3u; ++origin)
            count = fill_partition(
                mode, gFactoryHighModesV2State->option, origin,
                seed + 31u + origin * 17u, generated, count,
                (u8)(count + 1u));
    } else if (mode == 21u) {
        for (attempt = 0u; attempt < FACTORY_HIGH_RENTAL_COUNT; ++attempt) {
            u16 index = (u16)((seed + 31u + (u32)attempt * 73u)
                % FACTORY_HIGH_RENTAL_COUNT);
            const FactoryHighRentalRow *row = &gFactoryHighRentals[index];
            if (rental_legal(mode, gFactoryHighModesV2State->option, row)
                && row->role == 1u) {
                generated[count++] = index;
                restricted += (u8)(row->restricted_class != 0u);
                break;
            }
        }
    }
    for (attempt = 0u; attempt < FACTORY_HIGH_RENTAL_COUNT
         && count < wanted; ++attempt) {
        u16 index = (u16)((seed + 31u + (u32)attempt * 73u)
            % FACTORY_HIGH_RENTAL_COUNT);
        const FactoryHighRentalRow *row = &gFactoryHighRentals[index];
        if (!rental_legal(mode, gFactoryHighModesV2State->option, row)
            || !unique_with(generated, count, index)
            || (((mode == 20u && gFactoryHighModesV2State->option == 1u)
                 || mode == 21u)
                && row->restricted_class != 0u && restricted >= 2u))
            continue;
        generated[count++] = index;
        restricted += (u8)(row->restricted_class != 0u);
    }
    if (count != wanted)
        return 0u;
    if (wanted == gFactoryHighModes[mode].selection_count
        && !selected_legal(mode, generated, count))
        return 0u;
    copy_bytes(gFactoryHighModesV2State->opponent, generated,
               (u32)count * sizeof(u16));
    gFactoryHighModesV2State->opponent_count = count;
    gFactoryHighModesV2State->opponent_hash = fnv32(
        gFactoryHighModesV2State->opponent,
        (u32)count * sizeof(u16));
    return 1u;
}

static u8 set_exact_ability(HighPokemon *mon, u16 ability)
{
    u8 mode;
    for (mode = 0u; mode < 3u; ++mode) {
        u16 met = read_u16(mon->bytes + HIGH_MET_BITS_OFFSET);
        u32 iv = read_u32(mon->bytes + HIGH_IV_BITS_OFFSET);
        met &= (u16)~HIGH_HIDDEN_ABILITY_MASK;
        iv &= ~HIGH_ABILITY_NUM_MASK;
        if (mode == 1u)
            iv |= HIGH_ABILITY_NUM_MASK;
        else if (mode == 2u)
            met |= HIGH_HIDDEN_ABILITY_MASK;
        write_u16(mon->bytes + HIGH_MET_BITS_OFFSET, met);
        write_u32(mon->bytes + HIGH_IV_BITS_OFFSET, iv);
        if (FN_GET_MON_ABILITY(mon) == ability)
            return 1u;
    }
    /* The authored ID is always restored in the battle-data adapter even
     * when the species table cannot encode it as one of its three selectors. */
    write_u16(mon->bytes + HIGH_MET_BITS_OFFSET,
              (u16)(read_u16(mon->bytes + HIGH_MET_BITS_OFFSET)
                  & (u16)~HIGH_HIDDEN_ABILITY_MASK));
    write_u32(mon->bytes + HIGH_IV_BITS_OFFSET,
              read_u32(mon->bytes + HIGH_IV_BITS_OFFSET)
                  & ~HIGH_ABILITY_NUM_MASK);
    return 1u;
}

static u8 build_rental(HighPokemon *mon, u16 rental_index)
{
    const FactoryHighRentalRow *row;
    u8 index;
    u32 value;
    if (rental_index >= FACTORY_HIGH_RENTAL_COUNT)
        return 0u;
    row = &gFactoryHighRentals[rental_index];
    if (gFactoryHighModesV2State->test_mode) {
        clear_bytes(mon, sizeof(*mon));
        write_u16(mon->bytes, row->species);
        write_u16(mon->bytes + 2u, row->item);
        write_u16(mon->bytes + 4u, row->ability);
        mon->bytes[6] = row->level;
        mon->bytes[7] = row->tera_type;
        return 1u;
    }
    clear_bytes(mon, sizeof(*mon));
    FN_CREATE_MON(mon, row->species, row->level, 31u, 1u,
                  row->nature, 0u, 0u);
    value = row->item;
    FN_SET_MON_DATA(mon, HIGH_MON_DATA_HELD_ITEM, &value);
    value = 0u;
    FN_SET_MON_DATA(mon, HIGH_MON_DATA_PP_BONUSES, &value);
    for (index = 0u; index < 4u; ++index) {
        value = row->moves[index];
        FN_SET_MON_DATA(mon, HIGH_MON_DATA_MOVE1 + index, &value);
        value = FN_CALCULATE_PP(row->moves[index], 0u, index);
        FN_SET_MON_DATA(mon, HIGH_MON_DATA_PP1 + index, &value);
    }
    for (index = 0u; index < 6u; ++index) {
        value = row->ev[index];
        FN_SET_MON_DATA(mon, HIGH_MON_DATA_EV_HP + index, &value);
        value = 31u;
        FN_SET_MON_DATA(mon, HIGH_MON_DATA_IV_HP + index, &value);
    }
    mon->bytes[HIGH_NATURE_MINT_OFFSET] = (u8)(row->nature + 1u);
    mon->bytes[HIGH_TERA_TYPE_OFFSET] = row->tera_type;
    (void)set_exact_ability(mon, row->ability);
    FN_CALCULATE_STATS(mon);
    write_u16(mon->bytes + HIGH_HP_OFFSET,
              read_u16(mon->bytes + HIGH_MAX_HP_OFFSET));
    return (u8)(FN_GET_MON_DATA(mon, HIGH_MON_DATA_SPECIES, NULL)
        == row->species
        && FN_GET_MON_DATA(mon, HIGH_MON_DATA_LEVEL, NULL) == row->level);
}

static void mark_seen(const HighPokemon *mon)
{
    u16 species;
    u16 national;
    if (gFactoryHighModesV2State->test_mode)
        return;
    species = (u16)FN_GET_MON_DATA(mon, HIGH_MON_DATA_SPECIES, NULL);
    national = FN_SPECIES_TO_NATIONAL(species);
    if (national != 0u && national <= VEGA_NATIONAL_DEX_COUNT)
        (void)FN_GET_SET_POKEDEX(national, HIGH_DEX_SEEN);
}

static u8 find_partner(u8 mode, u8 option, u16 *selected,
                       u8 count, u32 seed)
{
    u16 attempt;
    for (attempt = 0u; attempt < FACTORY_HIGH_RENTAL_COUNT; ++attempt) {
        u16 index = (u16)((seed + attempt * 73u)
            % FACTORY_HIGH_RENTAL_COUNT);
        if (rental_legal(mode, option, &gFactoryHighRentals[index])
            && unique_with(selected, count, index)) {
            selected[count] = index;
            return 1u;
        }
    }
    return 0u;
}

static u8 build_player_team(void)
{
    const FactoryHighModeRow *mode =
        &gFactoryHighModes[gFactoryHighModesV2State->mode];
    u16 rows[6];
    u8 count = gFactoryHighModesV2State->selected_count;
    u8 index;
    copy_bytes(rows, gFactoryHighModesV2State->selected,
               (u32)count * sizeof(u16));
    while (count < mode->player_count) {
        if (!find_partner(gFactoryHighModesV2State->mode,
                          gFactoryHighModesV2State->option,
                          rows, count,
                          gFactoryHighModesV2State->seed + count * 43u))
            return 0u;
        ++count;
    }
    clear_bytes(G_PLAYER_PARTY,
                HIGH_PARTY_CAPACITY * sizeof(HighPokemon));
    for (index = 0u; index < count; ++index) {
        if (!build_rental(&G_PLAYER_PARTY[index], rows[index]))
            return 0u;
        gFactoryHighModesV2State->player_abilities[index]
            = gFactoryHighRentals[rows[index]].ability;
        mark_seen(&G_PLAYER_PARTY[index]);
    }
    *G_PLAYER_COUNT = count;
    gFactoryHighModesV2State->player_owned_count = mode->selection_count;
    if (!gFactoryHighModesV2State->test_mode)
        FN_HEAL_PLAYER_PARTY();
    return 1u;
}

static u8 build_enemy_team(void)
{
    u8 index;
    clear_bytes(G_ENEMY_PARTY,
                HIGH_PARTY_CAPACITY * sizeof(HighPokemon));
    for (index = 0u;
         index < gFactoryHighModesV2State->opponent_count; ++index) {
        u16 row = gFactoryHighModesV2State->opponent[index];
        if (!build_rental(&G_ENEMY_PARTY[index], row))
            return 0u;
        gFactoryHighModesV2State->opponent_abilities[index]
            = gFactoryHighRentals[row].ability;
        mark_seen(&G_ENEMY_PARTY[index]);
    }
    *G_ENEMY_COUNT = gFactoryHighModesV2State->opponent_count;
    return 1u;
}

static u8 choose_mechanic(u8 mode, u8 option, u32 seed)
{
    u8 mask = gFactoryHighModes[mode].mechanic_mask;
    u8 choices[5];
    u8 count = 0u;
    u8 value;
    if (mode == 23u)
        return option;
    for (value = 0u; value <= HIGH_MECHANIC_TERA; ++value) {
        if (mask & (1u << value))
            choices[count++] = value;
    }
    return count == 0u ? HIGH_MECHANIC_NONE
        : choices[mix32(seed) % count];
}

static u8 configure_battle(void)
{
    const FactoryHighModeRow *row =
        &gFactoryHighModes[gFactoryHighModesV2State->mode];
    u8 format = 0u;
    u8 rule = 0u;
    u8 mechanic = gFactoryHighModesV2State->configured_gimmick;
    if (row->format == HIGH_FORMAT_DOUBLE || row->format == HIGH_FORMAT_GS)
        format = 1u;
    else if (row->format == HIGH_FORMAT_NPC)
        format = 2u;
    if (row->format == HIGH_FORMAT_LITTLE)
        rule = 1u;
    else if (row->format == HIGH_FORMAT_MONOTYPE)
        rule = 2u;
    else if (row->format == HIGH_FORMAT_UNRESTRICTED)
        rule = (u8)(gFactoryHighModesV2State->option == 1u ? 5u : 3u);
    else if (row->format == HIGH_FORMAT_OU)
        rule = 4u;
    else if (row->format == HIGH_FORMAT_CAMOMONS)
        rule = 6u;
    else if (row->format == HIGH_FORMAT_GS)
        rule = 7u;
    if (gFactoryHighModesV2State->test_mode)
        return 1u;
    if (!FN_CONFIGURE_FACTORY(format, rule, mechanic))
        return 0u;
    if (*PTR(volatile u32 *, HIGH_PENDING_SHADOW_ADDRESS)
        == HIGH_PENDING_MAGIC)
        *PTR(volatile u8 *, HIGH_PENDING_SHADOW_ADDRESS
            + HIGH_PENDING_AI_OFFSET) = row->ai_profile;
    return 1u;
}

static u8 reward_matches(const FactoryHighRewardRow *reward,
                         u8 tier, u16 next_streak, u8 round_count)
{
    if (reward->tier != tier)
        return 0u;
    if (reward->trigger == 0u)
        return (u8)(next_streak != 0u
            && next_streak % round_count == 0u);
    if (reward->trigger == 1u)
        return (u8)(next_streak == round_count);
    return (u8)(next_streak == reward->streak);
}

static u8 bag_has_space(u16 item, u16 quantity)
{
    if (item == 0u || quantity == 0u
        || gFactoryHighModesV2State->test_mode)
        return 1u;
    return FN_CHECK_BAG_SPACE(item, quantity);
}

static u8 precheck_next_reward(void)
{
    u8 mode = gFactoryHighModesV2State->mode;
    const FactoryHighModeRow *config = &gFactoryHighModes[mode];
    u16 next = (u16)(G_LEDGER->factory.current_streak[mode] + 1u);
    u8 index;
    for (index = 0u; index < FACTORY_HIGH_REWARD_COUNT; ++index) {
        const FactoryHighRewardRow *row = &gFactoryHighRewards[index];
        if (reward_matches(row, config->tier, next, config->round_count)
            && row->item != 0u
            && (!row->once || row->claim_bit >= 32u
                || !(G_LEDGER->factory.reward_claim_bits
                    & (1u << row->claim_bit)))
            && !bag_has_space(row->item, row->quantity))
            return 0u;
    }
    return 1u;
}

static u8 precheck_run_rewards(u8 mode)
{
    const FactoryHighModeRow *config = &gFactoryHighModes[mode];
    u8 index;
    for (index = 0u; index < FACTORY_HIGH_REWARD_COUNT; ++index) {
        const FactoryHighRewardRow *row = &gFactoryHighRewards[index];
        if (row->tier == config->tier && row->item != 0u
            && (!row->once || row->claim_bit >= 32u
                || !(G_LEDGER->factory.reward_claim_bits
                    & (1u << row->claim_bit)))
            && !bag_has_space(row->item, row->quantity))
            return 0u;
    }
    return 1u;
}

typedef struct ItemGrant {
    u16 item;
    u8 quantity;
} ItemGrant;

static void rollback_items(const ItemGrant *items, u8 count)
{
    if (gFactoryHighModesV2State->test_mode)
        return;
    while (count != 0u) {
        --count;
        (void)FN_REMOVE_BAG_ITEM(items[count].item,
                                 items[count].quantity);
    }
}

static u8 grant_item(u16 item, u8 quantity,
                     ItemGrant *grants, u8 *grant_count)
{
    if (item == 0u || quantity == 0u)
        return 1u;
    if (*grant_count >= 4u || !bag_has_space(item, quantity))
        return 0u;
    if (!gFactoryHighModesV2State->test_mode
        && !FN_ADD_BAG_ITEM(item, quantity))
        return 0u;
    grants[*grant_count].item = item;
    grants[*grant_count].quantity = quantity;
    ++*grant_count;
    return 1u;
}

static u8 apply_rewards(u8 mode, u16 next_streak,
                        ItemGrant *grants, u8 *grant_count)
{
    const FactoryHighModeRow *config = &gFactoryHighModes[mode];
    u8 index;
    for (index = 0u; index < FACTORY_HIGH_REWARD_COUNT; ++index) {
        const FactoryHighRewardRow *row = &gFactoryHighRewards[index];
        u32 bit = row->claim_bit < 32u ? 1u << row->claim_bit : 0u;
        u32 total;
        if (!reward_matches(row, config->tier, next_streak,
                            config->round_count)
            || (row->once && bit != 0u
                && (G_LEDGER->factory.reward_claim_bits & bit)))
            continue;
        if (row->trigger == 4u) {
            G_LEDGER->factory.reward_claim_bits |=
                1u << HIGH_CLAIM_SHINY_DUE;
        } else {
            if (!grant_item(row->item, row->quantity,
                            grants, grant_count))
                return 0u;
            if (row->once && bit != 0u)
                G_LEDGER->factory.reward_claim_bits |= bit;
        }
        total = (u32)G_LEDGER->factory.battle_points + row->bp;
        G_LEDGER->factory.battle_points =
            (u16)(total > VEGA_BP_CAP ? VEGA_BP_CAP : total);
    }
    /* Existing T24 Factory milestone credit hooks are shared across modes and
     * remain exactly-once through their original claim bits 4..7. */
    for (index = 0u; index < 4u; ++index) {
        u32 bit = 1u << (4u + index);
        if (next_streak == gFactoryHighCreditThresholds[index]
            && !(G_LEDGER->factory.reward_claim_bits & bit)) {
            if (G_LEDGER->encounter_credits[index] != 0xFFFFu)
                ++G_LEDGER->encounter_credits[index];
            G_LEDGER->factory.reward_claim_bits |= bit;
            ++gFactoryHighModesV2State->credit_hook_count;
        }
    }
    return 1u;
}

static void clear_session(void)
{
    u8 index;
    gFactoryHighModesV2State->active = 0u;
    gFactoryHighModesV2State->phase = HIGH_PHASE_IDLE;
    gFactoryHighModesV2State->selected_count = 0u;
    gFactoryHighModesV2State->candidate_count = 0u;
    gFactoryHighModesV2State->opponent_count = 0u;
    gFactoryHighModesV2State->configured_gimmick = 0u;
    gFactoryHighModesV2State->player_gimmick_used = 0u;
    gFactoryHighModesV2State->opponent_gimmick_used = 0u;
    for (index = 0u; index < HIGH_PARTY_CAPACITY; ++index)
        G_SELECTED[index] = 0u;
}

static u16 restore_original(u8 reset_streak)
{
    u8 mode;
    u8 option;
    u8 uber;
    if (!ledger_valid() || !G_LEDGER->factory.snapshot_valid) {
        clear_session();
        return set_status(FACTORY_HIGH_STATUS_NOT_ACTIVE);
    }
    mode = active_mode();
    option = (u8)((G_LEDGER->factory.marker
        & HIGH_MARKER_GIMMICK_MASK) >> HIGH_MARKER_GIMMICK_SHIFT);
    uber = (u8)((G_LEDGER->factory.marker & HIGH_MARKER_UBER) != 0u);
    transaction_begin();
    G_LEDGER->factory.marker = packed_marker(
        VEGA_FACTORY_RESTORE_PENDING, option, uber);
    if (!persist_current())
        return set_status(FACTORY_HIGH_STATUS_PERSIST_FAILED);

    copy_bytes(G_PLAYER_PARTY, G_LEDGER->factory.party_snapshot,
               sizeof(G_LEDGER->factory.party_snapshot));
    *G_PLAYER_COUNT = G_LEDGER->factory.party_count;
    if (reset_streak && mode < FACTORY_HIGH_MODE_COUNT)
        G_LEDGER->factory.current_streak[mode] = 0u;
    transaction_begin();
    clear_bytes(G_LEDGER->factory.party_snapshot,
                sizeof(G_LEDGER->factory.party_snapshot));
    G_LEDGER->factory.party_count = 0u;
    G_LEDGER->factory.snapshot_valid = 0u;
    G_LEDGER->factory.reward_pending = 0u;
    G_LEDGER->factory.marker = VEGA_FACTORY_OUTSIDE;
    ++G_LEDGER->factory.transaction_id;
    if (!persist_current())
        return set_status(FACTORY_HIGH_STATUS_PERSIST_FAILED);
    gFactoryHighModesV2State->party_hash_after =
        fnv32(G_PLAYER_PARTY, HIGH_PARTY_CAPACITY * HIGH_MON_SIZE);
    clear_session();
    return set_status(FACTORY_HIGH_STATUS_OK);
}

static void repair_shiny_journal(void)
{
    volatile u8 *journal = &G_LEDGER->factory.party_snapshot[0][0];
    if (!G_LEDGER->factory.snapshot_valid
        && read_u32(journal) == HIGH_SHINY_JOURNAL_MAGIC) {
        transaction_begin();
        G_LEDGER->factory.current_streak[0] = read_u16(journal + 4u);
        clear_bytes(journal, 8u);
        (void)persist_current();
    }
}

static void claim_shiny_if_due(void)
{
    u32 due = 1u << HIGH_CLAIM_SHINY_DUE;
    u32 claimed = 1u << HIGH_CLAIM_SHINY_100;
    volatile u8 *journal = &G_LEDGER->factory.party_snapshot[0][0];
    u16 original;
    if (!ledger_valid() || G_LEDGER->factory.snapshot_valid
        || !(G_LEDGER->factory.reward_claim_bits & due)
        || (G_LEDGER->factory.reward_claim_bits & claimed))
        return;
    if (gFactoryHighModesV2State->test_mode) {
        transaction_begin();
        G_LEDGER->factory.reward_claim_bits =
            (G_LEDGER->factory.reward_claim_bits | claimed) & ~due;
        (void)persist_current();
        return;
    }
    original = G_LEDGER->factory.current_streak[0];
    transaction_begin();
    write_u32(journal, HIGH_SHINY_JOURNAL_MAGIC);
    write_u16(journal + 4u, original);
    G_LEDGER->factory.current_streak[0] = 100u;
    if (!persist_current())
        return;
    (void)FN_SHINY_CLAIM();
    repair_shiny_journal();
    if (G_LEDGER->factory.reward_claim_bits & claimed) {
        transaction_begin();
        G_LEDGER->factory.reward_claim_bits &= ~due;
        (void)persist_current();
    }
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_Probe)
u32 FactoryHighModesV2_Probe(u32 selector)
{
    ensure_state();
    if (selector == FACTORY_HIGH_PROBE_ABI)
        return FACTORY_HIGH_MODES_V2_ABI_VERSION;
    if (selector == FACTORY_HIGH_PROBE_STATE_ADDRESS)
        return FACTORY_HIGH_MODES_V2_STATE_ADDRESS;
    if (selector == FACTORY_HIGH_PROBE_LEDGER_ADDRESS)
        return HIGH_LEDGER_ADDRESS;
    if (selector == FACTORY_HIGH_PROBE_MODE_COUNT)
        return FACTORY_HIGH_MODE_COUNT;
    if (selector == FACTORY_HIGH_PROBE_RENTAL_COUNT)
        return FACTORY_HIGH_RENTAL_COUNT;
    if (selector == FACTORY_HIGH_PROBE_PROFILE_COUNT)
        return FACTORY_HIGH_PROFILE_COUNT;
    if (selector == FACTORY_HIGH_PROBE_REWARD_COUNT)
        return FACTORY_HIGH_REWARD_COUNT;
    if (selector == FACTORY_HIGH_PROBE_ACTIVE)
        return gFactoryHighModesV2State->active;
    if (selector == FACTORY_HIGH_PROBE_MODE)
        return gFactoryHighModesV2State->mode;
    if (selector == FACTORY_HIGH_PROBE_OPTION)
        return gFactoryHighModesV2State->option;
    if (selector == FACTORY_HIGH_PROBE_BATTLE)
        return active_battle();
    if (selector == FACTORY_HIGH_PROBE_SEED)
        return gFactoryHighModesV2State->seed;
    if (selector == FACTORY_HIGH_PROBE_PARTY_HASH)
        return fnv32(G_PLAYER_PARTY,
                     HIGH_PARTY_CAPACITY * HIGH_MON_SIZE);
    if (selector == FACTORY_HIGH_PROBE_CANDIDATE_HASH)
        return gFactoryHighModesV2State->candidate_hash;
    if (selector == FACTORY_HIGH_PROBE_OPPONENT_HASH)
        return gFactoryHighModesV2State->opponent_hash;
    if (selector == FACTORY_HIGH_PROBE_GIMMICK_COUNT)
        return (u32)gFactoryHighModesV2State->player_gimmick_used
            | ((u32)gFactoryHighModesV2State->opponent_gimmick_used << 8);
    if (selector == FACTORY_HIGH_PROBE_CREDIT_HOOK_COUNT)
        return gFactoryHighModesV2State->credit_hook_count;
    if (selector == FACTORY_HIGH_PROBE_DELEGATE_COUNTS)
        return (u32)gFactoryHighModesV2State->trainer_delegate_count
            | ((u32)gFactoryHighModesV2State->ability_delegate_count << 8)
            | ((u32)gFactoryHighModesV2State->save_delegate_count << 16);
    if (selector == FACTORY_HIGH_PROBE_MARKER_PACKED)
        return G_LEDGER->factory.marker;
    if (selector == FACTORY_HIGH_PROBE_REWARD_PENDING_PACKED)
        return G_LEDGER->factory.reward_pending;
    if (selector == FACTORY_HIGH_PROBE_CLAIM_BITS)
        return G_LEDGER->factory.reward_claim_bits;
    if (selector == FACTORY_HIGH_PROBE_BP)
        return G_LEDGER->factory.battle_points;
    if (selector == FACTORY_HIGH_PROBE_TRANSACTION)
        return G_LEDGER->factory.transaction_id;
    if (selector >= FACTORY_HIGH_PROBE_CURRENT_STREAK_BASE
        && selector < FACTORY_HIGH_PROBE_CURRENT_STREAK_BASE
            + FACTORY_HIGH_MODE_COUNT)
        return G_LEDGER->factory.current_streak[
            selector - FACTORY_HIGH_PROBE_CURRENT_STREAK_BASE];
    if (selector >= FACTORY_HIGH_PROBE_BEST_STREAK_BASE
        && selector < FACTORY_HIGH_PROBE_BEST_STREAK_BASE
            + FACTORY_HIGH_MODE_COUNT)
        return G_LEDGER->factory.best_streak[
            selector - FACTORY_HIGH_PROBE_BEST_STREAK_BASE];
    if (selector >= FACTORY_HIGH_PROBE_MODE_ROW_BASE
        && selector < FACTORY_HIGH_PROBE_MODE_ROW_BASE
            + FACTORY_HIGH_MODE_COUNT)
        return (u32)(uintptr_t)&gFactoryHighModes[
            selector - FACTORY_HIGH_PROBE_MODE_ROW_BASE];
    if (selector >= FACTORY_HIGH_PROBE_RENTAL_ROW_BASE
        && selector < FACTORY_HIGH_PROBE_RENTAL_ROW_BASE
            + FACTORY_HIGH_RENTAL_COUNT)
        return (u32)(uintptr_t)&gFactoryHighRentals[
            selector - FACTORY_HIGH_PROBE_RENTAL_ROW_BASE];
    if (selector >= FACTORY_HIGH_PROBE_PROFILE_ROW_BASE
        && selector < FACTORY_HIGH_PROBE_PROFILE_ROW_BASE
            + FACTORY_HIGH_PROFILE_COUNT)
        return (u32)(uintptr_t)&gFactoryHighProfiles[
            selector - FACTORY_HIGH_PROBE_PROFILE_ROW_BASE];
    if (selector >= FACTORY_HIGH_PROBE_REWARD_ROW_BASE
        && selector < FACTORY_HIGH_PROBE_REWARD_ROW_BASE
            + FACTORY_HIGH_REWARD_COUNT)
        return (u32)(uintptr_t)&gFactoryHighRewards[
            selector - FACTORY_HIGH_PROBE_REWARD_ROW_BASE];
    if (selector >= FACTORY_HIGH_PROBE_DIALOGUE_ROW_BASE
        && selector < FACTORY_HIGH_PROBE_DIALOGUE_ROW_BASE
            + FACTORY_HIGH_MODES_V2_DIALOGUE_COUNT)
        return (u32)(uintptr_t)gFactoryHighDialogues[
            selector - FACTORY_HIGH_PROBE_DIALOGUE_ROW_BASE];
    if (selector >= FACTORY_HIGH_PROBE_REQUIREMENT_ROW_BASE
        && selector < FACTORY_HIGH_PROBE_REQUIREMENT_ROW_BASE
            + FACTORY_HIGH_MODES_V2_REQUIREMENT_COUNT)
        return gFactoryHighRequirementKeys[
            selector - FACTORY_HIGH_PROBE_REQUIREMENT_ROW_BASE];
    if (selector >= FACTORY_HIGH_PROBE_BATCH_ROW_BASE
        && selector < FACTORY_HIGH_PROBE_BATCH_ROW_BASE
            + FACTORY_HIGH_MODES_V2_BATCH_COUNT)
        return gFactoryHighBatchKeys[
            selector - FACTORY_HIGH_PROBE_BATCH_ROW_BASE];
    return 0u;
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_EnterSelected)
u16 FactoryHighModesV2_EnterSelected(void)
{
    u8 mode;
    u8 option;
    u8 count;
    ensure_state();
    if (!ledger_valid())
        return set_status(FACTORY_HIGH_STATUS_ERROR);
    if (mirage_active())
        return set_status(FACTORY_HIGH_STATUS_ISOLATION_BUSY);
    if (G_LEDGER->factory.snapshot_valid) {
        u16 recovered = restore_original(1u);
        if (recovered != FACTORY_HIGH_STATUS_OK)
            return recovered;
    }
    mode = gFactoryHighModesV2State->mode;
    option = gFactoryHighModesV2State->option;
    if (mode == 0u)
        return set_status(FACTORY_HIGH_STATUS_TRIAL_DELEGATE);
    if (mode >= FACTORY_HIGH_MODE_COUNT || !unlocked(mode)
        || (mode == 17u && option > 2u)
        || (mode == 20u && option > 1u)
        || (mode == 23u
            && (option < HIGH_MECHANIC_MEGA
                || option > HIGH_MECHANIC_TERA)))
        return set_status(FACTORY_HIGH_STATUS_LOCKED);
    if (!precheck_run_rewards(mode))
        return set_status(FACTORY_HIGH_STATUS_BAG_FULL);
    count = gFactoryHighModesV2State->test_mode
        ? *G_PLAYER_COUNT : FN_CALCULATE_PARTY_COUNT();
    if (count > HIGH_PARTY_CAPACITY)
        return set_status(FACTORY_HIGH_STATUS_INVALID);
    transaction_begin();
    copy_bytes(G_LEDGER->factory.party_snapshot, G_PLAYER_PARTY,
               sizeof(G_LEDGER->factory.party_snapshot));
    G_LEDGER->factory.party_count = count;
    G_LEDGER->factory.snapshot_valid = 1u;
    ++G_LEDGER->factory.transaction_id;
    gFactoryHighModesV2State->configured_gimmick =
        choose_mechanic(mode, option, G_LEDGER->factory.transaction_id);
    G_LEDGER->factory.marker = packed_marker(
        VEGA_FACTORY_SNAPSHOT_COMMITTED,
        gFactoryHighModesV2State->configured_gimmick,
        (u8)(mode == 20u && option == 1u));
    G_LEDGER->factory.reward_pending = packed_pending(mode, 0u);
    if (!persist_current())
        return set_status(FACTORY_HIGH_STATUS_PERSIST_FAILED);
    gFactoryHighModesV2State->seed = mix32(
        G_LEDGER->factory.transaction_id ^ ((u32)mode << 24)
        ^ ((u32)option << 16));
    gFactoryHighModesV2State->party_hash_before =
        fnv32(G_PLAYER_PARTY, HIGH_PARTY_CAPACITY * HIGH_MON_SIZE);
    gFactoryHighModesV2State->phase = HIGH_PHASE_DRAFT;
    if (!generate_candidates(mode, option,
                             gFactoryHighModesV2State->seed)) {
        (void)restore_original(1u);
        return set_status(FACTORY_HIGH_STATUS_ERROR);
    }
    if (gFactoryHighModes[mode].selection_policy == HIGH_POLICY_RANDOM
        && !auto_select()) {
        (void)restore_original(1u);
        return set_status(FACTORY_HIGH_STATUS_ERROR);
    }
    return set_status(FACTORY_HIGH_STATUS_OK);
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_CommitSelection)
u16 FactoryHighModesV2_CommitSelection(void)
{
    u8 mode;
    ensure_state();
    mode = gFactoryHighModesV2State->mode;
    if (!ledger_valid() || mode == 0u || mode >= FACTORY_HIGH_MODE_COUNT
        || marker_base() != VEGA_FACTORY_SNAPSHOT_COMMITTED
        || !G_LEDGER->factory.snapshot_valid
        || !selected_legal(mode, gFactoryHighModesV2State->selected,
                           gFactoryHighModesV2State->selected_count)) {
        (void)restore_original(1u);
        return set_status(FACTORY_HIGH_STATUS_INVALID);
    }
    if (!build_player_team()
        || !generate_opponent(gFactoryHighModesV2State->seed ^ 0xA5A55A5Au)
        || !build_enemy_team()
        || !configure_battle()) {
        (void)restore_original(1u);
        return set_status(FACTORY_HIGH_STATUS_ERROR);
    }
    transaction_begin();
    G_LEDGER->factory.marker = packed_marker(
        VEGA_FACTORY_BATTLE_ACTIVE,
        gFactoryHighModesV2State->configured_gimmick,
        (u8)(mode == 20u && gFactoryHighModesV2State->option == 1u));
    G_LEDGER->factory.reward_pending = packed_pending(mode, 0u);
    if (!persist_current()) {
        (void)restore_original(1u);
        return set_status(FACTORY_HIGH_STATUS_PERSIST_FAILED);
    }
    gFactoryHighModesV2State->active = 1u;
    gFactoryHighModesV2State->battle_in_round = 0u;
    gFactoryHighModesV2State->phase = HIGH_PHASE_ACTIVE;
    return set_status(FACTORY_HIGH_STATUS_OK);
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_PrepareBattle)
u16 FactoryHighModesV2_PrepareBattle(void)
{
    u32 next_seed;
    ensure_state();
    if (!active_owned() || marker_base() != VEGA_FACTORY_BATTLE_ACTIVE)
        return set_status(FACTORY_HIGH_STATUS_NOT_ACTIVE);
    if (!precheck_next_reward())
        return set_status(FACTORY_HIGH_STATUS_BAG_FULL);
    next_seed = gFactoryHighModesV2State->seed
        ^ ((u32)G_LEDGER->factory.current_streak[
            gFactoryHighModesV2State->mode] * 0x9E3779B9u);
    if (!generate_opponent(next_seed) || !build_enemy_team()
        || !configure_battle())
        return set_status(FACTORY_HIGH_STATUS_ERROR);
    if (!gFactoryHighModesV2State->test_mode) {
        FN_HEAL_PLAYER_PARTY();
        *G_BATTLE_OUTCOME = 0u;
    }
    gFactoryHighModesV2State->phase = HIGH_PHASE_BATTLE;
    return set_status(FACTORY_HIGH_STATUS_OK);
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_AfterBattle)
u16 FactoryHighModesV2_AfterBattle(void)
{
    u8 mode;
    const FactoryHighModeRow *config;
    u16 next;
    u8 won;
    ItemGrant grants[4];
    u8 grant_count = 0u;
    u16 result;
    ensure_state();
    if (!active_owned())
        return set_status(FACTORY_HIGH_STATUS_NOT_ACTIVE);
    mode = gFactoryHighModesV2State->mode;
    config = &gFactoryHighModes[mode];
    won = gFactoryHighModesV2State->test_mode
        ? (u8)(*G_BATTLE_OUTCOME == HIGH_BATTLE_WON)
        : (u8)((*G_BATTLE_OUTCOME & 0x7Fu) == HIGH_BATTLE_WON);
    if (!won)
        return restore_original(1u);
    if (marker_base() == VEGA_FACTORY_BATTLE_ACTIVE) {
        transaction_begin();
        G_LEDGER->factory.marker = packed_marker(
            VEGA_FACTORY_RESULT_PENDING,
            gFactoryHighModesV2State->configured_gimmick,
            (u8)(mode == 20u && gFactoryHighModesV2State->option == 1u));
        if (!persist_current())
            return set_status(FACTORY_HIGH_STATUS_PERSIST_FAILED);
    } else if (marker_base() != VEGA_FACTORY_RESULT_PENDING) {
        return set_status(FACTORY_HIGH_STATUS_NOT_ACTIVE);
    }
    transaction_begin();
    next = G_LEDGER->factory.current_streak[mode];
    if (next != 0xFFFFu)
        ++next;
    G_LEDGER->factory.current_streak[mode] = next;
    if (G_LEDGER->factory.best_streak[mode] < next)
        G_LEDGER->factory.best_streak[mode] = next;
    if (!apply_rewards(mode, next, grants, &grant_count)) {
        rollback_items(grants, grant_count);
        copy_bytes(G_LEDGER, G_ROLLBACK, HIGH_LEDGER_SIZE);
        FN_SAVE_FINALIZE(G_LEDGER);
        return set_status(FACTORY_HIGH_STATUS_BAG_FULL);
    }
    gFactoryHighModesV2State->battle_in_round =
        (u8)(next % config->round_count);
    G_LEDGER->factory.reward_pending = packed_pending(
        mode, gFactoryHighModesV2State->battle_in_round);
    G_LEDGER->factory.marker = packed_marker(
        VEGA_FACTORY_BATTLE_ACTIVE,
        gFactoryHighModesV2State->configured_gimmick,
        (u8)(mode == 20u && gFactoryHighModesV2State->option == 1u));
    ++G_LEDGER->factory.transaction_id;
    if (!persist_current()) {
        rollback_items(grants, grant_count);
        return set_status(FACTORY_HIGH_STATUS_PERSIST_FAILED);
    }
    gFactoryHighModesV2State->last_transaction =
        G_LEDGER->factory.transaction_id;
    gFactoryHighModesV2State->phase = HIGH_PHASE_ACTIVE;
    if (next >= config->max_milestone
        && (config->tier != HIGH_TIER_MASTER || next >= 100u)) {
        result = restore_original(0u);
        claim_shiny_if_due();
        return result == FACTORY_HIGH_STATUS_OK
            ? set_status(FACTORY_HIGH_STATUS_COMPLETE) : result;
    }
    if (next % config->round_count == 0u)
        return set_status(FACTORY_HIGH_STATUS_ROUND);
    return set_status(FACTORY_HIGH_STATUS_OK);
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_BeginExchange)
u16 FactoryHighModesV2_BeginExchange(void)
{
    u8 index;
    if (!active_owned() || gFactoryHighModesV2State->opponent_count == 0u)
        return set_status(FACTORY_HIGH_STATUS_NOT_ACTIVE);
    for (index = 0u; index < HIGH_PARTY_CAPACITY; ++index)
        G_SELECTED[index] = 0u;
    *G_VAR_8000 = 0u;
    *G_VAR_8001 = 0u;
    if (!gFactoryHighModesV2State->test_mode) {
        (void)FN_VAR_SET(FACTORY_HIGH_FACILITY_PARTY_SIZE_VAR,
                        gFactoryHighModesV2State->player_owned_count);
    }
    return set_status(FACTORY_HIGH_STATUS_OK);
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_CommitExchange)
u16 FactoryHighModesV2_CommitExchange(void)
{
    u8 slot = gFactoryHighModesV2State->test_mode ? 1u : G_SELECTED[0];
    u16 incoming;
    u8 index;
    if (!active_owned() || slot == 0u
        || slot > gFactoryHighModesV2State->player_owned_count)
        return set_status(FACTORY_HIGH_STATUS_INVALID);
    incoming = gFactoryHighModesV2State->opponent[0];
    for (index = 0u; index < gFactoryHighModesV2State->selected_count; ++index) {
        if (index != slot - 1u
            && gFactoryHighRentals[
                gFactoryHighModesV2State->selected[index]].species
               == gFactoryHighRentals[incoming].species)
            return set_status(FACTORY_HIGH_STATUS_INVALID);
    }
    gFactoryHighModesV2State->selected[slot - 1u] = incoming;
    if (!build_rental(&G_PLAYER_PARTY[slot - 1u], incoming))
        return set_status(FACTORY_HIGH_STATUS_ERROR);
    gFactoryHighModesV2State->player_abilities[slot - 1u]
        = gFactoryHighRentals[incoming].ability;
    if (!gFactoryHighModesV2State->test_mode)
        FN_HEAL_PLAYER_PARTY();
    transaction_begin();
    ++G_LEDGER->factory.transaction_id;
    if (!persist_current())
        return set_status(FACTORY_HIGH_STATUS_PERSIST_FAILED);
    return set_status(FACTORY_HIGH_STATUS_OK);
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_SkipExchange)
u16 FactoryHighModesV2_SkipExchange(void)
{
    if (!active_owned())
        return set_status(FACTORY_HIGH_STATUS_NOT_ACTIVE);
    return set_status(FACTORY_HIGH_STATUS_OK);
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_Retire)
u16 FactoryHighModesV2_Retire(void)
{
    u8 mode;
    if (!active_owned())
        return set_status(FACTORY_HIGH_STATUS_NOT_ACTIVE);
    mode = gFactoryHighModesV2State->mode;
    if (G_LEDGER->factory.current_streak[mode]
        % gFactoryHighModes[mode].round_count != 0u)
        return set_status(FACTORY_HIGH_STATUS_INVALID);
    return restore_original(0u);
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_Abort)
u16 FactoryHighModesV2_Abort(void)
{
    ensure_state();
    if (!G_LEDGER->factory.snapshot_valid) {
        clear_session();
        return set_status(FACTORY_HIGH_STATUS_OK);
    }
    return restore_original(1u);
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_Recover)
u16 FactoryHighModesV2_Recover(void)
{
    ensure_state();
    repair_shiny_journal();
    if (!ledger_valid())
        return set_status(FACTORY_HIGH_STATUS_ERROR);
    if (!G_LEDGER->factory.snapshot_valid) {
        clear_session();
        claim_shiny_if_due();
        return set_status(FACTORY_HIGH_STATUS_NOT_ACTIVE);
    }
    ++gFactoryHighModesV2State->recovery_count;
    return restore_original(1u) == FACTORY_HIGH_STATUS_OK
        ? set_status(FACTORY_HIGH_STATUS_RECOVERED)
        : gFactoryHighModesV2State->last_status;
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_TrialCompleteAdapter)
u16 FactoryHighModesV2_TrialCompleteAdapter(void)
{
    u16 result = FN_TRIAL_COMPLETE();
    u32 bit = 1u << HIGH_CLAIM_TRIAL_ORAN;
    if (result == HIGH_TRIAL_RESULT && ledger_valid()
        && !(G_LEDGER->factory.reward_claim_bits & bit)
        && bag_has_space(FACTORY_HIGH_ITEM_ORAN_BERRY, 3u)) {
        transaction_begin();
        if (FN_ADD_BAG_ITEM(FACTORY_HIGH_ITEM_ORAN_BERRY, 3u)) {
            G_LEDGER->factory.reward_claim_bits |= bit;
            ++G_LEDGER->factory.transaction_id;
            if (!persist_current())
                (void)FN_REMOVE_BAG_ITEM(
                    FACTORY_HIGH_ITEM_ORAN_BERRY, 3u);
        }
    }
    *G_SPECIAL_RESULT = result;
    return result;
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_BuildTrainerPartyAdapter)
void FactoryHighModesV2_BuildTrainerPartyAdapter(void)
{
    ensure_state();
    FN_TRAINER_DELEGATE();
    ++gFactoryHighModesV2State->trainer_delegate_count;
    if (active_owned())
        (void)build_enemy_team();
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_LoadProperAbilityBattleDataAdapter)
void FactoryHighModesV2_LoadProperAbilityBattleDataAdapter(void)
{
    u8 battler;
    ensure_state();
    FN_ABILITY_DELEGATE();
    ++gFactoryHighModesV2State->ability_delegate_count;
    if (!active_owned())
        return;
    for (battler = 0u; battler < *G_BATTLERS_COUNT; ++battler) {
        u8 slot;
        u16 ability;
        if (*G_ABSENT_FLAGS & (1u << battler))
            continue;
        slot = G_PARTY_INDEX[battler];
        if (slot >= HIGH_PARTY_CAPACITY)
            continue;
        ability = (battler & 1u)
            ? gFactoryHighModesV2State->opponent_abilities[slot]
            : gFactoryHighModesV2State->player_abilities[slot];
        write_u16(G_BATTLE_MONS
            + (u32)battler * HIGH_BATTLE_MON_SIZE
            + HIGH_BATTLE_MON_ABILITY, ability);
    }
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_SaveLoadAdapter)
u8 FactoryHighModesV2_SaveLoadAdapter(u8 save_type)
{
    u8 result;
    ensure_state();
    result = FN_SAVE_DELEGATE(save_type);
    ++gFactoryHighModesV2State->save_delegate_count;
    if (result != 1u) {
        *G_SPECIAL_RESULT = result;
        return result;
    }
    initialize_state();
    if (ledger_valid()) {
        repair_shiny_journal();
        if (G_LEDGER->factory.snapshot_valid)
            (void)FactoryHighModesV2_Recover();
        else
            claim_shiny_if_due();
    }
    return result;
}

static void close_window(void)
{
    u8 window = gFactoryHighModesV2State->window_id;
    if (window == HIGH_WINDOW_INVALID)
        return;
    FN_CLEAR_STD_WINDOW_FRAME(window, 1u);
    FN_REMOVE_WINDOW(window);
    FN_SCHEDULE_BG_COPY(0u);
    gFactoryHighModesV2State->window_id = HIGH_WINDOW_INVALID;
}

static void draw_rows(const u8 *const *rows, u8 count)
{
    struct WindowTemplate template;
    u8 window;
    u8 index;
    template.bg = 0u;
    template.tilemap_left = 1u;
    template.tilemap_top = 1u;
    template.width = 20u;
    template.height = (u8)(count * 2u);
    template.palette_num = 15u;
    template.base_block = FN_GET_STD_WINDOW_BASE_TILE();
    close_window();
    window = (u8)FN_ADD_WINDOW(&template);
    gFactoryHighModesV2State->window_id = window;
    FN_FILL_WINDOW_PIXEL_BUFFER(window, 0x11u);
    FN_PUT_WINDOW_TILEMAP(window);
    FN_DRAW_STD_WINDOW_FRAME(window, 0u);
    for (index = 0u; index < count; ++index)
        FN_ADD_TEXT_PRINTER(window, 2u, rows[index], 8u,
                            (u8)(index * 16u), 0u, NULL);
    FN_COPY_WINDOW_TO_VRAM(window, HIGH_COPYWIN_BOTH);
    (void)FN_MENU_INIT_CURSOR(window, 2u, 0u, 0u,
                              count, 0u, 0u);
}

static void show_reception_menu(u8 stage)
{
    const u8 *rows[10];
    u8 count = 0u;
    u8 index;
    gFactoryHighModesV2State->menu_stage = stage;
    if (stage == HIGH_MENU_TIER) {
        for (index = 0u; index < 4u; ++index) {
            u8 first = index == 0u ? 0u : index == 1u ? 4u
                : index == 2u ? 8u : 12u;
            if (unlocked(first)) {
                rows[count] = gFactoryHighTierLabels[index];
                gFactoryHighModesV2State->menu_codes[count++] = index;
            }
        }
    } else if (stage == HIGH_MENU_MODE) {
        for (index = 0u; index < FACTORY_HIGH_MODE_COUNT; ++index) {
            if (gFactoryHighModes[index].tier
                    == gFactoryHighModesV2State->menu_page
                && unlocked(index)) {
                rows[count] = gFactoryHighModeLabels[index];
                gFactoryHighModesV2State->menu_codes[count++] = index;
            }
        }
    } else if (stage == HIGH_MENU_OPTION) {
        u8 mode = gFactoryHighModesV2State->mode;
        if (mode == 17u) {
            for (index = 0u; index < 3u; ++index) {
                rows[count] = gFactoryHighMonotypeLabels[index];
                gFactoryHighModesV2State->menu_codes[count++] = index;
            }
        } else if (mode == 20u) {
            for (index = 0u; index < 2u; ++index) {
                rows[count] = gFactoryHighUberLabels[index];
                gFactoryHighModesV2State->menu_codes[count++] = index;
            }
        } else if (mode == 23u) {
            for (index = 0u; index < 4u; ++index) {
                rows[count] = gFactoryHighUltimateLabels[index];
                gFactoryHighModesV2State->menu_codes[count++]
                    = (u8)(index + 1u);
            }
        }
    } else {
        rows[count] = gFactoryHighTextStart;
        gFactoryHighModesV2State->menu_codes[count++] = 1u;
    }
    rows[count] = gFactoryHighTextCancel;
    gFactoryHighModesV2State->menu_codes[count++] = HIGH_MENU_CANCEL;
    gFactoryHighModesV2State->menu_count = count;
    draw_rows(rows, count);
}

static void finish_menu_task(u8 task_id, u16 result)
{
    close_window();
    gFactoryHighModesV2State->menu_active = 0u;
    FN_DESTROY_TASK(task_id);
    set_status(result);
    FN_ENABLE_BOTH_SCRIPT_CONTEXTS();
}

static void TaskFactoryReception(u8 task_id)
{
    s8 input = FN_MENU_PROCESS_INPUT();
    u8 code;
    if (input == HIGH_MENU_NOTHING)
        return;
    if (input == HIGH_MENU_B) {
        if (gFactoryHighModesV2State->menu_stage == HIGH_MENU_TIER) {
            finish_menu_task(task_id, FACTORY_HIGH_STATUS_CANCELLED);
            return;
        }
        show_reception_menu(
            gFactoryHighModesV2State->menu_stage == HIGH_MENU_CONFIRM
                && gFactoryHighModesV2State->mode != 17u
                && gFactoryHighModesV2State->mode != 20u
                && gFactoryHighModesV2State->mode != 23u
                ? HIGH_MENU_MODE
                : gFactoryHighModesV2State->menu_stage - 1u);
        return;
    }
    if ((u8)input >= gFactoryHighModesV2State->menu_count)
        return;
    FN_PLAY_SE(HIGH_SE_SELECT);
    code = gFactoryHighModesV2State->menu_codes[(u8)input];
    if (code == HIGH_MENU_CANCEL) {
        if (gFactoryHighModesV2State->menu_stage == HIGH_MENU_TIER)
            finish_menu_task(task_id, FACTORY_HIGH_STATUS_CANCELLED);
        else
            show_reception_menu(
                gFactoryHighModesV2State->menu_stage == HIGH_MENU_CONFIRM
                    && gFactoryHighModesV2State->mode != 17u
                    && gFactoryHighModesV2State->mode != 20u
                    && gFactoryHighModesV2State->mode != 23u
                    ? HIGH_MENU_MODE
                    : gFactoryHighModesV2State->menu_stage - 1u);
        return;
    }
    if (gFactoryHighModesV2State->menu_stage == HIGH_MENU_TIER) {
        gFactoryHighModesV2State->menu_page = code;
        show_reception_menu(HIGH_MENU_MODE);
    } else if (gFactoryHighModesV2State->menu_stage == HIGH_MENU_MODE) {
        gFactoryHighModesV2State->mode = code;
        gFactoryHighModesV2State->option = 0u;
        if (code == 17u || code == 20u || code == 23u)
            show_reception_menu(HIGH_MENU_OPTION);
        else
            show_reception_menu(HIGH_MENU_CONFIRM);
    } else if (gFactoryHighModesV2State->menu_stage == HIGH_MENU_OPTION) {
        gFactoryHighModesV2State->option = code;
        show_reception_menu(HIGH_MENU_CONFIRM);
    } else {
        finish_menu_task(task_id,
            gFactoryHighModesV2State->mode == 0u
                ? FACTORY_HIGH_STATUS_TRIAL_DELEGATE
                : FACTORY_HIGH_STATUS_HIGH_MODE);
    }
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_FieldReception)
u16 FactoryHighModesV2_FieldReception(void)
{
    u8 task;
    ensure_state();
    if (!ledger_valid())
        return set_status(FACTORY_HIGH_STATUS_ERROR);
    repair_shiny_journal();
    if (G_LEDGER->factory.snapshot_valid) {
        u16 recovered = FactoryHighModesV2_Recover();
        if (recovered != FACTORY_HIGH_STATUS_RECOVERED)
            return recovered;
    }
    claim_shiny_if_due();
    if (mirage_active())
        return set_status(FACTORY_HIGH_STATUS_ISOLATION_BUSY);
    if (gFactoryHighModesV2State->menu_active)
        return set_status(FACTORY_HIGH_STATUS_ERROR);
    task = FN_CREATE_TASK(TaskFactoryReception, 80u);
    if (task >= HIGH_NUM_TASKS)
        return set_status(FACTORY_HIGH_STATUS_ERROR);
    gFactoryHighModesV2State->menu_active = 1u;
    FN_SCRIPT_CONTEXT2_ENABLE();
    show_reception_menu(HIGH_MENU_TIER);
    return set_status(FACTORY_HIGH_STATUS_OK);
}

static void show_draft_menu(void)
{
    const u8 *rows[10];
    u8 count = 0u;
    u8 index;
    for (index = 0u;
         index < gFactoryHighModesV2State->candidate_count; ++index) {
        u8 used = 0u;
        u8 selected;
        for (selected = 0u;
             selected < gFactoryHighModesV2State->selected_count; ++selected) {
            if (gFactoryHighModesV2State->selected[selected]
                == gFactoryHighModesV2State->candidates[index])
                used = 1u;
        }
        if (!used) {
            rows[count] = gFactoryHighRentalLabels[
                gFactoryHighModesV2State->candidates[index]];
            gFactoryHighModesV2State->menu_codes[count++] = index;
        }
    }
    rows[count] = gFactoryHighTextCancel;
    gFactoryHighModesV2State->menu_codes[count++] = HIGH_MENU_CANCEL;
    gFactoryHighModesV2State->menu_count = count;
    draw_rows(rows, count);
}

static void TaskFactoryDraft(u8 task_id)
{
    s8 input;
    u8 code;
    u8 mode = gFactoryHighModesV2State->mode;
    if (gFactoryHighModes[mode].selection_policy == HIGH_POLICY_RANDOM) {
        finish_menu_task(task_id, FACTORY_HIGH_STATUS_OK);
        return;
    }
    input = FN_MENU_PROCESS_INPUT();
    if (input == HIGH_MENU_NOTHING)
        return;
    if (input == HIGH_MENU_B) {
        (void)FactoryHighModesV2_Abort();
        finish_menu_task(task_id, FACTORY_HIGH_STATUS_CANCELLED);
        return;
    }
    if ((u8)input >= gFactoryHighModesV2State->menu_count)
        return;
    code = gFactoryHighModesV2State->menu_codes[(u8)input];
    if (code == HIGH_MENU_CANCEL) {
        (void)FactoryHighModesV2_Abort();
        finish_menu_task(task_id, FACTORY_HIGH_STATUS_CANCELLED);
        return;
    }
    FN_PLAY_SE(HIGH_SE_SELECT);
    if (code >= gFactoryHighModesV2State->candidate_count)
        return;
    gFactoryHighModesV2State->selected[
        gFactoryHighModesV2State->selected_count++] =
            gFactoryHighModesV2State->candidates[code];
    if (gFactoryHighModesV2State->selected_count
        >= gFactoryHighModes[mode].selection_count) {
        if (!selected_legal(mode, gFactoryHighModesV2State->selected,
                            gFactoryHighModesV2State->selected_count)) {
            gFactoryHighModesV2State->selected_count = 0u;
            show_draft_menu();
            return;
        }
        finish_menu_task(task_id, FACTORY_HIGH_STATUS_OK);
        return;
    }
    show_draft_menu();
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_FieldDraft)
u16 FactoryHighModesV2_FieldDraft(void)
{
    u8 task;
    if (gFactoryHighModesV2State->phase != HIGH_PHASE_DRAFT
        || !G_LEDGER->factory.snapshot_valid)
        return set_status(FACTORY_HIGH_STATUS_NOT_ACTIVE);
    task = FN_CREATE_TASK(TaskFactoryDraft, 80u);
    if (task >= HIGH_NUM_TASKS)
        return set_status(FACTORY_HIGH_STATUS_ERROR);
    gFactoryHighModesV2State->menu_active = 1u;
    FN_SCRIPT_CONTEXT2_ENABLE();
    if (gFactoryHighModes[
            gFactoryHighModesV2State->mode].selection_policy
        != HIGH_POLICY_RANDOM)
        show_draft_menu();
    return set_status(FACTORY_HIGH_STATUS_OK);
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_TestInitialize)
u16 FactoryHighModesV2_TestInitialize(void)
{
    u32 index;
    initialize_state();
    gFactoryHighModesV2State->test_mode = 1u;
    clear_bytes(G_LEDGER, HIGH_LEDGER_SIZE);
    FN_SAVE_INIT_NEW(G_LEDGER, 1u);
    G_LEDGER->factory.unlock_bits = 0x07u;
    FN_SAVE_FINALIZE(G_LEDGER);
    clear_bytes(G_PLAYER_PARTY,
                HIGH_PARTY_CAPACITY * sizeof(HighPokemon));
    for (index = 0u;
         index < HIGH_PARTY_CAPACITY * HIGH_MON_SIZE; ++index)
        PTR(volatile u8 *, HIGH_PLAYER_PARTY_ADDRESS)[index]
            = (u8)(index * 37u + 11u);
    *G_PLAYER_COUNT = HIGH_PARTY_CAPACITY;
    *G_ENEMY_COUNT = 0u;
    *G_BATTLE_OUTCOME = 0u;
    gFactoryHighModesV2State->party_hash_before =
        fnv32(G_PLAYER_PARTY, HIGH_PARTY_CAPACITY * HIGH_MON_SIZE);
    return set_status(FACTORY_HIGH_STATUS_OK);
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_TestSetUnlocks)
u16 FactoryHighModesV2_TestSetUnlocks(u32 unlock_bits)
{
    ensure_state();
    transaction_begin();
    G_LEDGER->factory.unlock_bits = unlock_bits & 0x07u;
    return persist_current()
        ? set_status(FACTORY_HIGH_STATUS_OK)
        : set_status(FACTORY_HIGH_STATUS_PERSIST_FAILED);
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_TestEnter)
u16 FactoryHighModesV2_TestEnter(u16 mode, u16 option, u32 seed)
{
    u16 result;
    ensure_state();
    gFactoryHighModesV2State->test_mode = 1u;
    if (mode >= FACTORY_HIGH_MODE_COUNT || option > 4u)
        return set_status(FACTORY_HIGH_STATUS_INVALID);
    gFactoryHighModesV2State->mode = (u8)mode;
    gFactoryHighModesV2State->option = (u8)option;
    result = FactoryHighModesV2_EnterSelected();
    if (result != FACTORY_HIGH_STATUS_OK)
        return result;
    gFactoryHighModesV2State->seed = seed;
    if (!generate_candidates((u8)mode, (u8)option, seed))
        return set_status(FACTORY_HIGH_STATUS_ERROR);
    if (gFactoryHighModes[mode].selection_policy == HIGH_POLICY_RANDOM
        && !auto_select())
        return set_status(FACTORY_HIGH_STATUS_ERROR);
    return set_status(FACTORY_HIGH_STATUS_OK);
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_TestCommitDraft)
u16 FactoryHighModesV2_TestCommitDraft(u32 selection_mask)
{
    u8 index;
    u8 count = 0u;
    u8 mode = gFactoryHighModesV2State->mode;
    if (mode == 0u || mode >= FACTORY_HIGH_MODE_COUNT)
        return set_status(FACTORY_HIGH_STATUS_INVALID);
    if (selection_mask != 0u) {
        for (index = 0u;
             index < gFactoryHighModesV2State->candidate_count
                 && count < HIGH_PARTY_CAPACITY; ++index) {
            if (selection_mask & (1u << index))
                gFactoryHighModesV2State->selected[count++]
                    = gFactoryHighModesV2State->candidates[index];
        }
        gFactoryHighModesV2State->selected_count = count;
    } else if (gFactoryHighModesV2State->selected_count == 0u
               && !auto_select()) {
        return set_status(FACTORY_HIGH_STATUS_INVALID);
    }
    return FactoryHighModesV2_CommitSelection();
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_TestBattleResult)
u16 FactoryHighModesV2_TestBattleResult(u16 won)
{
    u16 prepared = FactoryHighModesV2_PrepareBattle();
    if (prepared != FACTORY_HIGH_STATUS_OK)
        return prepared;
    *G_BATTLE_OUTCOME = (u8)(won ? HIGH_BATTLE_WON : 2u);
    return FactoryHighModesV2_AfterBattle();
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_TestSetPersistenceFault)
u16 FactoryHighModesV2_TestSetPersistenceFault(u16 enabled)
{
    ensure_state();
    if (enabled > 1u)
        return set_status(FACTORY_HIGH_STATUS_INVALID);
    gFactoryHighModesV2State->persistence_fault = (u8)enabled;
    return set_status(FACTORY_HIGH_STATUS_OK);
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_TestReload)
u16 FactoryHighModesV2_TestReload(void)
{
    u8 fault = gFactoryHighModesV2State->persistence_fault;
    initialize_state();
    gFactoryHighModesV2State->test_mode = 1u;
    gFactoryHighModesV2State->persistence_fault = fault;
    return FactoryHighModesV2_Recover();
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_TestSetStreak)
u16 FactoryHighModesV2_TestSetStreak(u16 mode, u16 streak)
{
    if (mode >= FACTORY_HIGH_MODE_COUNT)
        return set_status(FACTORY_HIGH_STATUS_INVALID);
    transaction_begin();
    G_LEDGER->factory.current_streak[mode] = streak;
    if (G_LEDGER->factory.best_streak[mode] < streak)
        G_LEDGER->factory.best_streak[mode] = streak;
    return persist_current()
        ? set_status(FACTORY_HIGH_STATUS_OK)
        : set_status(FACTORY_HIGH_STATUS_PERSIST_FAILED);
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_TestGeneratorAudit)
u32 FactoryHighModesV2_TestGeneratorAudit(u16 mode, u16 option, u32 seed)
{
    u8 candidate_ok;
    u8 select_ok;
    u8 opponent_ok;
    if (mode == 0u || mode >= FACTORY_HIGH_MODE_COUNT || option > 4u)
        return 0u;
    ensure_state();
    gFactoryHighModesV2State->test_mode = 1u;
    gFactoryHighModesV2State->mode = (u8)mode;
    gFactoryHighModesV2State->option = (u8)option;
    gFactoryHighModesV2State->seed = seed;
    gFactoryHighModesV2State->selected_count = 0u;
    candidate_ok = generate_candidates((u8)mode, (u8)option, seed);
    select_ok = candidate_ok ? auto_select() : 0u;
    opponent_ok = select_ok ? generate_opponent(seed ^ 0xA5A55A5Au) : 0u;
    return (u32)candidate_ok
        | ((u32)select_ok << 1)
        | ((u32)opponent_ok << 2)
        | ((u32)gFactoryHighModesV2State->candidate_count << 8)
        | ((u32)gFactoryHighModesV2State->opponent_count << 16)
        | ((u32)gFactoryHighModesV2State->profile_index << 24);
}

FACTORY_HIGH_EXPORT(FactoryHighModesV2_TestPartyHash)
u32 FactoryHighModesV2_TestPartyHash(void)
{
    return fnv32(G_PLAYER_PARTY,
                 HIGH_PARTY_CAPACITY * HIGH_MON_SIZE);
}
