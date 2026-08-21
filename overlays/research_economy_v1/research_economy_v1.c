/*
 * T23 Research Economy V1 production runtime.
 *
 * The save owner begins at the odd address 0x0203D73F.  Do not replace the
 * byte helpers below with packed-struct dereferences: ARM7TDMI halfword/word
 * accesses at that address are not valid.  Runtime-only state is confined to
 * the audited 96-byte EWRAM reservation; this translation unit intentionally
 * has no mutable static storage.
 */

#include "research_economy_v1.h"

#include <stddef.h>
#include <stdint.h>

typedef uint8_t u8;
typedef int8_t s8;
typedef uint16_t u16;
typedef int16_t s16;
typedef uint32_t u32;

typedef struct ResearchEconomyActivityConfig {
    u16 points;
    u16 daily_cap;
    u8 unlock_kind;
    u8 source_kind;
    u16 reserved;
} ResearchEconomyActivityConfig;

typedef struct ResearchEconomyRankConfig {
    u32 threshold;
    u16 reward_item_id;
    u16 reward_quantity;
    u8 unlock_kind;
    u8 reserved[3];
} ResearchEconomyRankConfig;

typedef struct ResearchEconomyShopConfig {
    u16 item_id;
    u16 price;
    u16 quantity;
    u8 unlock_kind;
    u8 stock_kind;
    u8 daily_slot;
    u8 daily_limit;
    u8 once_bit;
    u8 reserved;
    const u8 *row_text;
} ResearchEconomyShopConfig;

/* The build must supply packet-derived tables and all rooted delegates. */
#include "research_economy_v1_generated.h"

#define PTR(type, address) ((type)(uintptr_t)(address))
#define RESEARCH_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))

_Static_assert(RESEARCH_ECONOMY_GENERATED_SCHEMA_VERSION == 1u,
               "Research Economy generated schema differs");
_Static_assert(RESEARCH_ECONOMY_ACTIVITY_COUNT == RESEARCH_ACTIVITY_COUNT,
               "Research Economy activity count differs");
_Static_assert(RESEARCH_ECONOMY_RANK_COUNT == 7u,
               "Research Economy rank count differs");
_Static_assert(RESEARCH_ECONOMY_SHOP_COUNT == 23u,
               "Research Economy shop count differs");
_Static_assert(RESEARCH_ECONOMY_DIALOGUE_COUNT == 35u,
               "Research Economy dialogue count differs");
_Static_assert(sizeof(ResearchEconomyActivityConfig) == 8u,
               "Research Economy activity ABI differs");
_Static_assert(sizeof(ResearchEconomyRankConfig) == 12u,
               "Research Economy rank ABI differs");
_Static_assert(sizeof(ResearchEconomyShopConfig) == 16u,
               "Research Economy shop ABI differs");

enum {
    LEDGER_MAGIC = 0x31534756u,
    LEDGER_VERSION_V1 = 1u,
    LEDGER_VERSION_V2 = 2u,
    LEDGER_MAGIC_OFFSET = 0u,
    LEDGER_VERSION_OFFSET = 4u,
    LEDGER_SIZE_OFFSET = 6u,
    LEDGER_CHECKSUM_OFFSET = 8u,
    LEDGER_KANTO_ACCESS_OFFSET = 16u,
    LEDGER_KANTO_VISITED_OFFSET = 17u,
    LEDGER_HALL_OF_FAME_OFFSET = 18u,
    LEDGER_LEAGUE_II_OFFSET = 21u,
    LEDGER_KANTO_CERT_OFFSET = 24u,
    LEDGER_HATCH_MODE_OFFSET = 29u,
    LEDGER_EXP_SHARE_OFFSET = 30u,
    LEDGER_RESERVED_DEX_PREFIX_OFFSET = 0x41u,
    LEDGER_RESERVED_DEX_PREFIX_SIZE = 3u,
    LEDGER_ACQUISITION_OFFSET = 0x44u,
    LEDGER_ACQUISITION_SIZE = 240u,
    LEDGER_RESERVED_DEX_OFFSET = 0x134u,
    LEDGER_RESERVED_DEX_SIZE = 15u,
    LEDGER_V1_RESERVED_TAIL_SIZE = 193u,
    LEDGER_V2_RESERVED_OFFSET = 0x77Fu,
    LEDGER_V2_RESERVED_SIZE = 129u,
    ACQUISITION_MAGIC = 0x51434156u,
    ACQUISITION_VERSION = 1u,
    DURABLE_LEDGER_CANDIDATE_ADDRESS = 0x02039A14u,
    SAVE_ROLLBACK_ADDRESS = 0x0203E400u,
    TRANSACTION_SCRATCH_ADDRESS = 0x0203E300u
};

enum {
    OWNER_SCHEMA = 0u,
    OWNER_STRUCT_SIZE = 1u,
    OWNER_FLAGS = 2u,
    OWNER_BALANCE = 4u,
    OWNER_RANK = 6u,
    OWNER_MINUTES = 7u,
    OWNER_DAY_SERIAL = 8u,
    OWNER_LIFETIME = 10u,
    OWNER_DAILY = 14u,
    OWNER_RANK_CLAIMS = 26u,
    OWNER_SIMPLE_CLAIMS = 27u,
    OWNER_DAILY_SHOP = 28u,
    OWNER_SHOP_ONCE = 32u,
    OWNER_NEXT_TRANSACTION = 36u,
    OWNER_LAST_GAME_TOKEN = 40u,
    OWNER_PENDING_TRANSACTION = 44u,
    OWNER_PENDING_KIND = 48u,
    OWNER_PENDING_PHASE = 49u,
    OWNER_PENDING_KEY = 50u,
    OWNER_PENDING_AUX = 51u,
    OWNER_PENDING_AMOUNT = 52u,
    OWNER_PENDING_PRE_BALANCE = 54u,
    OWNER_PENDING_PRE_DAILY = 56u,
    OWNER_PENDING_PRE_STOCK = 58u,
    OWNER_RESERVED = 60u
};

enum {
    PENDING_NONE = 0u,
    PENDING_EXISTING_EARN = 1u,
    PENDING_SIMPLE_EARN = 2u,
    PENDING_SPEND = 3u,
    PENDING_RANK = 4u,
    PENDING_PHASE_PREPARED = 1u,
    RESEARCH_DAY_MINUTES = 60u,
    SIMPLE_ACTIVITY_FIRST = RESEARCH_ACTIVITY_BUG,
    SIMPLE_ACTIVITY_COUNT = 3u,
    FLAG_BADGE_1 = 0x0820u,
    FLAG_SHIOU_CLEAR = 0x0824u,
    FLAG_BADGE_5 = 0x0824u,
    FLAG_BADGE_6 = 0x0825u,
    FLAG_BADGE_7 = 0x0826u,
    FLAG_BADGE_8 = 0x0827u,
    FLAG_HALL_OF_FAME = 0x082Cu,
    FLAG_DH_CLEAR = 0x114Bu,
    MON_DATA_PERSONALITY = 0u,
    MON_DATA_SPECIES2 = 11u,
    POKEDEX_FLAG_GET_CAUGHT = 1u,
    TYPE_BUG = 6u,
    BATTLE_OUTCOME_CAUGHT = 7u,
    PARTY_CAPACITY = 6u,
    PARTY_MON_SIZE = 100u,
    BASE_STATS_SIZE = 32u,
    BASE_STATS_TYPE1_OFFSET = 6u,
    BASE_STATS_TYPE2_OFFSET = 7u,
    MENU_PAGE_SIZE = 5u,
    MENU_NOTHING = -2,
    MENU_B = -1,
    WINDOW_INVALID = 0xFFu,
    NUM_TASKS = 16u,
    COPYWIN_BOTH = 3u,
    SE_SELECT = 5u,
    RESULT_NOT_SET = 0xFFFFu,
    VOLATILE_MAGIC = 0x31564552u /* "REV1" */
};

typedef enum SaveStatus {
    SAVE_OK = 0,
    SAVE_EMPTY = 1,
    SAVE_BAD_MAGIC = 2,
    SAVE_UNSUPPORTED_VERSION = 3,
    SAVE_BAD_SIZE = 4,
    SAVE_BAD_CHECKSUM = 5,
    SAVE_INVALID_ARGUMENT = 6,
    SAVE_RESERVED_NONZERO = 15
} SaveStatus;

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

typedef struct ResearchEconomyVolatileState {
    u32 magic;
    u32 wild_pid;
    u16 wild_species;
    u16 game_initial_payout;
    u16 game_pre_coins;
    u16 game_last_remaining;
    u16 last_result;
    u16 selected_catalog;
    u16 test_bag_capacity;
    u8 wild_activity;
    u8 wild_pre_caught;
    u8 wild_armed;
    u8 game_active;
    u8 migration_dirty;
    u8 recovery_blocked;
    u8 test_unlock_all;
    u8 test_persistence_fault;
    u8 eligible_count;
    u8 page;
    u8 window_id;
    u8 menu_active;
    u8 reserved0;
    u8 reserved1;
    u16 eligible[RESEARCH_ECONOMY_SHOP_COUNT];
    u8 balance_text[14];
} ResearchEconomyVolatileState;

_Static_assert(sizeof(struct Task) == 40u, "FireRed Task ABI differs");
_Static_assert(sizeof(struct WindowTemplate) == 8u,
               "FireRed WindowTemplate ABI differs");
_Static_assert(sizeof(ResearchEconomyVolatileState)
                   == RESEARCH_ECONOMY_VOLATILE_SIZE,
               "Research Economy volatile reservation differs");

typedef void (*VoidFn)(void);
typedef u8 (*U8ArgU8Fn)(u8);
typedef u8 (*FlagGetFn)(u16);
typedef u8 (*BagFn)(u16, u16);
typedef u16 (*GetCoinsFn)(void);
typedef void (*AddCoinsFn)(u16);
typedef u32 (*GetMonDataFn)(const void *, int, u8 *);
typedef u16 (*SpeciesToNationalFn)(u16);
typedef u8 (*GetSetPokedexFn)(u16, u8);
typedef u8 (*WildLandFn)(const void *, u8, u8);
typedef u16 (*WildFishingFn)(const void *, u8);
typedef u8 (*WildHiddenFn)(void);
typedef void (*TaskFunc)(u8);
typedef u8 (*CreateTaskFn)(TaskFunc, u8);
typedef void (*TaskIdFn)(u8);
typedef u16 (*AddWindowFn)(const struct WindowTemplate *);
typedef void (*WindowU8Fn)(u8);
typedef void (*WindowPairFn)(u8, u8);
typedef void (*TextPrinterFn)(u8, u8, const u8 *, u8, u8, u8, void *);
typedef u8 (*MenuInitCursorFn)(u8, u8, u8, u8, u8, u8, u8);
typedef s8 (*MenuInputFn)(void);
typedef u16 (*GetBaseTileFn)(void);
typedef void (*PlaySeFn)(u16);

#define G_LEDGER PTR(volatile u8 *, RESEARCH_ECONOMY_LEDGER_ADDRESS)
#define G_OWNER (G_LEDGER + RESEARCH_ECONOMY_OWNER_OFFSET)
#define G_VOLATILE \
    PTR(volatile ResearchEconomyVolatileState *, \
        RESEARCH_ECONOMY_VOLATILE_ADDRESS)
#define G_TRANSACTION_SCRATCH PTR(volatile u8 *, TRANSACTION_SCRATCH_ADDRESS)
#define G_SAVE_ROLLBACK PTR(volatile u8 *, SAVE_ROLLBACK_ADDRESS)
#define G_SPECIAL_RESULT PTR(volatile u16 *, 0x02037004u)
#define G_SPECIAL_VAR_8004 PTR(volatile u16 *, 0x02036FF4u)
#define G_TASKS PTR(struct Task *, 0x030050D0u)
#define G_PARTY_COUNT PTR(volatile u8 *, 0x02023F89u)
#define G_PLAYER_PARTY PTR(const u8 *, 0x020241E4u)
#define G_ENEMY_PARTY PTR(const u8 *, 0x02023F8Cu)
#define G_BATTLE_OUTCOME PTR(volatile u8 *, 0x02023DEAu)
#define G_SAVE_BLOCK2_POINTER PTR(const volatile u8 *, 0x0300504Cu)
#define G_GAME_CORNER_STATE_POINTER PTR(const volatile u8 *, 0x0203F314u)

#define FN_MIRAGE_SAVE_LOAD \
    PTR(U8ArgU8Fn, RESEARCH_ECONOMY_DELEGATE_MIRAGE_SAVE_LOAD)
#define FN_QOL_SAVE PTR(U8ArgU8Fn, RESEARCH_ECONOMY_DELEGATE_QOL_SAVE)
#define FN_MOVE_LAND PTR(WildLandFn, RESEARCH_ECONOMY_DELEGATE_MOVE_LAND)
#define FN_MOVE_FISHING \
    PTR(WildFishingFn, RESEARCH_ECONOMY_DELEGATE_MOVE_FISHING)
#define FN_MOVE_HIDDEN PTR(WildHiddenFn, RESEARCH_ECONOMY_DELEGATE_MOVE_HIDDEN)
#define FN_QOL_WILD_END \
    PTR(VoidFn, RESEARCH_ECONOMY_DELEGATE_QOL_WILD_END)
#define FN_PLAY_TIME PTR(VoidFn, RESEARCH_ECONOMY_DELEGATE_PLAY_TIME)
#define FN_ADD_COINS PTR(AddCoinsFn, RESEARCH_ECONOMY_DELEGATE_ADD_COINS)
#define FN_GET_COINS PTR(GetCoinsFn, 0x080D1671u)
#define FN_FLAG_GET PTR(FlagGetFn, 0x0806DEC5u)
#define FN_CHECK_BAG_SPACE PTR(BagFn, 0x08099949u)
#define FN_ADD_BAG_ITEM PTR(BagFn, 0x08099A8Du)
#define FN_REMOVE_BAG_ITEM PTR(BagFn, 0x08099BE1u)
#define FN_GET_MON_DATA PTR(GetMonDataFn, 0x0803F355u)
#define FN_SPECIES_TO_NATIONAL PTR(SpeciesToNationalFn, 0x08042989u)
#define FN_GET_SET_POKEDEX PTR(GetSetPokedexFn, 0x08088A51u)
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

static const u8 sEmptyText[] = {0xFFu};

static u16 read_u16(const volatile u8 *bytes)
{
    return (u16)((u16)bytes[0] | ((u16)bytes[1] << 8));
}

static u32 read_u32(const volatile u8 *bytes)
{
    return (u32)bytes[0]
        | ((u32)bytes[1] << 8)
        | ((u32)bytes[2] << 16)
        | ((u32)bytes[3] << 24);
}

static void write_u16(volatile u8 *bytes, u16 value)
{
    bytes[0] = (u8)value;
    bytes[1] = (u8)(value >> 8);
}

static void write_u32(volatile u8 *bytes, u32 value)
{
    bytes[0] = (u8)value;
    bytes[1] = (u8)(value >> 8);
    bytes[2] = (u8)(value >> 16);
    bytes[3] = (u8)(value >> 24);
}

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

static u8 bytes_are_zero(const volatile u8 *bytes, u32 size)
{
    u32 index;
    for (index = 0u; index < size; ++index) {
        if (bytes[index] != 0u)
            return 0u;
    }
    return 1u;
}

static u8 erased_or_zero(const volatile u8 *bytes)
{
    u8 all_zero = 1u;
    u8 all_ff = 1u;
    u32 index;
    for (index = 0u; index < RESEARCH_ECONOMY_LEDGER_SIZE; ++index) {
        all_zero = (u8)(all_zero && bytes[index] == 0u);
        all_ff = (u8)(all_ff && bytes[index] == 0xFFu);
    }
    return (u8)(all_zero || all_ff);
}

static u32 acquisition_checksum(const volatile u8 *bytes)
{
    u32 crc = 0xFFFFFFFFu;
    u32 index;
    u8 bit;
    for (index = 0u; index < LEDGER_ACQUISITION_SIZE; ++index) {
        u8 value = (index >= 8u && index < 12u) ? 0u : bytes[index];
        crc ^= value;
        for (bit = 0u; bit < 8u; ++bit)
            crc = (crc >> 1) ^ (0xEDB88320u & (0u - (crc & 1u)));
    }
    return ~crc;
}

static u8 acquisition_valid(const volatile u8 *bytes)
{
    if (bytes_are_zero(bytes, LEDGER_ACQUISITION_SIZE))
        return 1u;
    return (u8)(read_u32(bytes) == ACQUISITION_MAGIC
        && read_u16(bytes + 4u) == ACQUISITION_VERSION
        && read_u16(bytes + 6u) == LEDGER_ACQUISITION_SIZE
        && read_u32(bytes + 8u) == acquisition_checksum(bytes));
}

static u8 configured_daily_shop_limit(u8 slot)
{
    u8 limit = 0u;
    u8 index;
    for (index = 0u; index < RESEARCH_ECONOMY_SHOP_COUNT; ++index) {
        const ResearchEconomyShopConfig *row = &gResearchEconomyShop[index];
        if (row->stock_kind == RESEARCH_STOCK_DAILY_LIMITED
            && row->daily_slot == slot)
            limit = row->daily_limit;
    }
    return limit;
}

static u32 configured_once_mask(void)
{
    u32 mask = 0u;
    u8 index;
    for (index = 0u; index < RESEARCH_ECONOMY_SHOP_COUNT; ++index) {
        u8 bit = gResearchEconomyShop[index].once_bit;
        if (bit < 32u)
            mask |= 1u << bit;
    }
    return mask;
}

static u8 owner_v2_fields_valid(const volatile u8 *owner)
{
    u8 pending_kind = owner[OWNER_PENDING_KIND];
    u8 pending_key = owner[OWNER_PENDING_KEY];
    u8 index;
    if (owner[OWNER_SCHEMA] != 1u
        || owner[OWNER_STRUCT_SIZE] != RESEARCH_ECONOMY_OWNER_SIZE
        || read_u16(owner + OWNER_FLAGS) != 0u
        || read_u16(owner + OWNER_BALANCE) > RESEARCH_ECONOMY_POINT_CAP
        || owner[OWNER_RANK] < 1u
        || owner[OWNER_RANK] > RESEARCH_ECONOMY_RANK_COUNT
        || owner[OWNER_MINUTES] >= RESEARCH_DAY_MINUTES
        || (owner[OWNER_RANK_CLAIMS] & 0x80u) != 0u
        || (owner[OWNER_SIMPLE_CLAIMS]
            & (u8)~((1u << SIMPLE_ACTIVITY_COUNT) - 1u)) != 0u
        || (read_u32(owner + OWNER_SHOP_ONCE)
            & ~configured_once_mask()) != 0u
        || read_u32(owner + OWNER_NEXT_TRANSACTION) == 0u
        || pending_kind > PENDING_RANK
        || !bytes_are_zero(owner + OWNER_RESERVED, 4u))
        return 0u;
    for (index = 0u; index < RESEARCH_ACTIVITY_COUNT; ++index) {
        if (read_u16(owner + OWNER_DAILY + (u32)index * 2u)
            > gResearchEconomyActivities[index].daily_cap)
            return 0u;
    }
    for (index = 0u; index < 4u; ++index) {
        u8 limit = configured_daily_shop_limit(index);
        if (limit == 0u || owner[OWNER_DAILY_SHOP + index] > limit)
            return 0u;
    }
    if (pending_kind == PENDING_NONE)
        return bytes_are_zero(owner + OWNER_PENDING_TRANSACTION, 16u);
    if (owner[OWNER_PENDING_PHASE] != PENDING_PHASE_PREPARED
        || read_u32(owner + OWNER_PENDING_TRANSACTION) == 0u
        || read_u16(owner + OWNER_PENDING_AMOUNT) == 0u)
        return 0u;
    if (pending_kind == PENDING_EXISTING_EARN)
        return (u8)(pending_key < SIMPLE_ACTIVITY_FIRST);
    if (pending_kind == PENDING_SIMPLE_EARN)
        return (u8)(pending_key >= SIMPLE_ACTIVITY_FIRST
            && pending_key < RESEARCH_ACTIVITY_COUNT);
    if (pending_kind == PENDING_SPEND)
        return (u8)(pending_key < RESEARCH_ECONOMY_SHOP_COUNT);
    return (u8)(pending_key < RESEARCH_ECONOMY_RANK_COUNT);
}

static u16 owner_u16(u32 offset)
{
    return read_u16(G_OWNER + offset);
}

static u32 owner_u32(u32 offset)
{
    return read_u32(G_OWNER + offset);
}

static void owner_set_u16(u32 offset, u16 value)
{
    write_u16(G_OWNER + offset, value);
}

static void owner_set_u32(u32 offset, u32 value)
{
    write_u32(G_OWNER + offset, value);
}

static u16 owner_daily(u8 activity)
{
    return owner_u16(OWNER_DAILY + (u32)activity * 2u);
}

static void owner_set_daily(u8 activity, u16 value)
{
    owner_set_u16(OWNER_DAILY + (u32)activity * 2u, value);
}

static void initialize_owner_at(volatile u8 *owner)
{
    clear_bytes(owner, RESEARCH_ECONOMY_OWNER_SIZE);
    owner[OWNER_SCHEMA] = 1u;
    owner[OWNER_STRUCT_SIZE] = RESEARCH_ECONOMY_OWNER_SIZE;
    owner[OWNER_RANK] = 1u;
    write_u32(owner + OWNER_NEXT_TRANSACTION, 1u);
}

static void reset_volatile_state(void)
{
    clear_bytes(G_VOLATILE, sizeof(*G_VOLATILE));
    G_VOLATILE->magic = VOLATILE_MAGIC;
    G_VOLATILE->selected_catalog = 0xFFFFu;
    G_VOLATILE->test_bag_capacity = 0xFFFFu;
    G_VOLATILE->window_id = WINDOW_INVALID;
    G_VOLATILE->last_result = RESULT_NOT_SET;
}

static void ensure_volatile_state(void)
{
    if (G_VOLATILE->magic != VOLATILE_MAGIC)
        reset_volatile_state();
}

static u16 set_result(u16 result)
{
    ensure_volatile_state();
    G_VOLATILE->last_result = result;
    *G_SPECIAL_RESULT = result;
    return result;
}

RESEARCH_EXPORT(ResearchEconomy_SaveChecksum)
u32 ResearchEconomy_SaveChecksum(const void *ledger)
{
    const volatile u8 *bytes = (const volatile u8 *)ledger;
    u32 hash = 2166136261u;
    u32 index;
    if (bytes == (const volatile u8 *)0)
        return 0u;
    for (index = 0u; index < RESEARCH_ECONOMY_LEDGER_SIZE; ++index) {
        u8 value = (index >= LEDGER_CHECKSUM_OFFSET
                    && index < LEDGER_CHECKSUM_OFFSET + 4u)
            ? 0u : bytes[index];
        hash ^= value;
        hash *= 16777619u;
    }
    return hash;
}

RESEARCH_EXPORT(ResearchEconomy_SaveValidate)
u32 ResearchEconomy_SaveValidate(const void *ledger, u32 available_size)
{
    const volatile u8 *bytes = (const volatile u8 *)ledger;
    const volatile u8 *owner;
    u16 version;
    if (bytes == (const volatile u8 *)0)
        return SAVE_INVALID_ARGUMENT;
    if (bytes == (const volatile u8 *)G_LEDGER
        || bytes == PTR(const volatile u8 *,
                        DURABLE_LEDGER_CANDIDATE_ADDRESS)) {
        ensure_volatile_state();
        /* A fixed-ledger v1 finalize is authorized only by this exact full
         * outer-checksum validation.  QOL may normalize unrelated fields
         * before consuming the token, but a corrupt v1 can never self-promote
         * merely by calling Finalize. */
        G_VOLATILE->reserved1 = 0u;
    }
    if (available_size < RESEARCH_ECONOMY_LEDGER_SIZE)
        return SAVE_BAD_SIZE;
    if (erased_or_zero(bytes))
        return SAVE_EMPTY;
    if (read_u32(bytes + LEDGER_MAGIC_OFFSET) != LEDGER_MAGIC)
        return SAVE_BAD_MAGIC;
    version = read_u16(bytes + LEDGER_VERSION_OFFSET);
    if (version != LEDGER_VERSION_V1 && version != LEDGER_VERSION_V2)
        return SAVE_UNSUPPORTED_VERSION;
    if (read_u16(bytes + LEDGER_SIZE_OFFSET)
        != RESEARCH_ECONOMY_LEDGER_SIZE)
        return SAVE_BAD_SIZE;
    if (read_u32(bytes + LEDGER_CHECKSUM_OFFSET)
        != ResearchEconomy_SaveChecksum((const void *)bytes))
        return SAVE_BAD_CHECKSUM;
    if (!bytes_are_zero(bytes + LEDGER_RESERVED_DEX_PREFIX_OFFSET,
                        LEDGER_RESERVED_DEX_PREFIX_SIZE)
        || !acquisition_valid(bytes + LEDGER_ACQUISITION_OFFSET)
        || !bytes_are_zero(bytes + LEDGER_RESERVED_DEX_OFFSET,
                           LEDGER_RESERVED_DEX_SIZE))
        return SAVE_RESERVED_NONZERO;
    if (version == LEDGER_VERSION_V1) {
        if (!bytes_are_zero(bytes + RESEARCH_ECONOMY_OWNER_OFFSET,
                            LEDGER_V1_RESERVED_TAIL_SIZE))
            return SAVE_RESERVED_NONZERO;
        if (bytes == (const volatile u8 *)G_LEDGER
            || bytes == PTR(const volatile u8 *,
                            DURABLE_LEDGER_CANDIDATE_ADDRESS)) {
            /* Preserve the checksum-valid image before QOL normalizes any
             * fields.  Migration persist failure can therefore restore a
             * valid v1 save, not a normalized image with its old checksum. */
            copy_bytes(G_SAVE_ROLLBACK, bytes,
                       RESEARCH_ECONOMY_LEDGER_SIZE);
            G_VOLATILE->reserved1 = 1u;
        }
        return SAVE_OK;
    }
    owner = bytes + RESEARCH_ECONOMY_OWNER_OFFSET;
    if (!owner_v2_fields_valid(owner)
        || !bytes_are_zero(bytes + LEDGER_V2_RESERVED_OFFSET,
                           LEDGER_V2_RESERVED_SIZE))
        return SAVE_RESERVED_NONZERO;
    return SAVE_OK;
}

RESEARCH_EXPORT(ResearchEconomy_SaveFinalize)
void ResearchEconomy_SaveFinalize(void *ledger)
{
    volatile u8 *bytes = (volatile u8 *)ledger;
    u16 version;
    if (bytes == (volatile u8 *)0)
        return;
    version = read_u16(bytes + LEDGER_VERSION_OFFSET);
    if (version == LEDGER_VERSION_V1) {
        /* QOL may normalize fields after v1 validation and before finalize,
         * so the old outer checksum is intentionally not rechecked here. */
        if (read_u32(bytes + LEDGER_MAGIC_OFFSET) != LEDGER_MAGIC
            || read_u16(bytes + LEDGER_SIZE_OFFSET)
                != RESEARCH_ECONOMY_LEDGER_SIZE
            || !bytes_are_zero(bytes + RESEARCH_ECONOMY_OWNER_OFFSET,
                               LEDGER_V1_RESERVED_TAIL_SIZE))
            return;
        ensure_volatile_state();
        if (bytes == G_LEDGER) {
            if (!G_VOLATILE->reserved1)
                return;
        } else if (ResearchEconomy_SaveValidate(
                       (const void *)bytes, RESEARCH_ECONOMY_LEDGER_SIZE)
                   != SAVE_OK) {
            return;
        }
        initialize_owner_at(bytes + RESEARCH_ECONOMY_OWNER_OFFSET);
        G_VOLATILE->reserved1 = 0u;
        G_VOLATILE->migration_dirty = 1u;
        write_u16(bytes + LEDGER_VERSION_OFFSET, LEDGER_VERSION_V2);
    } else if (version != LEDGER_VERSION_V2) {
        return;
    }
    write_u32(bytes + LEDGER_MAGIC_OFFSET, LEDGER_MAGIC);
    write_u16(bytes + LEDGER_VERSION_OFFSET, LEDGER_VERSION_V2);
    write_u16(bytes + LEDGER_SIZE_OFFSET, RESEARCH_ECONOMY_LEDGER_SIZE);
    write_u32(bytes + LEDGER_CHECKSUM_OFFSET, 0u);
    write_u32(bytes + LEDGER_CHECKSUM_OFFSET,
              ResearchEconomy_SaveChecksum((const void *)bytes));
}

RESEARCH_EXPORT(ResearchEconomy_SaveInitNew)
void ResearchEconomy_SaveInitNew(void *ledger, u8 first_badge_owned)
{
    volatile u8 *bytes = (volatile u8 *)ledger;
    if (bytes == (volatile u8 *)0)
        return;
    clear_bytes(bytes, RESEARCH_ECONOMY_LEDGER_SIZE);
    write_u16(bytes + LEDGER_VERSION_OFFSET, LEDGER_VERSION_V2);
    bytes[LEDGER_HATCH_MODE_OFFSET] = 1u;
    bytes[LEDGER_EXP_SHARE_OFFSET] = (u8)(first_badge_owned != 0u);
    initialize_owner_at(bytes + RESEARCH_ECONOMY_OWNER_OFFSET);
    ResearchEconomy_SaveFinalize((void *)bytes);
}

RESEARCH_EXPORT(ResearchEconomy_MigrateV1)
u32 ResearchEconomy_MigrateV1(void *ledger, u32 available_size)
{
    volatile u8 *bytes = (volatile u8 *)ledger;
    u32 status = ResearchEconomy_SaveValidate((const void *)bytes,
                                               available_size);
    if (status != SAVE_OK)
        return status;
    if (read_u16(bytes + LEDGER_VERSION_OFFSET) == LEDGER_VERSION_V2)
        return SAVE_OK;
    ResearchEconomy_SaveFinalize((void *)bytes);
    return ResearchEconomy_SaveValidate((const void *)bytes, available_size);
}

static u8 popcount8(u8 value)
{
    u8 count = 0u;
    while (value != 0u) {
        count = (u8)(count + (value & 1u));
        value >>= 1;
    }
    return count;
}

static u8 flag_get(u16 flag)
{
    ensure_volatile_state();
    if (G_VOLATILE->test_unlock_all)
        return 1u;
    if (G_VOLATILE->reserved0)
        return 0u;
    return FN_FLAG_GET(flag);
}

static u8 hall_of_fame(void)
{
    return (u8)(G_VOLATILE->test_unlock_all
        || G_LEDGER[LEDGER_HALL_OF_FAME_OFFSET]
        || flag_get(FLAG_HALL_OF_FAME));
}

static u8 kanto_access(void)
{
    return (u8)(G_VOLATILE->test_unlock_all
        || G_LEDGER[LEDGER_KANTO_ACCESS_OFFSET]
        || hall_of_fame()
        || (flag_get(FLAG_SHIOU_CLEAR) && flag_get(FLAG_DH_CLEAR)));
}

static u8 unlock_satisfied(u8 kind)
{
    ensure_volatile_state();
    if (G_VOLATILE->test_unlock_all)
        return 1u;
    switch (kind) {
    case RESEARCH_UNLOCK_VEGA_DH_CLEAR:
        return flag_get(FLAG_DH_CLEAR);
    case RESEARCH_UNLOCK_KANTO_EARLY_ACCESS:
        return kanto_access();
    case RESEARCH_UNLOCK_VEGA_BADGE_1:
        return flag_get(FLAG_BADGE_1);
    case RESEARCH_UNLOCK_KANTO_DAYCARE_QUEST:
        return (u8)(kanto_access()
            && G_LEDGER[LEDGER_KANTO_VISITED_OFFSET]);
    case RESEARCH_UNLOCK_VEGA_BADGE_5:
        return flag_get(FLAG_BADGE_5);
    case RESEARCH_UNLOCK_VEGA_BADGE_6:
        return flag_get(FLAG_BADGE_6);
    case RESEARCH_UNLOCK_COMPETITIVE_SUPPLY_UNLOCKED:
        return (u8)(hall_of_fame()
            && popcount8(G_LEDGER[LEDGER_KANTO_CERT_OFFSET]) >= 4u);
    case RESEARCH_UNLOCK_VEGA_BADGE_7:
        return flag_get(FLAG_BADGE_7);
    case RESEARCH_UNLOCK_VEGA_BADGE_8:
        return flag_get(FLAG_BADGE_8);
    case RESEARCH_UNLOCK_KANTO_LEAGUE_CLEAR:
    case RESEARCH_UNLOCK_UB_PARADOX_UNLOCKED:
        return (u8)(G_VOLATILE->test_unlock_all
            || G_LEDGER[LEDGER_LEAGUE_II_OFFSET]);
    case RESEARCH_UNLOCK_KANTO_CERT_1:
        return (u8)(G_VOLATILE->test_unlock_all
            || (G_LEDGER[LEDGER_KANTO_CERT_OFFSET] & 0x01u));
    case RESEARCH_UNLOCK_KANTO_CERT_2:
        return (u8)(G_VOLATILE->test_unlock_all
            || (G_LEDGER[LEDGER_KANTO_CERT_OFFSET] & 0x02u));
    case RESEARCH_UNLOCK_KANTO_CERT_3:
        return (u8)(G_VOLATILE->test_unlock_all
            || (G_LEDGER[LEDGER_KANTO_CERT_OFFSET] & 0x04u));
    case RESEARCH_UNLOCK_VEGA_HALL_OF_FAME:
        return hall_of_fame();
    default:
        return 0u;
    }
}

static u8 recompute_rank(void)
{
    u32 lifetime = owner_u32(OWNER_LIFETIME);
    u8 old_rank = G_OWNER[OWNER_RANK];
    u8 rank = old_rank;
    u8 index;
    for (index = 0u; index < RESEARCH_ECONOMY_RANK_COUNT; ++index) {
        const ResearchEconomyRankConfig *row = &gResearchEconomyRanks[index];
        if (lifetime >= row->threshold && unlock_satisfied(row->unlock_kind))
            rank = (u8)(index + 1u);
    }
    if (rank < old_rank)
        rank = old_rank;
    G_OWNER[OWNER_RANK] = rank;
    return (u8)(rank != old_rank);
}

static void clear_pending(void)
{
    clear_bytes(G_OWNER + OWNER_PENDING_TRANSACTION, 16u);
}

static u8 persist_phase(u8 phase)
{
    ensure_volatile_state();
    ResearchEconomy_SaveFinalize((void *)G_LEDGER);
    if (G_VOLATILE->test_persistence_fault == phase && phase != 0u) {
        G_VOLATILE->test_persistence_fault = 0u;
        return 0u;
    }
    if (G_VOLATILE->reserved0)
        return 1u;
    return (u8)(FN_QOL_SAVE(0u) == 1u);
}

static void snapshot_owner(void)
{
    copy_bytes(G_TRANSACTION_SCRATCH, G_OWNER,
               RESEARCH_ECONOMY_OWNER_SIZE);
}

static void restore_owner_snapshot(void)
{
    copy_bytes(G_OWNER, G_TRANSACTION_SCRATCH,
               RESEARCH_ECONOMY_OWNER_SIZE);
    ResearchEconomy_SaveFinalize((void *)G_LEDGER);
}

static u32 allocate_transaction(void)
{
    u32 transaction = owner_u32(OWNER_NEXT_TRANSACTION);
    u32 next;
    if (transaction == 0u)
        transaction = 1u;
    next = transaction + 1u;
    if (next == 0u)
        next = 1u;
    owner_set_u32(OWNER_NEXT_TRANSACTION, next);
    return transaction;
}

static void prepare_pending(u8 kind, u8 key, u8 aux, u16 amount,
                            u16 pre_stock, u32 source_token)
{
    u32 transaction = allocate_transaction();
    owner_set_u32(OWNER_PENDING_TRANSACTION,
                  source_token != 0u ? source_token : transaction);
    G_OWNER[OWNER_PENDING_KIND] = kind;
    G_OWNER[OWNER_PENDING_PHASE] = PENDING_PHASE_PREPARED;
    G_OWNER[OWNER_PENDING_KEY] = key;
    G_OWNER[OWNER_PENDING_AUX] = aux;
    owner_set_u16(OWNER_PENDING_AMOUNT, amount);
    owner_set_u16(OWNER_PENDING_PRE_BALANCE, owner_u16(OWNER_BALANCE));
    owner_set_u16(OWNER_PENDING_PRE_DAILY,
                  key < RESEARCH_ACTIVITY_COUNT ? owner_daily(key) : 0u);
    owner_set_u16(OWNER_PENDING_PRE_STOCK, pre_stock);
}

static u16 recover_internal(void)
{
    u8 kind;
    u8 key;
    u16 amount;
    u16 pre_balance;
    u16 pre_daily;
    u32 transaction;
    if (ResearchEconomy_SaveValidate((const void *)G_LEDGER,
                                     RESEARCH_ECONOMY_LEDGER_SIZE)
        != SAVE_OK
        || read_u16(G_LEDGER + LEDGER_VERSION_OFFSET) != LEDGER_VERSION_V2)
        return RESEARCH_RESULT_CORRUPT_SAVE;
    kind = G_OWNER[OWNER_PENDING_KIND];
    if (kind == PENDING_NONE) {
        G_VOLATILE->recovery_blocked = 0u;
        return RESEARCH_RESULT_EFFECTLESS;
    }
    snapshot_owner();
    key = G_OWNER[OWNER_PENDING_KEY];
    amount = owner_u16(OWNER_PENDING_AMOUNT);
    pre_balance = owner_u16(OWNER_PENDING_PRE_BALANCE);
    pre_daily = owner_u16(OWNER_PENDING_PRE_DAILY);
    transaction = owner_u32(OWNER_PENDING_TRANSACTION);
    if (kind == PENDING_EXISTING_EARN
        && key < RESEARCH_ACTIVITY_COUNT) {
        u32 lifetime = owner_u32(OWNER_LIFETIME);
        u32 next_lifetime = lifetime + amount;
        u32 balance = (u32)pre_balance + amount;
        u32 daily = (u32)pre_daily + amount;
        if (next_lifetime < lifetime)
            next_lifetime = 0xFFFFFFFFu;
        if (balance > RESEARCH_ECONOMY_POINT_CAP)
            balance = RESEARCH_ECONOMY_POINT_CAP;
        if (daily > gResearchEconomyActivities[key].daily_cap)
            daily = gResearchEconomyActivities[key].daily_cap;
        owner_set_u16(OWNER_BALANCE, (u16)balance);
        owner_set_daily(key, (u16)daily);
        owner_set_u32(OWNER_LIFETIME, next_lifetime);
        if (key == RESEARCH_ACTIVITY_GAME_CORNER)
            owner_set_u32(OWNER_LAST_GAME_TOKEN, transaction);
        (void)recompute_rank();
    }
    /* Simple earn, spend and rank reservations have no applied mutation in
     * the prepared save.  Recovery therefore only releases the reservation. */
    clear_pending();
    if (!persist_phase(0u)) {
        restore_owner_snapshot();
        G_VOLATILE->recovery_blocked = 1u;
        return RESEARCH_RESULT_PERSIST_FAILED;
    }
    G_VOLATILE->recovery_blocked = 0u;
    return RESEARCH_RESULT_SUCCESS;
}

static u8 ensure_save_idle(void)
{
    u32 status;
    ensure_volatile_state();
    status = ResearchEconomy_SaveValidate((const void *)G_LEDGER,
                                           RESEARCH_ECONOMY_LEDGER_SIZE);
    if (status == SAVE_EMPTY) {
        ResearchEconomy_SaveInitNew((void *)G_LEDGER,
                                    flag_get(FLAG_BADGE_1));
        if (!persist_phase(0u)) {
            G_VOLATILE->recovery_blocked = 1u;
            return 0u;
        }
    } else if (status == SAVE_OK
               && read_u16(G_LEDGER + LEDGER_VERSION_OFFSET)
                    == LEDGER_VERSION_V1) {
        if (ResearchEconomy_MigrateV1((void *)G_LEDGER,
                                      RESEARCH_ECONOMY_LEDGER_SIZE)
                != SAVE_OK
            || !persist_phase(0u)) {
            if (G_VOLATILE->migration_dirty)
                copy_bytes(G_LEDGER, G_SAVE_ROLLBACK,
                           RESEARCH_ECONOMY_LEDGER_SIZE);
            G_VOLATILE->migration_dirty = 0u;
            G_VOLATILE->recovery_blocked = 1u;
            return 0u;
        }
        G_VOLATILE->migration_dirty = 0u;
    } else if (status != SAVE_OK) {
        return 0u;
    }
    if (G_OWNER[OWNER_PENDING_KIND] != PENDING_NONE
        || G_VOLATILE->recovery_blocked) {
        u16 recovery = recover_internal();
        if (recovery != RESEARCH_RESULT_SUCCESS
            && recovery != RESEARCH_RESULT_EFFECTLESS)
            return 0u;
    }
    return 1u;
}

RESEARCH_EXPORT(ResearchEconomy_SaveLoadAdapter)
u8 ResearchEconomy_SaveLoadAdapter(u8 save_type)
{
    u8 result;
    u32 status;
    u16 recovery;
    /* Load replaces every runtime provenance/menu state.  Finalize invoked
     * inside the existing QOL->Mirage chain records migration_dirty here. */
    reset_volatile_state();
    result = FN_MIRAGE_SAVE_LOAD(save_type); /* exactly one load delegate */
    if (result != 1u) {
        *G_SPECIAL_RESULT = result;
        return result;
    }
    status = ResearchEconomy_SaveValidate((const void *)G_LEDGER,
                                           RESEARCH_ECONOMY_LEDGER_SIZE);
    if (status != SAVE_OK) {
        set_result(RESEARCH_RESULT_CORRUPT_SAVE);
        return 0u;
    }
    if (read_u16(G_LEDGER + LEDGER_VERSION_OFFSET) == LEDGER_VERSION_V1) {
        if (ResearchEconomy_MigrateV1((void *)G_LEDGER,
                                      RESEARCH_ECONOMY_LEDGER_SIZE)
            != SAVE_OK) {
            set_result(RESEARCH_RESULT_CORRUPT_SAVE);
            return 0u;
        }
    }
    if (G_VOLATILE->migration_dirty) {
        if (!persist_phase(0u)) {
            copy_bytes(G_LEDGER, G_SAVE_ROLLBACK,
                       RESEARCH_ECONOMY_LEDGER_SIZE);
            G_VOLATILE->migration_dirty = 0u;
            G_VOLATILE->recovery_blocked = 1u;
            set_result(RESEARCH_RESULT_PERSIST_FAILED);
            return 0u;
        }
        G_VOLATILE->migration_dirty = 0u;
    }
    recovery = recover_internal();
    if (recovery != RESEARCH_RESULT_SUCCESS
        && recovery != RESEARCH_RESULT_EFFECTLESS) {
        set_result(recovery);
        return 0u;
    }
    set_result(RESEARCH_RESULT_SUCCESS);
    return result;
}

RESEARCH_EXPORT(ResearchEconomy_Recover)
u16 ResearchEconomy_Recover(void)
{
    ensure_volatile_state();
    return set_result(recover_internal());
}

RESEARCH_EXPORT(ResearchEconomy_Probe)
u32 ResearchEconomy_Probe(u32 query)
{
    if (query == 0u)
        return RESEARCH_ECONOMY_ABI_VERSION;
    if (query == 1u)
        return RESEARCH_ECONOMY_LEDGER_ADDRESS;
    if (query == 2u)
        return RESEARCH_ECONOMY_OWNER_OFFSET;
    if (query == 3u)
        return RESEARCH_ECONOMY_VOLATILE_ADDRESS;
    if (query >= 0x100u
        && query < 0x100u + RESEARCH_ECONOMY_DIALOGUE_COUNT)
        return (u32)(uintptr_t)gResearchEconomyDialogues[query - 0x100u];
    if (query >= 0x200u
        && query < 0x200u + RESEARCH_ECONOMY_DIALOGUE_COUNT)
        return gResearchEconomyDialogueBinding[query - 0x200u];
    return 0u;
}

RESEARCH_EXPORT(ResearchEconomy_GetBalance)
u16 ResearchEconomy_GetBalance(void)
{
    u16 balance = ensure_save_idle() ? owner_u16(OWNER_BALANCE) : 0u;
    *G_SPECIAL_RESULT = balance;
    return balance;
}

RESEARCH_EXPORT(ResearchEconomy_GetRank)
u16 ResearchEconomy_GetRank(void)
{
    u8 old_rank;
    if (!ensure_save_idle()) {
        *G_SPECIAL_RESULT = 0u;
        return 0u;
    }
    old_rank = G_OWNER[OWNER_RANK];
    if (recompute_rank()) {
        if (!persist_phase(0u)) {
            G_OWNER[OWNER_RANK] = old_rank;
            ResearchEconomy_SaveFinalize((void *)G_LEDGER);
        }
    }
    *G_SPECIAL_RESULT = G_OWNER[OWNER_RANK];
    return G_OWNER[OWNER_RANK];
}

RESEARCH_EXPORT(ResearchEconomy_MinuteTick)
u16 ResearchEconomy_MinuteTick(void)
{
    u8 minutes;
    u8 index;
    if (!ensure_save_idle())
        return set_result(RESEARCH_RESULT_CORRUPT_SAVE);
    minutes = (u8)(G_OWNER[OWNER_MINUTES] + 1u);
    if (minutes >= RESEARCH_DAY_MINUTES) {
        G_OWNER[OWNER_MINUTES] = 0u;
        owner_set_u16(OWNER_DAY_SERIAL,
                      (u16)(owner_u16(OWNER_DAY_SERIAL) + 1u));
        for (index = 0u; index < RESEARCH_ACTIVITY_COUNT; ++index)
            owner_set_daily(index, 0u);
        G_OWNER[OWNER_SIMPLE_CLAIMS] = 0u;
        clear_bytes(G_OWNER + OWNER_DAILY_SHOP, 4u);
    } else {
        G_OWNER[OWNER_MINUTES] = minutes;
    }
    /* Play time itself is not flash-written every minute.  Recomputing the
     * RAM image checksum keeps the economy and active time in one later save. */
    ResearchEconomy_SaveFinalize((void *)G_LEDGER);
    return set_result(RESEARCH_RESULT_SUCCESS);
}

RESEARCH_EXPORT(ResearchEconomy_CreditActivity)
u16 ResearchEconomy_CreditActivity(u16 activity, u32 source_token,
                                   u16 simple_event)
{
    const ResearchEconomyActivityConfig *row;
    u16 balance;
    u16 daily;
    u16 remaining_daily;
    u16 remaining_balance;
    u16 actual;
    u8 simple;
    u8 simple_bit = 0u;
    u32 lifetime;
    if (!ensure_save_idle())
        return set_result(RESEARCH_RESULT_CORRUPT_SAVE);
    if (activity >= RESEARCH_ACTIVITY_COUNT)
        return set_result(RESEARCH_RESULT_INVALID);
    row = &gResearchEconomyActivities[activity];
    if (!unlock_satisfied(row->unlock_kind))
        return set_result(RESEARCH_RESULT_LOCKED);
    simple = (u8)(activity >= SIMPLE_ACTIVITY_FIRST);
    if (simple) {
        if (!simple_event)
            return set_result(RESEARCH_RESULT_CANCELLED);
        simple_bit = (u8)(1u << (activity - SIMPLE_ACTIVITY_FIRST));
        if (G_OWNER[OWNER_SIMPLE_CLAIMS] & simple_bit)
            return set_result(RESEARCH_RESULT_DAILY_CAP);
    } else if (source_token == 0u) {
        return set_result(RESEARCH_RESULT_INVALID);
    }
    if (activity == RESEARCH_ACTIVITY_GAME_CORNER
        && owner_u32(OWNER_LAST_GAME_TOKEN) == source_token)
        return set_result(RESEARCH_RESULT_EFFECTLESS);
    balance = owner_u16(OWNER_BALANCE);
    daily = owner_daily((u8)activity);
    if (daily >= row->daily_cap)
        return set_result(RESEARCH_RESULT_DAILY_CAP);
    if (balance >= RESEARCH_ECONOMY_POINT_CAP)
        return set_result(RESEARCH_RESULT_CAPACITY);
    remaining_daily = (u16)(row->daily_cap - daily);
    remaining_balance = (u16)(RESEARCH_ECONOMY_POINT_CAP - balance);
    actual = row->points;
    if (actual > remaining_daily)
        actual = remaining_daily;
    if (actual > remaining_balance)
        actual = remaining_balance;
    if (actual == 0u)
        return set_result(RESEARCH_RESULT_DAILY_CAP);
    if (simple && actual != row->points)
        return set_result(remaining_daily < row->points
            ? RESEARCH_RESULT_DAILY_CAP : RESEARCH_RESULT_CAPACITY);

    snapshot_owner();
    prepare_pending(simple ? PENDING_SIMPLE_EARN : PENDING_EXISTING_EARN,
                    (u8)activity, simple_bit, actual,
                    G_OWNER[OWNER_SIMPLE_CLAIMS], source_token);
    if (!persist_phase(1u)) {
        restore_owner_snapshot();
        return set_result(RESEARCH_RESULT_PERSIST_FAILED);
    }
    /* Scratch now represents the durable prepared state. */
    snapshot_owner();
    owner_set_u16(OWNER_BALANCE, (u16)(balance + actual));
    owner_set_daily((u8)activity, (u16)(daily + actual));
    lifetime = owner_u32(OWNER_LIFETIME);
    owner_set_u32(OWNER_LIFETIME,
                  lifetime + actual < lifetime ? 0xFFFFFFFFu
                                               : lifetime + actual);
    if (simple)
        G_OWNER[OWNER_SIMPLE_CLAIMS] |= simple_bit;
    if (activity == RESEARCH_ACTIVITY_GAME_CORNER)
        owner_set_u32(OWNER_LAST_GAME_TOKEN, source_token);
    (void)recompute_rank();
    clear_pending();
    if (!persist_phase(2u)) {
        restore_owner_snapshot();
        G_VOLATILE->recovery_blocked = 1u;
        return set_result(RESEARCH_RESULT_PERSIST_FAILED);
    }
    return set_result(RESEARCH_RESULT_SUCCESS);
}

static u8 bag_has_capacity(u16 item, u16 quantity)
{
    ensure_volatile_state();
    if (G_VOLATILE->test_bag_capacity != 0xFFFFu
        && quantity > G_VOLATILE->test_bag_capacity)
        return 0u;
    if (G_VOLATILE->reserved0)
        return 1u;
    return FN_CHECK_BAG_SPACE(item, quantity);
}

static u8 add_bag_item(u16 item, u16 quantity)
{
    if (G_VOLATILE->reserved0)
        return 1u;
    return FN_ADD_BAG_ITEM(item, quantity);
}

static void remove_bag_item(u16 item, u16 quantity)
{
    if (!G_VOLATILE->reserved0)
        (void)FN_REMOVE_BAG_ITEM(item, quantity);
}

static u16 shop_stock_result(const ResearchEconomyShopConfig *row)
{
    u32 once;
    if (row->once_bit != RESEARCH_NO_ONCE_BIT) {
        if (row->once_bit >= 32u)
            return RESEARCH_RESULT_INVALID;
        once = owner_u32(OWNER_SHOP_ONCE);
        if (once & (1u << row->once_bit))
            return RESEARCH_RESULT_DAILY_CAP;
    }
    if (row->stock_kind == RESEARCH_STOCK_DAILY_LIMITED) {
        if (row->daily_slot >= 4u || row->daily_limit == 0u)
            return RESEARCH_RESULT_INVALID;
        if (G_OWNER[OWNER_DAILY_SHOP + row->daily_slot]
            >= row->daily_limit)
            return RESEARCH_RESULT_DAILY_CAP;
    } else if (row->stock_kind != RESEARCH_STOCK_UNLIMITED) {
        return RESEARCH_RESULT_INVALID;
    }
    return RESEARCH_RESULT_SUCCESS;
}

RESEARCH_EXPORT(ResearchEconomy_PurchaseByIndex)
u16 ResearchEconomy_PurchaseByIndex(u16 catalog_index, u16 confirmed)
{
    const ResearchEconomyShopConfig *row;
    u16 stock_result;
    u16 pre_stock = 0u;
    u32 once;
    if (!confirmed)
        return set_result(RESEARCH_RESULT_CANCELLED);
    if (!ensure_save_idle())
        return set_result(RESEARCH_RESULT_CORRUPT_SAVE);
    if (catalog_index >= RESEARCH_ECONOMY_SHOP_COUNT)
        return set_result(RESEARCH_RESULT_INVALID);
    row = &gResearchEconomyShop[catalog_index];
    if (!kanto_access() || !unlock_satisfied(row->unlock_kind))
        return set_result(RESEARCH_RESULT_LOCKED);
    stock_result = shop_stock_result(row);
    if (stock_result != RESEARCH_RESULT_SUCCESS)
        return set_result(stock_result);
    if (owner_u16(OWNER_BALANCE) < row->price)
        return set_result(RESEARCH_RESULT_INSUFFICIENT);
    if (!bag_has_capacity(row->item_id, row->quantity))
        return set_result(RESEARCH_RESULT_BAG_FULL);
    if (row->stock_kind == RESEARCH_STOCK_DAILY_LIMITED)
        pre_stock = G_OWNER[OWNER_DAILY_SHOP + row->daily_slot];
    snapshot_owner();
    prepare_pending(PENDING_SPEND, (u8)catalog_index,
                    (u8)row->quantity, row->price, pre_stock, 0u);
    if (!persist_phase(1u)) {
        restore_owner_snapshot();
        return set_result(RESEARCH_RESULT_PERSIST_FAILED);
    }
    snapshot_owner();
    if (!add_bag_item(row->item_id, row->quantity)) {
        clear_pending();
        if (!persist_phase(0u)) {
            restore_owner_snapshot();
            G_VOLATILE->recovery_blocked = 1u;
        }
        return set_result(RESEARCH_RESULT_BAG_FULL);
    }
    owner_set_u16(OWNER_BALANCE,
                  (u16)(owner_u16(OWNER_BALANCE) - row->price));
    if (row->stock_kind == RESEARCH_STOCK_DAILY_LIMITED)
        G_OWNER[OWNER_DAILY_SHOP + row->daily_slot]
            = (u8)(pre_stock + row->quantity);
    if (row->once_bit != RESEARCH_NO_ONCE_BIT) {
        once = owner_u32(OWNER_SHOP_ONCE);
        owner_set_u32(OWNER_SHOP_ONCE, once | (1u << row->once_bit));
    }
    clear_pending();
    if (!persist_phase(2u)) {
        remove_bag_item(row->item_id, row->quantity);
        restore_owner_snapshot();
        G_VOLATILE->recovery_blocked = 1u;
        return set_result(RESEARCH_RESULT_PERSIST_FAILED);
    }
    return set_result(RESEARCH_RESULT_SUCCESS);
}

RESEARCH_EXPORT(ResearchEconomy_ClaimNextRankReward)
u16 ResearchEconomy_ClaimNextRankReward(u16 confirmed)
{
    const ResearchEconomyRankConfig *row = (const ResearchEconomyRankConfig *)0;
    u8 index;
    u8 rank;
    u8 claims;
    if (!confirmed)
        return set_result(RESEARCH_RESULT_CANCELLED);
    if (!ensure_save_idle())
        return set_result(RESEARCH_RESULT_CORRUPT_SAVE);
    (void)recompute_rank();
    rank = G_OWNER[OWNER_RANK];
    claims = G_OWNER[OWNER_RANK_CLAIMS];
    for (index = 0u; index < rank && index < RESEARCH_ECONOMY_RANK_COUNT;
         ++index) {
        if (!(claims & (1u << index))
            && unlock_satisfied(gResearchEconomyRanks[index].unlock_kind)) {
            row = &gResearchEconomyRanks[index];
            break;
        }
    }
    if (row == (const ResearchEconomyRankConfig *)0) {
        ResearchEconomy_SaveFinalize((void *)G_LEDGER);
        return set_result(RESEARCH_RESULT_EFFECTLESS);
    }
    if (!bag_has_capacity(row->reward_item_id, row->reward_quantity))
        return set_result(RESEARCH_RESULT_BAG_FULL);
    snapshot_owner();
    prepare_pending(PENDING_RANK, index, (u8)row->reward_quantity,
                    row->reward_item_id, claims, 0u);
    if (!persist_phase(1u)) {
        restore_owner_snapshot();
        return set_result(RESEARCH_RESULT_PERSIST_FAILED);
    }
    snapshot_owner();
    if (!add_bag_item(row->reward_item_id, row->reward_quantity)) {
        clear_pending();
        if (!persist_phase(0u)) {
            restore_owner_snapshot();
            G_VOLATILE->recovery_blocked = 1u;
        }
        return set_result(RESEARCH_RESULT_BAG_FULL);
    }
    G_OWNER[OWNER_RANK_CLAIMS] |= (u8)(1u << index);
    clear_pending();
    if (!persist_phase(2u)) {
        remove_bag_item(row->reward_item_id, row->reward_quantity);
        restore_owner_snapshot();
        G_VOLATILE->recovery_blocked = 1u;
        return set_result(RESEARCH_RESULT_PERSIST_FAILED);
    }
    return set_result(RESEARCH_RESULT_SUCCESS);
}

static void close_window(u8 task_id)
{
    u8 window_id = (u8)G_TASKS[task_id].data[0];
    if (window_id == WINDOW_INVALID)
        return;
    FN_CLEAR_STD_WINDOW_FRAME(window_id, 0u);
    FN_REMOVE_WINDOW(window_id);
    FN_SCHEDULE_BG_COPY(0u);
    G_TASKS[task_id].data[0] = WINDOW_INVALID;
    G_VOLATILE->window_id = WINDOW_INVALID;
}

static u8 page_row_count(void)
{
    u8 first = (u8)(G_VOLATILE->page * MENU_PAGE_SIZE);
    u8 remaining = first < G_VOLATILE->eligible_count
        ? (u8)(G_VOLATILE->eligible_count - first) : 0u;
    return remaining > MENU_PAGE_SIZE ? MENU_PAGE_SIZE : remaining;
}

static void append_balance_text(u16 balance)
{
    u8 *out = (u8 *)(uintptr_t)&G_VOLATILE->balance_text[0];
    u8 index = 0u;
    u16 divisor = 1000u;
    u8 started = 0u;
    while (gResearchEconomyBalancePrefix[index] != 0xFFu
           && index + 1u < sizeof(G_VOLATILE->balance_text)) {
        out[index] = gResearchEconomyBalancePrefix[index];
        ++index;
    }
    while (divisor != 0u
           && index + 1u < sizeof(G_VOLATILE->balance_text)) {
        u8 digit = (u8)(balance / divisor);
        if (digit != 0u || started || divisor == 1u) {
            out[index++] = gResearchEconomyDigitGlyphs[digit];
            started = 1u;
        }
        balance = (u16)(balance % divisor);
        divisor = (u16)(divisor / 10u);
    }
    out[index] = 0xFFu;
}

static u8 render_menu(u8 task_id)
{
    struct WindowTemplate template;
    u8 first = (u8)(G_VOLATILE->page * MENU_PAGE_SIZE);
    u8 rows = page_row_count();
    u8 has_next = (u8)(first + rows < G_VOLATILE->eligible_count);
    u8 menu_count = (u8)(rows + 1u);
    u8 index;
    u8 window_id;
    template.bg = 0u;
    template.tilemap_left = 8u;
    template.tilemap_top = 0u;
    template.width = 21u;
    template.height = (u8)(menu_count * 2u + 4u);
    template.palette_num = 15u;
    template.base_block = FN_GET_STD_WINDOW_BASE_TILE();
    window_id = (u8)FN_ADD_WINDOW(&template);
    if (window_id == WINDOW_INVALID)
        return 0u;
    G_TASKS[task_id].data[0] = window_id;
    G_VOLATILE->window_id = window_id;
    FN_FILL_WINDOW_PIXEL_BUFFER(window_id, 0x11u);
    FN_DRAW_STD_WINDOW_FRAME(window_id, 0u);
    FN_PUT_WINDOW_TILEMAP(window_id);
    append_balance_text(owner_u16(OWNER_BALANCE));
    FN_ADD_TEXT_PRINTER(window_id, 2u,
                        (const u8 *)(uintptr_t)&G_VOLATILE->balance_text[0],
                        8u, 1u, 0u, (void *)0);
    for (index = 0u; index < rows; ++index) {
        u16 catalog = G_VOLATILE->eligible[first + index];
        const u8 *text = gResearchEconomyShop[catalog].row_text;
        FN_ADD_TEXT_PRINTER(window_id, 2u,
                            text != (const u8 *)0 ? text : sEmptyText,
                            8u, (u8)(17u + index * 16u), 0u, (void *)0);
    }
    FN_ADD_TEXT_PRINTER(window_id, 2u,
                        has_next ? gResearchEconomyTextNext
                                 : gResearchEconomyTextCancel,
                        8u, (u8)(17u + rows * 16u), 0u, (void *)0);
    FN_MENU_INIT_CURSOR(window_id, 2u, 0u, 17u, 16u, menu_count, 0u);
    FN_COPY_WINDOW_TO_VRAM(window_id, COPYWIN_BOTH);
    FN_SCHEDULE_BG_COPY(0u);
    return 1u;
}

static void finish_menu(u8 task_id, u16 catalog, u16 result)
{
    close_window(task_id);
    FN_DESTROY_TASK(task_id);
    FN_PLAY_SE(SE_SELECT);
    G_VOLATILE->menu_active = 0u;
    G_VOLATILE->selected_catalog = catalog;
    set_result(result);
    FN_ENABLE_BOTH_SCRIPT_CONTEXTS();
}

static void Task_HandleResearchShop(u8 task_id)
{
    s8 choice = FN_MENU_PROCESS_INPUT();
    u8 first;
    u8 rows;
    u8 has_next;
    if (choice == MENU_NOTHING)
        return;
    first = (u8)(G_VOLATILE->page * MENU_PAGE_SIZE);
    rows = page_row_count();
    has_next = (u8)(first + rows < G_VOLATILE->eligible_count);
    if (choice == MENU_B || choice < 0) {
        finish_menu(task_id, 0xFFFFu, RESEARCH_RESULT_CANCELLED);
        return;
    }
    if ((u8)choice == rows) {
        if (has_next) {
            close_window(task_id);
            ++G_VOLATILE->page;
            if (!render_menu(task_id))
                finish_menu(task_id, 0xFFFFu,
                            RESEARCH_RESULT_ENGINE_REJECTED);
        } else {
            finish_menu(task_id, 0xFFFFu, RESEARCH_RESULT_CANCELLED);
        }
        return;
    }
    if ((u8)choice >= rows) {
        finish_menu(task_id, 0xFFFFu, RESEARCH_RESULT_INVALID);
        return;
    }
    finish_menu(task_id, G_VOLATILE->eligible[first + (u8)choice],
                RESEARCH_RESULT_SELECTED);
}

RESEARCH_EXPORT(ResearchEconomy_OpenShop)
u16 ResearchEconomy_OpenShop(void)
{
    u16 index;
    u8 task_id;
    ensure_volatile_state();
    if (!ensure_save_idle())
        return set_result(RESEARCH_RESULT_CORRUPT_SAVE);
    if (!kanto_access())
        return set_result(RESEARCH_RESULT_LOCKED);
    G_VOLATILE->eligible_count = 0u;
    G_VOLATILE->page = 0u;
    G_VOLATILE->window_id = WINDOW_INVALID;
    G_VOLATILE->selected_catalog = 0xFFFFu;
    G_VOLATILE->menu_active = 0u;
    clear_bytes(G_VOLATILE->eligible, sizeof(G_VOLATILE->eligible));
    clear_bytes(G_VOLATILE->balance_text, sizeof(G_VOLATILE->balance_text));
    for (index = 0u; index < RESEARCH_ECONOMY_SHOP_COUNT; ++index) {
        if (unlock_satisfied(gResearchEconomyShop[index].unlock_kind))
            G_VOLATILE->eligible[G_VOLATILE->eligible_count++] = index;
    }
    if (G_VOLATILE->eligible_count == 0u)
        return set_result(RESEARCH_RESULT_LOCKED);
    task_id = FN_CREATE_TASK(Task_HandleResearchShop, 0x50u);
    if (task_id >= NUM_TASKS)
        return set_result(RESEARCH_RESULT_ENGINE_REJECTED);
    G_TASKS[task_id].data[0] = WINDOW_INVALID;
    if (!render_menu(task_id)) {
        FN_DESTROY_TASK(task_id);
        return set_result(RESEARCH_RESULT_ENGINE_REJECTED);
    }
    G_VOLATILE->menu_active = 1u;
    set_result(RESEARCH_RESULT_BUSY);
    FN_SCRIPT_CONTEXT2_ENABLE();
    return RESEARCH_RESULT_BUSY;
}

RESEARCH_EXPORT(ResearchEconomy_PostShopMenu)
void ResearchEconomy_PostShopMenu(void)
{
    u16 result;
    ensure_volatile_state();
    result = G_VOLATILE->last_result;
    if (result == RESULT_NOT_SET)
        result = RESEARCH_RESULT_CANCELLED;
    *G_SPECIAL_RESULT = result;
}

RESEARCH_EXPORT(ResearchEconomy_PurchaseSelected)
u16 ResearchEconomy_PurchaseSelected(void)
{
    ensure_volatile_state();
    if (G_VOLATILE->selected_catalog == 0xFFFFu)
        return set_result(RESEARCH_RESULT_INVALID);
    return ResearchEconomy_PurchaseByIndex(G_VOLATILE->selected_catalog, 1u);
}

RESEARCH_EXPORT(ResearchEconomy_FieldCounter)
u16 ResearchEconomy_FieldCounter(void)
{
    u8 old_rank;
    u8 all_capped = 1u;
    u8 index;
    if (!ensure_save_idle())
        return set_result(RESEARCH_RESULT_PERSIST_FAILED);
    old_rank = G_OWNER[OWNER_RANK];
    if (recompute_rank() && !persist_phase(0u)) {
        G_OWNER[OWNER_RANK] = old_rank;
        ResearchEconomy_SaveFinalize((void *)G_LEDGER);
        return set_result(RESEARCH_RESULT_PERSIST_FAILED);
    }
    ResearchEconomy_SaveFinalize((void *)G_LEDGER);
    for (index = 0u; index < RESEARCH_ACTIVITY_COUNT; ++index) {
        if (owner_daily(index)
            < gResearchEconomyActivities[index].daily_cap)
            all_capped = 0u;
    }
    return set_result(all_capped ? RESEARCH_RESULT_DAILY_CAP
                                 : RESEARCH_RESULT_SUCCESS);
}

RESEARCH_EXPORT(ResearchEconomy_FieldRank)
u16 ResearchEconomy_FieldRank(void)
{
    return ResearchEconomy_ClaimNextRankReward(1u);
}

static u8 party_has_bug_type(void)
{
    u32 stats_root = read_u32(PTR(const volatile u8 *, 0x080001BCu));
    u8 count = *G_PARTY_COUNT;
    u8 index;
    if (count > PARTY_CAPACITY)
        count = PARTY_CAPACITY;
    if (stats_root < 0x08000000u || stats_root >= 0x0A000000u)
        return 0u;
    for (index = 0u; index < count; ++index) {
        const u8 *mon = G_PLAYER_PARTY + (u32)index * PARTY_MON_SIZE;
        u16 species = (u16)FN_GET_MON_DATA(mon, MON_DATA_SPECIES2,
                                            (u8 *)0);
        const volatile u8 *stats;
        if (species == 0u)
            continue;
        stats = PTR(const volatile u8 *,
                    stats_root + (u32)species * BASE_STATS_SIZE);
        if (stats[BASE_STATS_TYPE1_OFFSET] == TYPE_BUG
            || stats[BASE_STATS_TYPE2_OFFSET] == TYPE_BUG)
            return 1u;
    }
    return 0u;
}

RESEARCH_EXPORT(ResearchEconomy_FieldBug)
u16 ResearchEconomy_FieldBug(void)
{
    if (!party_has_bug_type())
        return set_result(RESEARCH_RESULT_LOCKED);
    return ResearchEconomy_CreditActivity(RESEARCH_ACTIVITY_BUG, 0u, 1u);
}

RESEARCH_EXPORT(ResearchEconomy_FieldMining)
u16 ResearchEconomy_FieldMining(void)
{
    /* The physical script calls this only after standard Rock Smash success. */
    return ResearchEconomy_CreditActivity(RESEARCH_ACTIVITY_MINING, 0u, 1u);
}

RESEARCH_EXPORT(ResearchEconomy_FieldPhoto)
u16 ResearchEconomy_FieldPhoto(void)
{
    return ResearchEconomy_CreditActivity(RESEARCH_ACTIVITY_PHOTO, 0u, 1u);
}

RESEARCH_EXPORT(ResearchEconomy_PlayTimeAdapter)
void ResearchEconomy_PlayTimeAdapter(void)
{
    u32 save_block = read_u32(G_SAVE_BLOCK2_POINTER);
    u8 old_seconds = 0u;
    if (save_block >= 0x02000000u && save_block < 0x02040000u) {
        const volatile u8 *play = PTR(const volatile u8 *, save_block);
        old_seconds = play[0x11u];
    }
    FN_PLAY_TIME();
    if (save_block >= 0x02000000u && save_block < 0x02040000u) {
        const volatile u8 *play = PTR(const volatile u8 *, save_block);
        /* Use the seconds rollover rather than displayed hours/minutes: the
         * vanilla play-time display can saturate while active research days
         * must continue advancing deterministically. */
        if (old_seconds == 59u && play[0x11u] == 0u)
            (void)ResearchEconomy_MinuteTick();
    }
}

static u8 dex_caught(u16 species)
{
    u16 national;
    if (species == 0u)
        return 0u;
    national = FN_SPECIES_TO_NATIONAL(species);
    if (national == 0u)
        return 0u;
    return FN_GET_SET_POKEDEX(national, POKEDEX_FLAG_GET_CAUGHT);
}

static void clear_wild_provenance(void)
{
    ensure_volatile_state();
    G_VOLATILE->wild_armed = 0u;
    G_VOLATILE->wild_activity = 0xFFu;
    G_VOLATILE->wild_species = 0u;
    G_VOLATILE->wild_pid = 0u;
    G_VOLATILE->wild_pre_caught = 0u;
}

static void arm_wild_provenance(u8 activity)
{
    u16 species = (u16)FN_GET_MON_DATA(G_ENEMY_PARTY, MON_DATA_SPECIES2,
                                        (u8 *)0);
    u32 pid = FN_GET_MON_DATA(G_ENEMY_PARTY, MON_DATA_PERSONALITY,
                              (u8 *)0);
    if (species == 0u)
        return;
    G_VOLATILE->wild_species = species;
    G_VOLATILE->wild_pid = pid;
    G_VOLATILE->wild_pre_caught = dex_caught(species);
    G_VOLATILE->wild_activity = activity;
    G_VOLATILE->wild_armed = 1u;
}

RESEARCH_EXPORT(ResearchEconomy_TryGenerateWildMonAdapter)
u8 ResearchEconomy_TryGenerateWildMonAdapter(const void *info, u8 area,
                                              u8 flags)
{
    clear_wild_provenance();
    /* Land/water is deliberately not research-credit provenance.  The chain
     * remains rooted so the current MoveDistribution/QOL behavior is kept. */
    return FN_MOVE_LAND(info, area, flags);
}

RESEARCH_EXPORT(ResearchEconomy_GenerateFishingEncounterAdapter)
u16 ResearchEconomy_GenerateFishingEncounterAdapter(const void *info, u8 rod)
{
    u16 species;
    clear_wild_provenance();
    species = FN_MOVE_FISHING(info, rod);
    if (species != 0u)
        arm_wild_provenance(RESEARCH_ACTIVITY_FISHING);
    return species;
}

RESEARCH_EXPORT(ResearchEconomy_TryHiddenEncounterAdapter)
u8 ResearchEconomy_TryHiddenEncounterAdapter(void)
{
    u8 result;
    clear_wild_provenance();
    result = FN_MOVE_HIDDEN();
    if (result)
        arm_wild_provenance(RESEARCH_ACTIVITY_ECOLOGY);
    return result;
}

__attribute__((section(".text.ResearchEconomy_EndWildBattleCommitInternal"),
               used, noinline, externally_visible))
void ResearchEconomy_EndWildBattleCommitInternal(void)
{
    u16 species;
    u32 pid;
    u32 token;
    ensure_volatile_state();
    if (!G_VOLATILE->wild_armed)
        return;
    species = (u16)FN_GET_MON_DATA(G_ENEMY_PARTY, MON_DATA_SPECIES2,
                                    (u8 *)0);
    pid = FN_GET_MON_DATA(G_ENEMY_PARTY, MON_DATA_PERSONALITY, (u8 *)0);
    if (*G_BATTLE_OUTCOME == BATTLE_OUTCOME_CAUGHT
        && species == G_VOLATILE->wild_species
        && pid == G_VOLATILE->wild_pid
        && !G_VOLATILE->wild_pre_caught
        && dex_caught(species)) {
        token = pid ^ ((u32)species << 16);
        if (token == 0u)
            token = 1u;
        (void)ResearchEconomy_CreditActivity(G_VOLATILE->wild_activity,
                                              token, 0u);
    }
    clear_wild_provenance();
}

RESEARCH_EXPORT(ResearchEconomy_EndWildBattleAdapter)
__attribute__((naked))
void ResearchEconomy_EndWildBattleAdapter(void)
{
    /* The QOL target is an assembly continuation, not a returning C function.
     * Preserve the original hook LR/SP and callee-saved r4 across our C commit,
     * then tail-chain with exactly the entry context that QOL expects. */
    __asm__ volatile(
        "push {r4, lr}\n"
        "bl ResearchEconomy_EndWildBattleCommitInternal\n"
        "pop {r4}\n"
        "pop {r3}\n"
        "mov lr, r3\n"
        "ldr r3, =%c0\n"
        "bx r3\n"
        :
        : "i" (RESEARCH_ECONOMY_DELEGATE_QOL_WILD_END)
        : "r3", "memory");
}

static volatile u8 *game_corner_state(void)
{
    u32 address = read_u32(G_GAME_CORNER_STATE_POINTER);
    if (address < 0x02000000u || address + 0x52u > 0x02040000u)
        return (volatile u8 *)0;
    return PTR(volatile u8 *, address);
}

RESEARCH_EXPORT(ResearchEconomy_GameCornerPayoutAdapter)
void ResearchEconomy_GameCornerPayoutAdapter(u16 amount)
{
    volatile u8 *state;
    u16 remaining;
    u16 coins_before;
    u16 coins_after;
    u32 already_paid;
    u32 expected_coins;
    u32 token;
    ensure_volatile_state();
    if (G_VOLATILE->reserved0) {
        if (amount >= 100u) {
            token = owner_u32(OWNER_NEXT_TRANSACTION)
                ^ ((u32)amount << 16) ^ 0x4743u;
            if (token == 0u)
                token = 1u;
            (void)ResearchEconomy_CreditActivity(
                RESEARCH_ACTIVITY_GAME_CORNER, token, 0u);
        }
        return;
    }
    state = game_corner_state();
    if (state == (volatile u8 *)0) {
        FN_ADD_COINS(amount);
        return;
    }
    remaining = read_u16(state + 0x50u);
    coins_before = FN_GET_COINS();
    already_paid = G_VOLATILE->game_initial_payout >= remaining
        ? (u32)(G_VOLATILE->game_initial_payout - remaining) : 0u;
    expected_coins = (u32)G_VOLATILE->game_pre_coins + already_paid;
    if (expected_coins > 9999u)
        expected_coins = 9999u;
    if (!G_VOLATILE->game_active
        || remaining > G_VOLATILE->game_last_remaining
        || coins_before != (u16)expected_coins) {
        G_VOLATILE->game_active = 1u;
        G_VOLATILE->game_initial_payout = remaining;
        G_VOLATILE->game_pre_coins = coins_before;
    }
    G_VOLATILE->game_last_remaining = remaining;
    FN_ADD_COINS(amount);
    coins_after = FN_GET_COINS();
    if (remaining <= amount) {
        u16 initial = G_VOLATILE->game_initial_payout;
        u16 pre_coins = G_VOLATILE->game_pre_coins;
        G_VOLATILE->game_active = 0u;
        G_VOLATILE->game_initial_payout = 0u;
        G_VOLATILE->game_pre_coins = 0u;
        G_VOLATILE->game_last_remaining = 0u;
        if (initial >= 100u && coins_after >= pre_coins
            && (u16)(coins_after - pre_coins) >= 100u) {
            token = owner_u32(OWNER_NEXT_TRANSACTION)
                ^ ((u32)initial << 16) ^ pre_coins;
            if (token == 0u)
                token = 1u;
            (void)ResearchEconomy_CreditActivity(
                RESEARCH_ACTIVITY_GAME_CORNER, token, 0u);
        }
    }
}

RESEARCH_EXPORT(ResearchEconomy_TestInitialize)
u16 ResearchEconomy_TestInitialize(void)
{
    reset_volatile_state();
    /* Exact-ROM probes run before a normal game boot has initialized engine
     * save/bag/minigame globals.  Test mode models those external services;
     * production entrypoints never enable it. */
    G_VOLATILE->reserved0 = 1u;
    ResearchEconomy_SaveInitNew((void *)G_LEDGER, 0u);
    return set_result(RESEARCH_RESULT_SUCCESS);
}

RESEARCH_EXPORT(ResearchEconomy_TestSetUnlockAll)
u16 ResearchEconomy_TestSetUnlockAll(u16 enabled)
{
    ensure_volatile_state();
    if (enabled > 1u)
        return set_result(RESEARCH_RESULT_INVALID);
    G_VOLATILE->test_unlock_all = (u8)enabled;
    return set_result(RESEARCH_RESULT_SUCCESS);
}

RESEARCH_EXPORT(ResearchEconomy_TestSetPersistenceFault)
u16 ResearchEconomy_TestSetPersistenceFault(u16 phase)
{
    ensure_volatile_state();
    if (phase > 2u)
        return set_result(RESEARCH_RESULT_INVALID);
    G_VOLATILE->test_persistence_fault = (u8)phase;
    return set_result(RESEARCH_RESULT_SUCCESS);
}

RESEARCH_EXPORT(ResearchEconomy_TestSetBagCapacity)
u16 ResearchEconomy_TestSetBagCapacity(u16 available)
{
    ensure_volatile_state();
    G_VOLATILE->test_bag_capacity = available;
    return set_result(RESEARCH_RESULT_SUCCESS);
}

RESEARCH_EXPORT(ResearchEconomy_TestGetOwnerByte)
u16 ResearchEconomy_TestGetOwnerByte(u16 offset)
{
    if (offset >= RESEARCH_ECONOMY_OWNER_SIZE)
        return set_result(RESEARCH_RESULT_INVALID);
    *G_SPECIAL_RESULT = G_OWNER[offset];
    return G_OWNER[offset];
}

RESEARCH_EXPORT(ResearchEconomy_TestSetBalance)
u16 ResearchEconomy_TestSetBalance(u16 balance)
{
    if (balance > RESEARCH_ECONOMY_POINT_CAP)
        return set_result(RESEARCH_RESULT_INVALID);
    if (!ensure_save_idle())
        return set_result(RESEARCH_RESULT_CORRUPT_SAVE);
    owner_set_u16(OWNER_BALANCE, balance);
    ResearchEconomy_SaveFinalize((void *)G_LEDGER);
    return set_result(RESEARCH_RESULT_SUCCESS);
}
