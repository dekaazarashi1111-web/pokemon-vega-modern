/*
 * USER-20260827-COLLECTION-SUPPLY-V1-IMPLEMENTATION
 *
 * Collection Supply V1の全canonical表を、標準field menu、通常party選択、
 * CFRU Raid、bag／money／BP／research economy、独立sector 31 ownerへ接続する。
 */

#include "collection_supply_v1.h"

#include <stddef.h>
#include <stdint.h>

#include "../save_migration/save_migration.h"

typedef uint8_t u8;
typedef int8_t s8;
typedef uint16_t u16;
typedef int16_t s16;
typedef uint32_t u32;

#define PTR(type, address) ((type)(uintptr_t)(address))
#define COLLECTION_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))

enum {
    COLLECTION_OWNER_MAGIC = 0x31565343u,
    COLLECTION_STATE_MAGIC = 0x31545343u,
    COLLECTION_PAGE_SIZE = 5u,
    COLLECTION_MENU_NOTHING = -2,
    COLLECTION_MENU_B = -1,
    COLLECTION_WINDOW_INVALID = 0xFFu,
    COLLECTION_NUM_TASKS = 16u,
    COLLECTION_COPYWIN_BOTH = 3u,
    COLLECTION_SE_SELECT = 5u,
    COLLECTION_SECTOR = 31u,
    COLLECTION_SECTOR_DATA_SIZE = 0x0FF0u,
    COLLECTION_SECTOR_SIZE = 0x1000u,
    COLLECTION_PARTY_SIZE = 6u,
    COLLECTION_MON_SIZE = 100u,
    COLLECTION_BOX_COUNT = 14u,
    COLLECTION_BOX_CAPACITY = 30u,
    COLLECTION_MON_DATA_PERSONALITY = 0u,
    COLLECTION_MON_DATA_SPECIES = 11u,
    COLLECTION_MON_DATA_IS_EGG = 45u,
    COLLECTION_MON_DATA_SPECIES2 = 65u,
    COLLECTION_GMAX_BYTE_OFFSET = 0x47u,
    COLLECTION_GMAX_MASK = 0x08u,
    COLLECTION_BATTLE_OUTCOME_CAUGHT = 7u,
    COLLECTION_FLAG_BADGE_1 = 0x0820u,
    COLLECTION_FLAG_HALL_OF_FAME = 0x082Cu,
    COLLECTION_FLAG_SHIOU_CLEAR = 0x0824u,
    COLLECTION_FLAG_DH_CLEAR = 0x114Bu,
    COLLECTION_FIELD_MAIN_CALLBACK = 0x08055E75u,
    COLLECTION_MENU_ROOT = 0u,
    COLLECTION_MENU_ITEMS = 1u,
    COLLECTION_MENU_FORMS = 2u,
    COLLECTION_MENU_GIFTS = 3u,
    COLLECTION_MENU_RELICS = 4u,
    COLLECTION_PENDING_NONE = 0u,
    COLLECTION_PENDING_PREPARED = 1u,
    COLLECTION_PENDING_STAGED = 2u,
    COLLECTION_PENDING_ITEM = 1u,
    COLLECTION_PENDING_GIFT = 2u,
    COLLECTION_CLAIM_NONE = 0u,
    COLLECTION_CLAIM_ITEM = 1u,
    COLLECTION_CLAIM_FORM_GIFT = 2u,
    COLLECTION_SOURCE_MONEY = 0u,
    COLLECTION_SOURCE_BP = 1u,
    COLLECTION_SOURCE_RESEARCH = 2u,
    COLLECTION_SOURCE_FACTORY = 3u,
    COLLECTION_SOURCE_RAID = 4u,
    COLLECTION_SOURCE_GIFT = 5u,
    COLLECTION_SOURCE_FORM = 6u,
    COLLECTION_SOURCE_STORY = 7u,
    COLLECTION_SOURCE_EXISTING = 8u,
    COLLECTION_SOURCE_EXCLUDED = 9u,
    COLLECTION_SERVICE_MONEY = 0u,
    COLLECTION_SERVICE_BP = 1u,
    COLLECTION_SERVICE_RESEARCH = 2u,
    COLLECTION_SERVICE_FORM = 3u,
    COLLECTION_SERVICE_RELIC = 4u,
    COLLECTION_SERVICE_GIFT = 5u,
    COLLECTION_SERVICE_GMAX = 6u,
    COLLECTION_GIFT_FIXED = 0u,
    COLLECTION_GIFT_RESEARCH_EGG = 1u,
    COLLECTION_CAPTURE_REPEATABLE = 0u,
    COLLECTION_CAPTURE_SHARED = 1u,
    COLLECTION_CAPTURE_FORM = 2u,
    COLLECTION_CURRENCY_NONE = 0u,
    COLLECTION_CURRENCY_MONEY = 1u,
    COLLECTION_CURRENCY_BP = 2u,
    COLLECTION_CURRENCY_RESEARCH = 3u,
    COLLECTION_SAVE1_MONEY_OFFSET = 0x290u,
    COLLECTION_SAVE2_KEY_OFFSET = 0x0F20u,
    COLLECTION_RESEARCH_OWNER_OFFSET = 0x73Fu,
    COLLECTION_RESEARCH_BALANCE_OFFSET = 4u,
    COLLECTION_RESEARCH_SCHEMA_OFFSET = 0u,
    COLLECTION_RESEARCH_RANK_OFFSET = 6u,
    COLLECTION_OWNER_FLASH_OFFSET = 0x0964u
};

typedef struct CollectionItemRow {
    u16 item_id;
    u16 price;
    u8 quantity;
    u8 source;
    u8 unlock;
    u8 repeatability;
    const u8 *name;
} CollectionItemRow;

typedef struct CollectionFormRow {
    u16 target_species;
    u16 base_species;
    u8 method;
    u8 unlock;
    u8 distributable;
    u8 reserved;
    const u8 *name;
} CollectionFormRow;

typedef struct CollectionGmaxRow {
    u16 base_species;
    u16 form_species;
} CollectionGmaxRow;

typedef struct CollectionGiftRow {
    u16 form_index;
    u8 kind;
    u8 claim_bit;
    u8 unlock;
    u8 reserved;
    const u8 *name;
} CollectionGiftRow;

typedef struct CollectionPoolRow {
    u16 species;
    u16 weight;
    u8 pool;
    u8 tier;
    u8 level_min;
    u8 level_max;
    u8 gmax_chance;
    u8 capture_kind;
    u8 capture_index;
    u8 reward_once;
    u8 unlock;
    u8 reserved;
} CollectionPoolRow;

typedef struct CollectionRewardRow {
    u16 item_id;
    u16 weight;
    u8 pool;
    u8 quantity_min;
    u8 quantity_max;
    u8 first_clear;
    u8 unlock;
    u8 reserved;
} CollectionRewardRow;

typedef struct CollectionHostRow {
    u8 pool;
    u8 reward_pool;
    u8 unlock;
    u8 service;
    u8 high_raid;
    u8 reserved[3];
} CollectionHostRow;

/* The builder emits all 388/34/999/14/292/217 canonical rows here. */
#include "collection_supply_v1_generated.h"

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

typedef void (*VoidFn)(void);
typedef u8 (*U8ArgFn)(u8);
typedef u16 (*U16Fn)(void);
typedef u8 (*FlagGetFn)(u16);
typedef u8 (*BagFn)(u16, u16);
typedef u16 (*CountBagFn)(u16);
typedef u8 (*TryWriteSectorFn)(u16, const void *);
typedef void (*ReadFlashFn)(u16, u32, void *, u32);
typedef void (*CreateMonFn)(void *, u16, u8, u8, u8, u32, u8, u32);
typedef u8 (*GiveMonFn)(void *);
typedef u32 (*GetMonDataFn)(const void *, int, u8 *);
typedef void (*SetMonDataFn)(void *, int, const void *);
typedef void (*CalculateStatsFn)(void *);
typedef u8 (*CalculatePartyCountFn)(void);
typedef u16 (*RandomFn)(void);
typedef u8 (*ConfigureRaidFn)(u8, u8, u8, u8, u8);
typedef u32 (*GetBoxMonDataAtFn)(u8, u8, u32);
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

#define G_STATE gCollectionSupplyVolatileState
#define G_OWNER gCollectionSupplyOwner
#define G_SPECIAL_RESULT PTR(volatile u16 *, 0x02037004u)
#define G_VAR_8004 PTR(volatile u16 *, 0x02036FF4u)
#define G_TASKS PTR(struct Task *, 0x030050D0u)
#define G_PLAYER_PARTY PTR(u8 *, 0x020241E4u)
#define G_ENEMY_PARTY PTR(u8 *, 0x02023F8Cu)
#define G_PARTY_COUNT PTR(volatile u8 *, 0x02023F89u)
#define G_BATTLE_OUTCOME PTR(volatile u8 *, 0x02023DEAu)
#define G_SAVE_BLOCK1_PTR PTR(volatile u8 * volatile *, 0x03005048u)
#define G_SAVE_BLOCK2_PTR PTR(volatile u8 * volatile *, 0x0300504Cu)
#define G_MAIN_CALLBACK2 PTR(volatile u32 *, 0x03003134u)
#define G_SAVE_BUFFER PTR(volatile u8 *, 0x020399B0u)
#define G_SECTOR31_IMAGE PTR(const volatile u8 *, 0x0203CF9Cu)

#define FN_FLAG_GET PTR(FlagGetFn, COLLECTION_ENGINE_FLAG_GET)
#define FN_ADD_BAG PTR(BagFn, COLLECTION_ENGINE_ADD_BAG_ITEM)
#define FN_REMOVE_BAG PTR(BagFn, COLLECTION_ENGINE_REMOVE_BAG_ITEM)
#define FN_COUNT_BAG PTR(CountBagFn, COLLECTION_ENGINE_COUNT_BAG_ITEM)
#define FN_TRY_WRITE_SECTOR \
    PTR(TryWriteSectorFn, COLLECTION_ENGINE_TRY_WRITE_SECTOR)
#define FN_READ_FLASH PTR(ReadFlashFn, COLLECTION_ENGINE_READ_FLASH)
#define FN_CREATE_MON PTR(CreateMonFn, COLLECTION_ENGINE_CREATE_MON)
#define FN_GIVE_MON PTR(GiveMonFn, COLLECTION_ENGINE_GIVE_MON)
#define FN_GET_MON_DATA PTR(GetMonDataFn, COLLECTION_ENGINE_GET_MON_DATA)
#define FN_SET_MON_DATA PTR(SetMonDataFn, COLLECTION_ENGINE_SET_MON_DATA)
#define FN_CALCULATE_STATS \
    PTR(CalculateStatsFn, COLLECTION_ENGINE_CALCULATE_STATS)
#define FN_PARTY_COUNT \
    PTR(CalculatePartyCountFn, COLLECTION_ENGINE_CALCULATE_PARTY_COUNT)
#define FN_RANDOM PTR(RandomFn, COLLECTION_ENGINE_RANDOM)
#define FN_CONFIGURE_RAID PTR(ConfigureRaidFn, COLLECTION_ENGINE_CONFIGURE_RAID)
#define FN_START_WILD PTR(VoidFn, COLLECTION_ENGINE_START_SCRIPTED_WILD_BATTLE)
#define FN_GET_BOX_MON_DATA_AT \
    PTR(GetBoxMonDataAtFn, COLLECTION_ENGINE_GET_BOX_MON_DATA_AT)
#define FN_SCRIPT_CONTEXT2_ENABLED \
    PTR(U16Fn, COLLECTION_ENGINE_SCRIPT_CONTEXT2_ENABLED)
#define FN_SCRIPT_CONTEXT2_ENABLE \
    PTR(VoidFn, COLLECTION_ENGINE_SCRIPT_CONTEXT2_ENABLE)
#define FN_ENABLE_BOTH_CONTEXTS \
    PTR(VoidFn, COLLECTION_ENGINE_ENABLE_BOTH_SCRIPT_CONTEXTS)
#define FN_CREATE_TASK PTR(CreateTaskFn, COLLECTION_ENGINE_CREATE_TASK)
#define FN_DESTROY_TASK PTR(TaskIdFn, COLLECTION_ENGINE_DESTROY_TASK)
#define FN_ADD_WINDOW PTR(AddWindowFn, COLLECTION_ENGINE_ADD_WINDOW)
#define FN_REMOVE_WINDOW PTR(WindowU8Fn, COLLECTION_ENGINE_REMOVE_WINDOW)
#define FN_COPY_WINDOW PTR(WindowPairFn, COLLECTION_ENGINE_COPY_WINDOW_TO_VRAM)
#define FN_PUT_WINDOW_TILEMAP \
    PTR(WindowU8Fn, COLLECTION_ENGINE_PUT_WINDOW_TILEMAP)
#define FN_FILL_WINDOW \
    PTR(WindowPairFn, COLLECTION_ENGINE_FILL_WINDOW_PIXEL_BUFFER)
#define FN_ADD_TEXT PTR(TextPrinterFn, COLLECTION_ENGINE_ADD_TEXT_PRINTER)
#define FN_SCHEDULE_BG PTR(WindowU8Fn, COLLECTION_ENGINE_SCHEDULE_BG_COPY)
#define FN_DRAW_FRAME PTR(WindowPairFn, COLLECTION_ENGINE_DRAW_STD_WINDOW_FRAME)
#define FN_CLEAR_FRAME \
    PTR(WindowPairFn, COLLECTION_ENGINE_CLEAR_STD_WINDOW_FRAME)
#define FN_BASE_TILE \
    PTR(GetBaseTileFn, COLLECTION_ENGINE_GET_STD_WINDOW_BASE_TILE)
#define FN_MENU_INIT PTR(MenuInitCursorFn, COLLECTION_ENGINE_MENU_INIT_CURSOR)
#define FN_MENU_INPUT PTR(MenuInputFn, COLLECTION_ENGINE_MENU_PROCESS_INPUT)
#define FN_PLAY_SE PTR(PlaySeFn, COLLECTION_ENGINE_PLAY_SE)
#define FN_BASE_READ_KEYS PTR(VoidFn, COLLECTION_DELEGATE_READ_KEYS)
#define FN_BASE_SAVE_LOAD PTR(U8ArgFn, COLLECTION_DELEGATE_SAVE_LOAD)
#define FN_BASE_LAND_WATER \
    PTR(u8 (*)(const void *, u8, u8), COLLECTION_DELEGATE_LAND_WATER)
#define FN_BASE_WILD_END PTR(VoidFn, COLLECTION_DELEGATE_WILD_END)
#define FN_TRY_SAVING_DATA PTR(U8ArgFn, COLLECTION_TRY_SAVING_DATA)
#define FN_RESEARCH_FINALIZE \
    PTR(void (*)(void *), COLLECTION_RESEARCH_SAVE_FINALIZE)

_Static_assert(sizeof(struct Task) == 40u, "FireRed Task ABI differs");
_Static_assert(sizeof(struct WindowTemplate) == 8u,
               "FireRed Window ABI differs");

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

static u16 read16(const volatile u8 *bytes)
{
    return (u16)((u16)bytes[0] | ((u16)bytes[1] << 8));
}

static u32 read32(const volatile u8 *bytes)
{
    return (u32)bytes[0] | ((u32)bytes[1] << 8)
        | ((u32)bytes[2] << 16) | ((u32)bytes[3] << 24);
}

static void write16(volatile u8 *bytes, u16 value)
{
    bytes[0] = (u8)value;
    bytes[1] = (u8)(value >> 8);
}

static void write32(volatile u8 *bytes, u32 value)
{
    bytes[0] = (u8)value;
    bytes[1] = (u8)(value >> 8);
    bytes[2] = (u8)(value >> 16);
    bytes[3] = (u8)(value >> 24);
}

static u32 crc_byte(u32 crc, u8 value)
{
    u32 bit;
    crc ^= value;
    for (bit = 0u; bit < 8u; ++bit) {
        u32 mask = 0u - (crc & 1u);
        crc = (crc >> 1) ^ (0xEDB88320u & mask);
    }
    return crc;
}

static u32 owner_crc_at(const volatile CollectionSupplyOwnerV1 *owner)
{
    const volatile u8 *bytes = (const volatile u8 *)owner;
    u32 crc = 0xFFFFFFFFu;
    u32 index;
    for (index = 0u; index < COLLECTION_SUPPLY_OWNER_SIZE; ++index) {
        u8 value = index >= 12u && index < 16u ? 0u : bytes[index];
        crc = crc_byte(crc, value);
    }
    return crc ^ 0xFFFFFFFFu;
}

static void owner_finalize(void)
{
    G_OWNER->magic = COLLECTION_OWNER_MAGIC;
    G_OWNER->magic_inverse = ~COLLECTION_OWNER_MAGIC;
    G_OWNER->version = 1u;
    G_OWNER->struct_size = COLLECTION_SUPPLY_OWNER_SIZE;
    G_OWNER->crc32 = 0u;
    G_OWNER->crc32 = owner_crc_at(G_OWNER);
}

static u8 owner_valid_at(const volatile CollectionSupplyOwnerV1 *owner)
{
    return (u8)(owner->magic == COLLECTION_OWNER_MAGIC
        && owner->magic_inverse == ~(u32)COLLECTION_OWNER_MAGIC
        && owner->version == 1u
        && owner->struct_size == COLLECTION_SUPPLY_OWNER_SIZE
        && owner->crc32 == owner_crc_at(owner)
        && owner->pending_phase <= COLLECTION_PENDING_STAGED
        && owner->pending_reward_host <= COLLECTION_HOST_COUNT);
}

static u8 owner_valid(void)
{
    return owner_valid_at(G_OWNER);
}

static void owner_initialize(void)
{
    clear_bytes(G_OWNER, COLLECTION_SUPPLY_OWNER_SIZE);
    G_OWNER->generation = 1u;
    G_OWNER->transaction_id = 1u;
    owner_finalize();
}

static void ensure_state(void)
{
    if (G_STATE->magic != COLLECTION_STATE_MAGIC
        || G_STATE->magic_inverse != ~(u32)COLLECTION_STATE_MAGIC) {
        clear_bytes(G_STATE, COLLECTION_SUPPLY_VOLATILE_SIZE);
        G_STATE->magic = COLLECTION_STATE_MAGIC;
        G_STATE->magic_inverse = ~COLLECTION_STATE_MAGIC;
        G_STATE->window_id = COLLECTION_WINDOW_INVALID;
        G_STATE->active_entry = 0xFFFFu;
        G_STATE->pending_index = 0xFFFFu;
    }
}

static void set_result(u16 result)
{
    ensure_state();
    G_STATE->last_result = result;
    *G_SPECIAL_RESULT = result;
}

static u8 test_fault(u8 bit)
{
    if (!G_STATE->test_mode || (G_STATE->test_fault & bit) == 0u)
        return 0u;
    G_STATE->test_fault &= (u8)~bit;
    return 1u;
}

static u8 persist_sector(void)
{
    owner_finalize();
    if (test_fault(2u))
        return 0u;
    if (G_STATE->test_mode)
        return 1u;
    clear_bytes(G_SAVE_BUFFER, COLLECTION_SECTOR_SIZE);
    copy_bytes(G_SAVE_BUFFER, G_SECTOR31_IMAGE,
               COLLECTION_SECTOR_DATA_SIZE);
    return (u8)(FN_TRY_WRITE_SECTOR(COLLECTION_SECTOR,
                                    (const void *)G_SAVE_BUFFER) == 1u);
}

static u8 persist_standard(void)
{
    if (test_fault(1u))
        return 0u;
    if (G_STATE->test_mode)
        return 1u;
    return (u8)(FN_TRY_SAVING_DATA(0u) == 1u);
}

static u8 ledger_valid(void)
{
    return (u8)(VegaSaveValidate(gVegaModernSaveData,
                                 VEGA_SAVE_LEDGER_SIZE) == VEGA_SAVE_OK);
}

static u8 unlock_satisfied(u8 unlock)
{
    volatile u8 *research = (volatile u8 *)gVegaModernSaveData
        + COLLECTION_RESEARCH_OWNER_OFFSET;
    if (G_STATE->test_mode)
        return 1u;
    switch (unlock) {
    case COLLECTION_UNLOCK_NONE:
    case COLLECTION_UNLOCK_VEGA_PRE_ENTRY:
        return 1u;
    case COLLECTION_UNLOCK_VEGA_BADGE_1:
        return FN_FLAG_GET(COLLECTION_FLAG_BADGE_1);
    case COLLECTION_UNLOCK_VEGA_BADGE_2:
        return FN_FLAG_GET((u16)(COLLECTION_FLAG_BADGE_1 + 1u));
    case COLLECTION_UNLOCK_VEGA_BADGE_5:
        return FN_FLAG_GET((u16)(COLLECTION_FLAG_BADGE_1 + 4u));
    case COLLECTION_UNLOCK_KANTO_EARLY_ACCESS:
        return (u8)(gVegaModernSaveData->kanto_travel_unlocked
                    || gVegaModernSaveData->vega_hall_of_fame
                    || (FN_FLAG_GET(COLLECTION_FLAG_SHIOU_CLEAR)
                        && FN_FLAG_GET(COLLECTION_FLAG_DH_CLEAR)));
    case COLLECTION_UNLOCK_RESEARCH_PROFILE:
        return (u8)(research[COLLECTION_RESEARCH_SCHEMA_OFFSET] == 1u
                    && research[COLLECTION_RESEARCH_RANK_OFFSET] >= 1u);
    case COLLECTION_UNLOCK_RAID_HIGH:
    case COLLECTION_UNLOCK_TM_LICENSE:
    case COLLECTION_UNLOCK_HIDDEN_ABILITY:
        return (u8)(gVegaModernSaveData->vega_hall_of_fame
                    || FN_FLAG_GET((u16)(COLLECTION_FLAG_BADGE_1 + 7u)));
    case COLLECTION_UNLOCK_LEAGUE_I:
    case COLLECTION_UNLOCK_FACTORY_STANDARD:
        return gVegaModernSaveData->league_i_cleared;
    case COLLECTION_UNLOCK_LEAGUE_II:
    case COLLECTION_UNLOCK_COMPETITIVE:
    case COLLECTION_UNLOCK_FACTORY_FULL:
        return gVegaModernSaveData->league_ii_cleared;
    case COLLECTION_UNLOCK_FINAL_LEAGUE:
    case COLLECTION_UNLOCK_KANTO_LEAGUE:
    case COLLECTION_UNLOCK_UB_PARADOX:
    case COLLECTION_UNLOCK_FACTORY_MASTER:
        return (u8)(gVegaModernSaveData->league_ii_cleared
                    && (gVegaModernSaveData->vega_hall_of_fame
                        || FN_FLAG_GET(COLLECTION_FLAG_HALL_OF_FAME)));
    default:
        return 0u;
    }
}

static u32 money_balance(void)
{
    volatile u8 *save1 = *G_SAVE_BLOCK1_PTR;
    volatile u8 *save2 = *G_SAVE_BLOCK2_PTR;
    if (G_STATE->test_mode)
        return G_STATE->test_money;
    if (save1 == (volatile u8 *)0 || save2 == (volatile u8 *)0)
        return 0u;
    return read32(save1 + COLLECTION_SAVE1_MONEY_OFFSET)
        ^ read32(save2 + COLLECTION_SAVE2_KEY_OFFSET);
}

static void set_money_balance(u32 value)
{
    volatile u8 *save1 = *G_SAVE_BLOCK1_PTR;
    volatile u8 *save2 = *G_SAVE_BLOCK2_PTR;
    if (G_STATE->test_mode) {
        G_STATE->test_money = value;
        return;
    }
    if (save1 != (volatile u8 *)0 && save2 != (volatile u8 *)0)
        write32(save1 + COLLECTION_SAVE1_MONEY_OFFSET,
                value ^ read32(save2 + COLLECTION_SAVE2_KEY_OFFSET));
}

static volatile u8 *research_owner(void)
{
    return (volatile u8 *)gVegaModernSaveData
        + COLLECTION_RESEARCH_OWNER_OFFSET;
}

static u16 research_balance(void)
{
    if (G_STATE->test_mode)
        return G_STATE->test_research;
    return read16(research_owner() + COLLECTION_RESEARCH_BALANCE_OFFSET);
}

static void set_research_balance(u16 value)
{
    if (G_STATE->test_mode) {
        G_STATE->test_research = value;
        return;
    }
    write16(research_owner() + COLLECTION_RESEARCH_BALANCE_OFFSET, value);
    FN_RESEARCH_FINALIZE((void *)gVegaModernSaveData);
}

static u32 currency_balance(u8 currency)
{
    if (currency == COLLECTION_CURRENCY_MONEY)
        return money_balance();
    if (currency == COLLECTION_CURRENCY_BP)
        return G_STATE->test_mode ? G_STATE->test_bp
                                  : gVegaModernSaveData->factory.battle_points;
    if (currency == COLLECTION_CURRENCY_RESEARCH)
        return research_balance();
    return 0u;
}

static void currency_set(u8 currency, u32 value)
{
    if (currency == COLLECTION_CURRENCY_MONEY)
        set_money_balance(value);
    else if (currency == COLLECTION_CURRENCY_BP && G_STATE->test_mode)
        G_STATE->test_bp = (u16)value;
    else if (currency == COLLECTION_CURRENCY_BP) {
        gVegaModernSaveData->factory.battle_points = (u16)value;
        VegaSaveFinalize(gVegaModernSaveData);
    } else if (currency == COLLECTION_CURRENCY_RESEARCH)
        set_research_balance((u16)value);
}

static u8 source_currency(u8 source)
{
    if (source == COLLECTION_SOURCE_MONEY)
        return COLLECTION_CURRENCY_MONEY;
    if (source == COLLECTION_SOURCE_BP)
        return COLLECTION_CURRENCY_BP;
    if (source == COLLECTION_SOURCE_RESEARCH)
        return COLLECTION_CURRENCY_RESEARCH;
    return COLLECTION_CURRENCY_NONE;
}

static u16 bag_count(u16 item)
{
    if (!G_STATE->test_mode)
        return FN_COUNT_BAG(item);
    return G_STATE->test_bag_item == item ? G_STATE->test_bag_quantity : 0u;
}

static u8 bag_add(u16 item, u16 quantity)
{
    if (!G_STATE->test_mode)
        return FN_ADD_BAG(item, quantity);
    if (G_STATE->test_bag_item != item && G_STATE->test_bag_quantity != 0u)
        return 0u;
    if ((u32)G_STATE->test_bag_quantity + quantity
            > G_STATE->test_bag_capacity)
        return 0u;
    G_STATE->test_bag_item = item;
    G_STATE->test_bag_quantity = (u16)(G_STATE->test_bag_quantity + quantity);
    return 1u;
}

static u8 bag_remove(u16 item, u16 quantity)
{
    if (!G_STATE->test_mode)
        return FN_REMOVE_BAG(item, quantity);
    if (G_STATE->test_bag_item != item
        || G_STATE->test_bag_quantity < quantity)
        return 0u;
    G_STATE->test_bag_quantity = (u16)(G_STATE->test_bag_quantity - quantity);
    if (G_STATE->test_bag_quantity == 0u)
        G_STATE->test_bag_item = 0u;
    return 1u;
}

static u16 random16(void)
{
    if (!G_STATE->test_mode)
        return FN_RANDOM();
    G_STATE->test_rng = G_STATE->test_rng * 1103515245u + 24691u;
    return (u16)(G_STATE->test_rng >> 16);
}

static u8 item_claimed(u16 item)
{
    if (item >= COLLECTION_ITEM_COUNT)
        return 0u;
    return (u8)((gVegaModernSaveData->item_obtained_flags[item >> 3]
                 >> (item & 7u)) & 1u);
}

static void set_item_claimed(u16 item, u8 value)
{
    u8 mask;
    if (item >= COLLECTION_ITEM_COUNT)
        return;
    mask = (u8)(1u << (item & 7u));
    if (value)
        gVegaModernSaveData->item_obtained_flags[item >> 3] |= mask;
    else
        gVegaModernSaveData->item_obtained_flags[item >> 3]
            &= (u8)~mask;
    VegaSaveFinalize(gVegaModernSaveData);
}

static void clear_pending(void)
{
    G_OWNER->pending_phase = COLLECTION_PENDING_NONE;
    G_OWNER->pending_kind = COLLECTION_PENDING_NONE;
    G_OWNER->pending_currency = COLLECTION_CURRENCY_NONE;
    G_OWNER->pending_claim_kind = COLLECTION_CLAIM_NONE;
    G_OWNER->pending_key = 0u;
    G_OWNER->pending_item = 0u;
    G_OWNER->pending_quantity = 0u;
    G_OWNER->pending_balance_before = 0u;
    G_OWNER->pending_bag_before = 0u;
    G_OWNER->pending_species = 0u;
    G_OWNER->pending_personality = 0u;
    G_OWNER->pending_host = 0u;
    G_OWNER->pending_entry = 0u;
}

static u8 mon_exists(u16 species, u32 personality)
{
    u8 index;
    u8 box;
    u8 slot;
    if (G_STATE->test_mode && G_STATE->test_gift_species == species
        && G_STATE->test_gift_personality == personality)
        return 1u;
    for (index = 0u; index < *G_PARTY_COUNT && index < COLLECTION_PARTY_SIZE;
         ++index) {
        u8 *mon = G_PLAYER_PARTY + (u32)index * COLLECTION_MON_SIZE;
        if ((u16)FN_GET_MON_DATA(mon, COLLECTION_MON_DATA_SPECIES2,
                                (u8 *)0) == species
            && FN_GET_MON_DATA(mon, COLLECTION_MON_DATA_PERSONALITY,
                               (u8 *)0) == personality)
            return 1u;
    }
    for (box = 0u; box < COLLECTION_BOX_COUNT; ++box) {
        for (slot = 0u; slot < COLLECTION_BOX_CAPACITY; ++slot) {
            if ((u16)FN_GET_BOX_MON_DATA_AT(
                    box, slot, COLLECTION_MON_DATA_SPECIES) == species
                && FN_GET_BOX_MON_DATA_AT(
                    box, slot, COLLECTION_MON_DATA_PERSONALITY) == personality)
                return 1u;
        }
    }
    return 0u;
}

static void recover_pending(void)
{
    u8 mutated = 0u;
    if (!owner_valid() || G_OWNER->pending_phase == COLLECTION_PENDING_NONE)
        return;
    if (G_OWNER->pending_kind == COLLECTION_PENDING_ITEM) {
        u16 count = bag_count(G_OWNER->pending_item);
        mutated = (u8)(count >= (u16)(G_OWNER->pending_bag_before
                                      + G_OWNER->pending_quantity));
        if (mutated && G_OWNER->pending_claim_kind == COLLECTION_CLAIM_ITEM)
            set_item_claimed(G_OWNER->pending_item, 1u);
        if (!mutated)
            currency_set(G_OWNER->pending_currency,
                         G_OWNER->pending_balance_before);
    } else if (G_OWNER->pending_kind == COLLECTION_PENDING_GIFT) {
        mutated = mon_exists(G_OWNER->pending_species,
                             G_OWNER->pending_personality);
        if (mutated
            && G_OWNER->pending_claim_kind == COLLECTION_CLAIM_FORM_GIFT
            && G_OWNER->pending_key < 8u)
            G_OWNER->form_gift_bits |= (u8)(1u << G_OWNER->pending_key);
    }
    clear_pending();
    ++G_OWNER->generation;
    owner_finalize();
    (void)persist_standard();
    (void)persist_sector();
}

static void finish_owner_restore(void)
{
    volatile u8 *save1;
    ensure_state();
    if (!G_STATE->restore_pending)
        return;
    if (*G_MAIN_CALLBACK2 != COLLECTION_FIELD_MAIN_CALLBACK
        || FN_SCRIPT_CONTEXT2_ENABLED() != 0u)
        return;
    save1 = *G_SAVE_BLOCK1_PTR;
    if (save1 == (volatile u8 *)0 || *G_PARTY_COUNT > COLLECTION_PARTY_SIZE)
        return;
    if (++G_STATE->restore_frames < 4u)
        return;
    FN_READ_FLASH(COLLECTION_SECTOR, COLLECTION_OWNER_FLASH_OFFSET,
                  (void *)G_OWNER, COLLECTION_SUPPLY_OWNER_SIZE);
    if (!owner_valid())
        owner_initialize();
    G_STATE->restore_pending = 0u;
    G_STATE->restore_frames = 0u;
    recover_pending();
}

static u8 ensure_owner(void)
{
    ensure_state();
    if (G_STATE->restore_pending)
        finish_owner_restore();
    if (!owner_valid() && !G_STATE->restore_pending)
        owner_initialize();
    if (owner_valid() && G_OWNER->pending_phase != COLLECTION_PENDING_NONE)
        recover_pending();
    return owner_valid();
}

static u16 acquire_item(u16 item_index, u8 claim_kind)
{
    const CollectionItemRow *row;
    CollectionSupplyOwnerV1 before_owner;
    CollectionSupplyOwnerV1 committed_owner;
    u8 currency;
    u32 balance;
    u16 bag_before;
    if (!ensure_owner() || !ledger_valid()
        || item_index >= COLLECTION_ITEM_COUNT)
        return COLLECTION_RESULT_INVALID;
    row = &gCollectionItemRows[item_index];
    currency = source_currency(row->source);
    if (row->source == COLLECTION_SOURCE_EXCLUDED
        || row->source == COLLECTION_SOURCE_FORM
        || row->source == COLLECTION_SOURCE_STORY
        || row->source == COLLECTION_SOURCE_EXISTING)
        return COLLECTION_RESULT_INVALID;
    if (!unlock_satisfied(row->unlock))
        return COLLECTION_RESULT_LOCKED;
    if (claim_kind == COLLECTION_CLAIM_ITEM && item_claimed(row->item_id))
        return COLLECTION_RESULT_EFFECTLESS;
    balance = currency_balance(currency);
    if (currency != COLLECTION_CURRENCY_NONE && balance < row->price)
        return COLLECTION_RESULT_INSUFFICIENT;
    bag_before = bag_count(row->item_id);
    copy_bytes(&before_owner, G_OWNER, sizeof(before_owner));
    G_OWNER->pending_phase = COLLECTION_PENDING_PREPARED;
    G_OWNER->pending_kind = COLLECTION_PENDING_ITEM;
    G_OWNER->pending_currency = currency;
    G_OWNER->pending_claim_kind = claim_kind;
    G_OWNER->pending_key = item_index;
    G_OWNER->pending_item = row->item_id;
    G_OWNER->pending_quantity = row->quantity;
    G_OWNER->pending_balance_before = balance;
    G_OWNER->pending_bag_before = bag_before;
    owner_finalize();
    if (!persist_sector()) {
        copy_bytes(G_OWNER, &before_owner, sizeof(before_owner));
        return COLLECTION_RESULT_PERSIST_FAILED;
    }
    if (!bag_add(row->item_id, row->quantity)) {
        copy_bytes(G_OWNER, &before_owner, sizeof(before_owner));
        owner_finalize();
        (void)persist_sector();
        return COLLECTION_RESULT_BAG_FULL;
    }
    if (currency != COLLECTION_CURRENCY_NONE)
        currency_set(currency, balance - row->price);
    if (claim_kind == COLLECTION_CLAIM_ITEM)
        set_item_claimed(row->item_id, 1u);
    G_OWNER->pending_phase = COLLECTION_PENDING_STAGED;
    owner_finalize();
    if (!persist_sector() || !persist_standard()) {
        (void)bag_remove(row->item_id, row->quantity);
        currency_set(currency, balance);
        if (claim_kind == COLLECTION_CLAIM_ITEM)
            set_item_claimed(row->item_id, 0u);
        copy_bytes(G_OWNER, &before_owner, sizeof(before_owner));
        owner_finalize();
        (void)persist_standard();
        (void)persist_sector();
        return COLLECTION_RESULT_PERSIST_FAILED;
    }
    copy_bytes(&committed_owner, G_OWNER, sizeof(committed_owner));
    clear_pending();
    ++G_OWNER->transaction_id;
    if (G_OWNER->transaction_id == 0u)
        G_OWNER->transaction_id = 1u;
    ++G_OWNER->generation;
    owner_finalize();
    if (!persist_sector()) {
        copy_bytes(G_OWNER, &committed_owner, sizeof(committed_owner));
        return COLLECTION_RESULT_SUCCESS;
    }
    return COLLECTION_RESULT_SUCCESS;
}

static u16 apply_form(u16 form_index, u16 slot)
{
    const CollectionFormRow *row;
    u8 *mon;
    u16 current;
    u16 target;
    if (form_index >= COLLECTION_FORM_COUNT || slot >= FN_PARTY_COUNT())
        return COLLECTION_RESULT_INVALID;
    row = &gCollectionFormRows[form_index];
    if (row->method != COLLECTION_METHOD_FORM_SERVICE
        || !row->distributable || !unlock_satisfied(row->unlock))
        return COLLECTION_RESULT_LOCKED;
    mon = G_PLAYER_PARTY + (u32)slot * COLLECTION_MON_SIZE;
    current = (u16)FN_GET_MON_DATA(mon, COLLECTION_MON_DATA_SPECIES2,
                                  (u8 *)0);
    if (current == row->base_species)
        target = row->target_species;
    else if (current == row->target_species)
        target = row->base_species;
    else
        return COLLECTION_RESULT_EFFECTLESS;
    G_STATE->previous_species = current;
    FN_SET_MON_DATA(mon, COLLECTION_MON_DATA_SPECIES, &target);
    FN_CALCULATE_STATS(mon);
    if (!persist_standard()) {
        FN_SET_MON_DATA(mon, COLLECTION_MON_DATA_SPECIES, &current);
        FN_CALCULATE_STATS(mon);
        (void)persist_standard();
        return COLLECTION_RESULT_PERSIST_FAILED;
    }
    return COLLECTION_RESULT_SUCCESS;
}

static u8 gmax_species(u16 species)
{
    u16 index;
    for (index = 0u; index < COLLECTION_GMAX_COUNT; ++index) {
        if (gCollectionGmaxRows[index].base_species == species)
            return 1u;
    }
    return 0u;
}

static u16 toggle_gmax(u16 slot)
{
    u8 *mon;
    u16 species;
    if (slot >= FN_PARTY_COUNT())
        return COLLECTION_RESULT_INVALID;
    mon = G_PLAYER_PARTY + (u32)slot * COLLECTION_MON_SIZE;
    species = (u16)FN_GET_MON_DATA(mon, COLLECTION_MON_DATA_SPECIES2,
                                  (u8 *)0);
    if (!gmax_species(species))
        return COLLECTION_RESULT_EFFECTLESS;
    if (!bag_remove(COLLECTION_DYNAMAX_CANDY_ITEM_ID, 1u))
        return COLLECTION_RESULT_INSUFFICIENT;
    mon[COLLECTION_GMAX_BYTE_OFFSET] ^= COLLECTION_GMAX_MASK;
    if (!persist_standard()) {
        mon[COLLECTION_GMAX_BYTE_OFFSET] ^= COLLECTION_GMAX_MASK;
        (void)bag_add(COLLECTION_DYNAMAX_CANDY_ITEM_ID, 1u);
        (void)persist_standard();
        return COLLECTION_RESULT_PERSIST_FAILED;
    }
    return COLLECTION_RESULT_SUCCESS;
}

static u16 deliver_gift(u16 gift_index)
{
    const CollectionGiftRow *gift;
    const CollectionFormRow *form;
    CollectionSupplyOwnerV1 before_owner;
    CollectionSupplyOwnerV1 committed_owner;
    u8 mon[COLLECTION_MON_SIZE];
    u8 egg = 1u;
    u8 destination;
    u32 personality;
    if (!ensure_owner() || gift_index >= COLLECTION_GIFT_COUNT)
        return COLLECTION_RESULT_INVALID;
    gift = &gCollectionGiftRows[gift_index];
    form = &gCollectionFormRows[gift->form_index];
    if (!unlock_satisfied(gift->unlock))
        return COLLECTION_RESULT_LOCKED;
    if (gift->kind == COLLECTION_GIFT_FIXED
        && (G_OWNER->form_gift_bits & (u8)(1u << gift->claim_bit)) != 0u)
        return COLLECTION_RESULT_EFFECTLESS;
    copy_bytes(&before_owner, G_OWNER, sizeof(before_owner));
    clear_bytes(mon, sizeof(mon));
    FN_CREATE_MON(mon, form->target_species,
                  gift->kind == COLLECTION_GIFT_RESEARCH_EGG ? 1u : 50u,
                  32u, 0u, 0u, 0u, 0u);
    if (gift->kind == COLLECTION_GIFT_RESEARCH_EGG)
        FN_SET_MON_DATA(mon, COLLECTION_MON_DATA_IS_EGG, &egg);
    personality = FN_GET_MON_DATA(mon, COLLECTION_MON_DATA_PERSONALITY,
                                  (u8 *)0);
    G_OWNER->pending_phase = COLLECTION_PENDING_PREPARED;
    G_OWNER->pending_kind = COLLECTION_PENDING_GIFT;
    G_OWNER->pending_claim_kind = gift->kind == COLLECTION_GIFT_FIXED
        ? COLLECTION_CLAIM_FORM_GIFT : COLLECTION_CLAIM_NONE;
    G_OWNER->pending_key = gift->claim_bit;
    G_OWNER->pending_species = form->target_species;
    G_OWNER->pending_personality = personality;
    owner_finalize();
    if (!persist_sector()) {
        copy_bytes(G_OWNER, &before_owner, sizeof(before_owner));
        return COLLECTION_RESULT_PERSIST_FAILED;
    }
    if (G_STATE->test_mode) {
        destination = 0u;
        G_STATE->test_gift_species = form->target_species;
        G_STATE->test_gift_personality = personality;
    } else {
        destination = FN_GIVE_MON(mon);
    }
    if (destination >= 2u) {
        copy_bytes(G_OWNER, &before_owner, sizeof(before_owner));
        owner_finalize();
        (void)persist_sector();
        return COLLECTION_RESULT_STORAGE_FULL;
    }
    G_OWNER->pending_phase = COLLECTION_PENDING_STAGED;
    if (gift->kind == COLLECTION_GIFT_FIXED)
        G_OWNER->form_gift_bits |= (u8)(1u << gift->claim_bit);
    owner_finalize();
    if (!persist_sector() || !persist_standard())
        return COLLECTION_RESULT_PERSIST_FAILED;
    copy_bytes(&committed_owner, G_OWNER, sizeof(committed_owner));
    clear_pending();
    ++G_OWNER->generation;
    owner_finalize();
    if (!persist_sector()) {
        copy_bytes(G_OWNER, &committed_owner, sizeof(committed_owner));
        return COLLECTION_RESULT_SUCCESS;
    }
    return COLLECTION_RESULT_SUCCESS;
}

static u8 capture_done(const CollectionPoolRow *row)
{
    if (row->capture_kind == COLLECTION_CAPTURE_SHARED)
        return (u8)((gVegaModernSaveData->shared_special_capture[
                         row->capture_index >> 3]
                     >> (row->capture_index & 7u)) & 1u);
    if (row->capture_kind == COLLECTION_CAPTURE_FORM)
        return (u8)((G_OWNER->raid_form_capture_bits
                     >> row->capture_index) & 1u);
    return 0u;
}

static u8 reward_done(const CollectionPoolRow *row)
{
    if (row->capture_kind != COLLECTION_CAPTURE_SHARED || !row->reward_once)
        return 0u;
    return (u8)((gVegaModernSaveData->raid_reward_claimed[
                     row->capture_index >> 3]
                 >> (row->capture_index & 7u)) & 1u);
}

static void mark_capture(const CollectionPoolRow *row)
{
    if (row->capture_kind == COLLECTION_CAPTURE_SHARED) {
        gVegaModernSaveData->shared_special_capture[row->capture_index >> 3]
            |= (u8)(1u << (row->capture_index & 7u));
        VegaSaveFinalize(gVegaModernSaveData);
    } else if (row->capture_kind == COLLECTION_CAPTURE_FORM)
        G_OWNER->raid_form_capture_bits |= (u8)(1u << row->capture_index);
}

static void mark_reward(const CollectionPoolRow *row)
{
    if (row->capture_kind == COLLECTION_CAPTURE_SHARED && row->reward_once) {
        gVegaModernSaveData->raid_reward_claimed[row->capture_index >> 3]
            |= (u8)(1u << (row->capture_index & 7u));
        VegaSaveFinalize(gVegaModernSaveData);
    }
}

static u16 select_reward(u8 host)
{
    const CollectionHostRow *host_row = &gCollectionHostRows[host];
    u16 index;
    u32 total = 0u;
    u32 pick;
    u8 first = (u8)((G_OWNER->raid_first_clear_bits
                     & (u16)(1u << host)) == 0u);
    for (index = 0u; index < COLLECTION_REWARD_COUNT; ++index) {
        const CollectionRewardRow *row = &gCollectionRewardRows[index];
        if (row->pool == host_row->reward_pool
            && unlock_satisfied(row->unlock)
            && (!first || row->first_clear))
            total += row->weight;
    }
    if (total == 0u && first) {
        first = 0u;
        for (index = 0u; index < COLLECTION_REWARD_COUNT; ++index) {
            const CollectionRewardRow *row = &gCollectionRewardRows[index];
            if (row->pool == host_row->reward_pool
                && unlock_satisfied(row->unlock))
                total += row->weight;
        }
    }
    if (total == 0u)
        return 0xFFFFu;
    pick = (u32)random16() % total;
    for (index = 0u; index < COLLECTION_REWARD_COUNT; ++index) {
        const CollectionRewardRow *row = &gCollectionRewardRows[index];
        if (row->pool != host_row->reward_pool
            || !unlock_satisfied(row->unlock)
            || (first && !row->first_clear))
            continue;
        if (pick < row->weight)
            return index;
        pick -= row->weight;
    }
    return 0xFFFFu;
}

static u16 grant_raid_reward(u8 host, u16 entry_index)
{
    const CollectionPoolRow *pool = &gCollectionPoolRows[entry_index];
    u16 reward_index = select_reward(host);
    const CollectionRewardRow *reward;
    CollectionSupplyOwnerV1 before_owner;
    CollectionSupplyOwnerV1 committed_owner;
    u8 reward_was_done;
    u16 bag_before;
    u8 quantity;
    if (reward_index == 0xFFFFu)
        return COLLECTION_RESULT_INVALID;
    reward = &gCollectionRewardRows[reward_index];
    quantity = reward->quantity_min;
    if (reward->quantity_max > reward->quantity_min)
        quantity = (u8)(quantity + random16()
            % (u16)(reward->quantity_max - reward->quantity_min + 1u));
    copy_bytes(&before_owner, G_OWNER, sizeof(before_owner));
    reward_was_done = reward_done(pool);
    bag_before = bag_count(reward->item_id);
    G_OWNER->pending_phase = COLLECTION_PENDING_PREPARED;
    G_OWNER->pending_kind = COLLECTION_PENDING_ITEM;
    G_OWNER->pending_currency = COLLECTION_CURRENCY_NONE;
    G_OWNER->pending_claim_kind = COLLECTION_CLAIM_NONE;
    G_OWNER->pending_item = reward->item_id;
    G_OWNER->pending_quantity = quantity;
    G_OWNER->pending_bag_before = bag_before;
    G_OWNER->pending_host = host;
    G_OWNER->pending_entry = entry_index;
    owner_finalize();
    if (!persist_sector()) {
        copy_bytes(G_OWNER, &before_owner, sizeof(before_owner));
        return COLLECTION_RESULT_PERSIST_FAILED;
    }
    if (!bag_add(reward->item_id, quantity)) {
        copy_bytes(G_OWNER, &before_owner, sizeof(before_owner));
        G_OWNER->pending_reward_host = (u8)(host + 1u);
        owner_finalize();
        (void)persist_standard();
        (void)persist_sector();
        return COLLECTION_RESULT_BAG_FULL;
    }
    G_OWNER->pending_reward_host = 0u;
    G_OWNER->raid_first_clear_bits |= (u16)(1u << host);
    ++G_OWNER->rotation[host];
    mark_reward(pool);
    G_OWNER->pending_phase = COLLECTION_PENDING_STAGED;
    owner_finalize();
    if (!persist_sector() || !persist_standard()) {
        (void)bag_remove(reward->item_id, quantity);
        if (!reward_was_done && pool->capture_kind == COLLECTION_CAPTURE_SHARED
            && pool->reward_once) {
            gVegaModernSaveData->raid_reward_claimed[pool->capture_index >> 3]
                &= (u8)~(1u << (pool->capture_index & 7u));
            VegaSaveFinalize(gVegaModernSaveData);
        }
        copy_bytes(G_OWNER, &before_owner, sizeof(before_owner));
        G_OWNER->pending_reward_host = (u8)(host + 1u);
        owner_finalize();
        (void)persist_standard();
        (void)persist_sector();
        return COLLECTION_RESULT_PERSIST_FAILED;
    }
    copy_bytes(&committed_owner, G_OWNER, sizeof(committed_owner));
    clear_pending();
    ++G_OWNER->generation;
    owner_finalize();
    if (!persist_sector()) {
        copy_bytes(G_OWNER, &committed_owner, sizeof(committed_owner));
        return COLLECTION_RESULT_SUCCESS;
    }
    return COLLECTION_RESULT_SUCCESS;
}

static u16 prepare_raid(u8 host)
{
    const CollectionHostRow *host_row;
    u16 index;
    u32 total = 0u;
    u32 pick;
    if (!ensure_owner() || host >= COLLECTION_HOST_COUNT)
        return COLLECTION_RESULT_INVALID;
    host_row = &gCollectionHostRows[host];
    if (!unlock_satisfied(host_row->unlock))
        return COLLECTION_RESULT_LOCKED;
    for (index = 0u; index < COLLECTION_POOL_COUNT; ++index) {
        const CollectionPoolRow *row = &gCollectionPoolRows[index];
        if (row->pool == host_row->pool && unlock_satisfied(row->unlock)
            && !(capture_done(row) && reward_done(row)))
            total += row->weight;
    }
    if (total == 0u)
        return COLLECTION_RESULT_EFFECTLESS;
    pick = (u32)G_OWNER->rotation[host] % total;
    for (index = 0u; index < COLLECTION_POOL_COUNT; ++index) {
        const CollectionPoolRow *row = &gCollectionPoolRows[index];
        if (row->pool != host_row->pool || !unlock_satisfied(row->unlock)
            || (capture_done(row) && reward_done(row)))
            continue;
        if (pick < row->weight) {
            G_STATE->host = host;
            G_STATE->active_entry = index;
            G_STATE->active_species = row->species;
            return COLLECTION_RESULT_RAID_REQUEST;
        }
        pick -= row->weight;
    }
    return COLLECTION_RESULT_INVALID;
}

static u16 start_prepared_raid(void)
{
    const CollectionPoolRow *row;
    const CollectionHostRow *host;
    u8 level;
    if (G_STATE->active_entry >= COLLECTION_POOL_COUNT
        || G_STATE->host >= COLLECTION_HOST_COUNT)
        return COLLECTION_RESULT_INVALID;
    row = &gCollectionPoolRows[G_STATE->active_entry];
    host = &gCollectionHostRows[G_STATE->host];
    if (capture_done(row))
        return grant_raid_reward(G_STATE->host, G_STATE->active_entry);
    level = row->level_min;
    if (row->level_max > row->level_min)
        level = (u8)(level + random16()
            % (u16)(row->level_max - row->level_min + 1u));
    clear_bytes(G_ENEMY_PARTY, COLLECTION_MON_SIZE * COLLECTION_PARTY_SIZE);
    FN_CREATE_MON(G_ENEMY_PARTY, row->species, level, 32u, 0u, 0u, 0u, 0u);
    G_STATE->active_personality = FN_GET_MON_DATA(
        G_ENEMY_PARTY, COLLECTION_MON_DATA_PERSONALITY, (u8 *)0);
    G_STATE->active_gmax = (u8)(row->gmax_chance != 0u
        && ((u32)random16() * 100u >> 16) < row->gmax_chance);
    if (G_STATE->active_gmax)
        G_ENEMY_PARTY[COLLECTION_GMAX_BYTE_OFFSET] |= COLLECTION_GMAX_MASK;
    if (!G_STATE->test_mode
        && !FN_CONFIGURE_RAID(0u, host->high_raid ? 6u : 0u,
                              host->high_raid ? 5u : 0u, 10u, 1u))
        return COLLECTION_RESULT_ENGINE_REJECTED;
    G_STATE->raid_active = 1u;
    if (!G_STATE->test_mode)
        FN_START_WILD();
    return COLLECTION_RESULT_BATTLE_STARTED;
}

static u16 complete_raid(u8 caught)
{
    const CollectionPoolRow *row;
    if (!G_STATE->raid_active || G_STATE->active_entry >= COLLECTION_POOL_COUNT)
        return COLLECTION_RESULT_INVALID;
    row = &gCollectionPoolRows[G_STATE->active_entry];
    if (caught) {
        u16 result;
        mark_capture(row);
        result = grant_raid_reward(G_STATE->host, G_STATE->active_entry);
        G_STATE->raid_active = 0u;
        G_STATE->active_entry = 0xFFFFu;
        return result;
    }
    G_STATE->raid_active = 0u;
    G_STATE->active_entry = 0xFFFFu;
    return COLLECTION_RESULT_SUCCESS;
}

static u16 eligible_count(void);
static u16 eligible_at(u16 ordinal);
static u8 render_menu(u8 task_id);

static void close_window(u8 task_id)
{
    u8 window = (u8)G_TASKS[task_id].data[0];
    if (window == COLLECTION_WINDOW_INVALID)
        return;
    FN_CLEAR_FRAME(window, 0u);
    FN_REMOVE_WINDOW(window);
    FN_SCHEDULE_BG(0u);
    G_TASKS[task_id].data[0] = COLLECTION_WINDOW_INVALID;
    G_STATE->window_id = COLLECTION_WINDOW_INVALID;
}

static const u8 *service_text(u8 service)
{
    switch (service) {
    case COLLECTION_SERVICE_MONEY: return gCollectionTextMoney;
    case COLLECTION_SERVICE_BP: return gCollectionTextBp;
    case COLLECTION_SERVICE_RESEARCH: return gCollectionTextResearch;
    case COLLECTION_SERVICE_FORM: return gCollectionTextForm;
    case COLLECTION_SERVICE_RELIC: return gCollectionTextRelic;
    case COLLECTION_SERVICE_GIFT: return gCollectionTextGift;
    case COLLECTION_SERVICE_GMAX: return gCollectionTextGmax;
    default: return gCollectionTextCancel;
    }
}

static u8 source_for_service(u8 service)
{
    if (service == COLLECTION_SERVICE_MONEY)
        return COLLECTION_SOURCE_MONEY;
    if (service == COLLECTION_SERVICE_BP)
        return COLLECTION_SOURCE_BP;
    if (service == COLLECTION_SERVICE_RESEARCH)
        return COLLECTION_SOURCE_RESEARCH;
    return COLLECTION_SOURCE_EXCLUDED;
}

static u16 eligible_count(void)
{
    u16 count = 0u;
    u16 index;
    if (G_STATE->menu_mode == COLLECTION_MENU_ITEMS) {
        u8 source = source_for_service(G_STATE->service);
        for (index = 0u; index < COLLECTION_ITEM_COUNT; ++index)
            if (gCollectionItemRows[index].source == source
                && unlock_satisfied(gCollectionItemRows[index].unlock))
                ++count;
    } else if (G_STATE->menu_mode == COLLECTION_MENU_FORMS) {
        for (index = 0u; index < COLLECTION_SERVICE_FORM_COUNT; ++index)
            if (unlock_satisfied(gCollectionFormRows[
                    gCollectionServiceFormIndices[index]].unlock))
                ++count;
    } else if (G_STATE->menu_mode == COLLECTION_MENU_GIFTS) {
        for (index = 0u; index < COLLECTION_GIFT_COUNT; ++index)
            if (unlock_satisfied(gCollectionGiftRows[index].unlock)
                && (gCollectionGiftRows[index].kind
                        == COLLECTION_GIFT_RESEARCH_EGG
                    || (G_OWNER->form_gift_bits
                        & (u8)(1u << gCollectionGiftRows[index].claim_bit))
                       == 0u))
                ++count;
    } else if (G_STATE->menu_mode == COLLECTION_MENU_RELICS) {
        for (index = 0u; index < COLLECTION_RELIC_COUNT; ++index) {
            u16 item_index = gCollectionRelicItemIndices[index];
            if (!item_claimed(gCollectionItemRows[item_index].item_id)
                && unlock_satisfied(gCollectionItemRows[item_index].unlock))
                ++count;
        }
    }
    return count;
}

static u16 eligible_at(u16 ordinal)
{
    u16 seen = 0u;
    u16 index;
    if (G_STATE->menu_mode == COLLECTION_MENU_ITEMS) {
        u8 source = source_for_service(G_STATE->service);
        for (index = 0u; index < COLLECTION_ITEM_COUNT; ++index) {
            if (gCollectionItemRows[index].source != source
                || !unlock_satisfied(gCollectionItemRows[index].unlock))
                continue;
            if (seen++ == ordinal)
                return index;
        }
    } else if (G_STATE->menu_mode == COLLECTION_MENU_FORMS) {
        for (index = 0u; index < COLLECTION_SERVICE_FORM_COUNT; ++index) {
            u16 form = gCollectionServiceFormIndices[index];
            if (!unlock_satisfied(gCollectionFormRows[form].unlock))
                continue;
            if (seen++ == ordinal)
                return form;
        }
    } else if (G_STATE->menu_mode == COLLECTION_MENU_GIFTS) {
        for (index = 0u; index < COLLECTION_GIFT_COUNT; ++index) {
            const CollectionGiftRow *gift = &gCollectionGiftRows[index];
            if (!unlock_satisfied(gift->unlock)
                || (gift->kind == COLLECTION_GIFT_FIXED
                    && (G_OWNER->form_gift_bits
                        & (u8)(1u << gift->claim_bit)) != 0u))
                continue;
            if (seen++ == ordinal)
                return index;
        }
    } else if (G_STATE->menu_mode == COLLECTION_MENU_RELICS) {
        for (index = 0u; index < COLLECTION_RELIC_COUNT; ++index) {
            u16 item_index = gCollectionRelicItemIndices[index];
            if (item_claimed(gCollectionItemRows[item_index].item_id)
                || !unlock_satisfied(gCollectionItemRows[item_index].unlock))
                continue;
            if (seen++ == ordinal)
                return item_index;
        }
    }
    return 0xFFFFu;
}

static const u8 *row_text(u16 index)
{
    if (G_STATE->menu_mode == COLLECTION_MENU_ITEMS
        || G_STATE->menu_mode == COLLECTION_MENU_RELICS)
        return gCollectionItemRows[index].name;
    if (G_STATE->menu_mode == COLLECTION_MENU_FORMS)
        return gCollectionFormRows[index].name;
    if (G_STATE->menu_mode == COLLECTION_MENU_GIFTS)
        return gCollectionGiftRows[index].name;
    return gCollectionTextCancel;
}

static u8 render_menu(u8 task_id)
{
    struct WindowTemplate window;
    u16 count = G_STATE->menu_mode == COLLECTION_MENU_ROOT
        ? 2u : eligible_count();
    u16 first = (u16)(G_STATE->page * COLLECTION_PAGE_SIZE);
    u8 rows = G_STATE->menu_mode == COLLECTION_MENU_ROOT ? 2u
        : (u8)(count > first ? (u16)(count - first) : (u16)0u);
    u8 has_next;
    u8 menu_count;
    u8 index;
    u8 window_id;
    if (rows > COLLECTION_PAGE_SIZE)
        rows = COLLECTION_PAGE_SIZE;
    has_next = (u8)(first + rows < count);
    menu_count = (u8)(rows + 1u);
    window.bg = 0u;
    window.tilemap_left = 7u;
    window.tilemap_top = 0u;
    window.width = 22u;
    window.height = (u8)(menu_count * 2u + 2u);
    window.palette_num = 15u;
    window.base_block = FN_BASE_TILE();
    window_id = (u8)FN_ADD_WINDOW(&window);
    if (window_id == COLLECTION_WINDOW_INVALID)
        return 0u;
    G_TASKS[task_id].data[0] = window_id;
    G_STATE->window_id = window_id;
    FN_FILL_WINDOW(window_id, 0x11u);
    FN_DRAW_FRAME(window_id, 0u);
    FN_PUT_WINDOW_TILEMAP(window_id);
    if (G_STATE->menu_mode == COLLECTION_MENU_ROOT) {
        FN_ADD_TEXT(window_id, 2u, gCollectionTextRaid,
                    8u, 1u, 0u, (void *)0);
        FN_ADD_TEXT(window_id, 2u, service_text(G_STATE->service),
                    8u, 17u, 0u, (void *)0);
    } else {
        for (index = 0u; index < rows; ++index) {
            u16 selected = eligible_at((u16)(first + index));
            FN_ADD_TEXT(window_id, 2u, row_text(selected),
                        8u, (u8)(1u + index * 16u), 0u, (void *)0);
        }
    }
    FN_ADD_TEXT(window_id, 2u,
                has_next ? gCollectionTextNext : gCollectionTextCancel,
                8u, (u8)(1u + rows * 16u), 0u, (void *)0);
    FN_MENU_INIT(window_id, 2u, 0u, 1u, 16u, menu_count, 0u);
    FN_COPY_WINDOW(window_id, COLLECTION_COPYWIN_BOTH);
    FN_SCHEDULE_BG(0u);
    return 1u;
}

static void finish_menu(u8 task_id, u16 result)
{
    close_window(task_id);
    FN_DESTROY_TASK(task_id);
    FN_PLAY_SE(COLLECTION_SE_SELECT);
    set_result(result);
    FN_ENABLE_BOTH_CONTEXTS();
}

static void enter_service_menu(u8 task_id)
{
    close_window(task_id);
    G_STATE->page = 0u;
    if (G_STATE->service == COLLECTION_SERVICE_FORM)
        G_STATE->menu_mode = COLLECTION_MENU_FORMS;
    else if (G_STATE->service == COLLECTION_SERVICE_GIFT)
        G_STATE->menu_mode = COLLECTION_MENU_GIFTS;
    else if (G_STATE->service == COLLECTION_SERVICE_RELIC)
        G_STATE->menu_mode = COLLECTION_MENU_RELICS;
    else
        G_STATE->menu_mode = COLLECTION_MENU_ITEMS;
    if (!render_menu(task_id))
        finish_menu(task_id, COLLECTION_RESULT_ENGINE_REJECTED);
}

static void Task_CollectionMenu(u8 task_id)
{
    s8 choice = FN_MENU_INPUT();
    u16 count;
    u16 first;
    u8 rows;
    u8 has_next;
    u16 selected;
    u16 result;
    if (choice == COLLECTION_MENU_NOTHING)
        return;
    if (choice == COLLECTION_MENU_B || choice < 0) {
        finish_menu(task_id, COLLECTION_RESULT_CANCELLED);
        return;
    }
    if (G_STATE->menu_mode == COLLECTION_MENU_ROOT) {
        if (choice == 0) {
            result = prepare_raid(G_STATE->host);
            finish_menu(task_id, result);
        } else if (choice == 1) {
            if (G_STATE->service == COLLECTION_SERVICE_GMAX)
                finish_menu(task_id, COLLECTION_RESULT_GMAX_REQUEST);
            else
                enter_service_menu(task_id);
        } else
            finish_menu(task_id, COLLECTION_RESULT_CANCELLED);
        return;
    }
    count = eligible_count();
    first = (u16)(G_STATE->page * COLLECTION_PAGE_SIZE);
    rows = (u8)(count > first ? (u16)(count - first) : (u16)0u);
    if (rows > COLLECTION_PAGE_SIZE)
        rows = COLLECTION_PAGE_SIZE;
    has_next = (u8)(first + rows < count);
    if ((u8)choice == rows) {
        if (has_next) {
            close_window(task_id);
            ++G_STATE->page;
            if (!render_menu(task_id))
                finish_menu(task_id, COLLECTION_RESULT_ENGINE_REJECTED);
        } else
            finish_menu(task_id, COLLECTION_RESULT_CANCELLED);
        return;
    }
    if ((u8)choice >= rows) {
        finish_menu(task_id, COLLECTION_RESULT_INVALID);
        return;
    }
    selected = eligible_at((u16)(first + (u8)choice));
    if (selected == 0xFFFFu) {
        finish_menu(task_id, COLLECTION_RESULT_INVALID);
        return;
    }
    G_STATE->pending_index = selected;
    if (G_STATE->menu_mode == COLLECTION_MENU_FORMS)
        result = COLLECTION_RESULT_FORM_REQUEST;
    else if (G_STATE->menu_mode == COLLECTION_MENU_GIFTS)
        result = deliver_gift(selected);
    else if (G_STATE->menu_mode == COLLECTION_MENU_RELICS)
        result = acquire_item(selected, COLLECTION_CLAIM_ITEM);
    else
        result = acquire_item(selected, COLLECTION_CLAIM_NONE);
    finish_menu(task_id, result);
}

COLLECTION_EXPORT(CollectionSupply_Probe)
u32 CollectionSupply_Probe(u32 query)
{
    ensure_state();
    if (query == 0u) return COLLECTION_SUPPLY_ABI_VERSION;
    if (query == 1u) return COLLECTION_FORM_COUNT;
    if (query == 2u) return COLLECTION_GMAX_COUNT;
    if (query == 3u) return COLLECTION_ITEM_COUNT;
    if (query == 4u) return COLLECTION_HOST_COUNT;
    if (query == 5u) return COLLECTION_POOL_COUNT;
    if (query == 6u) return COLLECTION_REWARD_COUNT;
    if (query == 7u) return COLLECTION_SUPPLY_OWNER_ADDRESS;
    if (query == 8u) return COLLECTION_SUPPLY_OWNER_SIZE;
    return 0u;
}

COLLECTION_EXPORT(CollectionSupply_FieldHost)
u16 CollectionSupply_FieldHost(void)
{
    u16 host = *G_VAR_8004;
    u8 task;
    if (!ensure_owner() || host >= COLLECTION_HOST_COUNT) {
        set_result(COLLECTION_RESULT_INVALID);
        return COLLECTION_RESULT_INVALID;
    }
    clear_bytes(G_STATE, COLLECTION_SUPPLY_VOLATILE_SIZE);
    G_STATE->magic = COLLECTION_STATE_MAGIC;
    G_STATE->magic_inverse = ~COLLECTION_STATE_MAGIC;
    G_STATE->host = (u8)host;
    G_STATE->service = gCollectionHostRows[host].service;
    G_STATE->menu_mode = COLLECTION_MENU_ROOT;
    G_STATE->window_id = COLLECTION_WINDOW_INVALID;
    G_STATE->active_entry = 0xFFFFu;
    G_STATE->pending_index = 0xFFFFu;
    task = FN_CREATE_TASK(Task_CollectionMenu, 0x50u);
    if (task >= COLLECTION_NUM_TASKS) {
        set_result(COLLECTION_RESULT_ENGINE_REJECTED);
        return COLLECTION_RESULT_ENGINE_REJECTED;
    }
    G_TASKS[task].data[0] = COLLECTION_WINDOW_INVALID;
    if (!render_menu(task)) {
        FN_DESTROY_TASK(task);
        set_result(COLLECTION_RESULT_ENGINE_REJECTED);
        return COLLECTION_RESULT_ENGINE_REJECTED;
    }
    set_result(COLLECTION_RESULT_BUSY);
    FN_SCRIPT_CONTEXT2_ENABLE();
    return COLLECTION_RESULT_BUSY;
}

COLLECTION_EXPORT(CollectionSupply_ApplySelectedForm)
u16 CollectionSupply_ApplySelectedForm(void)
{
    u16 result = apply_form(G_STATE->pending_index, *G_VAR_8004);
    set_result(result);
    return result;
}

COLLECTION_EXPORT(CollectionSupply_ApplySelectedGmax)
u16 CollectionSupply_ApplySelectedGmax(void)
{
    u16 result = toggle_gmax(*G_VAR_8004);
    set_result(result);
    return result;
}

COLLECTION_EXPORT(CollectionSupply_StartSelectedRaid)
u16 CollectionSupply_StartSelectedRaid(void)
{
    u16 result = start_prepared_raid();
    set_result(result);
    return result;
}

COLLECTION_EXPORT(CollectionSupply_ReadKeysAdapter)
void CollectionSupply_ReadKeysAdapter(void)
{
    FN_BASE_READ_KEYS();
    finish_owner_restore();
}

COLLECTION_EXPORT(CollectionSupply_SaveLoadAdapter)
u8 CollectionSupply_SaveLoadAdapter(u8 save_type)
{
    u8 result = FN_BASE_SAVE_LOAD(save_type);
    ensure_state();
    clear_bytes(G_OWNER, COLLECTION_SUPPLY_OWNER_SIZE);
    G_STATE->restore_pending = (u8)(result == 1u);
    G_STATE->restore_frames = 0u;
    if (result != 1u)
        owner_initialize();
    return result;
}

COLLECTION_EXPORT(CollectionSupply_TryGenerateWildMonAdapter)
u8 CollectionSupply_TryGenerateWildMonAdapter(const void *info, u8 area,
                                               u8 flags)
{
    u8 result = FN_BASE_LAND_WATER(info, area, flags);
    u16 species;
    u16 index;
    u16 matches = 0u;
    u16 selected = 0xFFFFu;
    if (!result || !ledger_valid()
        || !unlock_satisfied(COLLECTION_UNLOCK_RESEARCH_PROFILE)
        || ((u32)random16() & 3u) != 0u)
        return result;
    species = (u16)FN_GET_MON_DATA(G_ENEMY_PARTY,
                                   COLLECTION_MON_DATA_SPECIES2, (u8 *)0);
    for (index = 0u; index < COLLECTION_WILD_FORM_COUNT; ++index) {
        u16 form = gCollectionWildFormIndices[index];
        if (gCollectionFormRows[form].base_species == species)
            ++matches;
    }
    if (matches == 0u)
        return result;
    matches = (u16)(random16() % matches);
    for (index = 0u; index < COLLECTION_WILD_FORM_COUNT; ++index) {
        u16 form = gCollectionWildFormIndices[index];
        if (gCollectionFormRows[form].base_species != species)
            continue;
        if (matches-- == 0u) {
            selected = form;
            break;
        }
    }
    if (selected != 0xFFFFu) {
        u16 target = gCollectionFormRows[selected].target_species;
        FN_SET_MON_DATA(G_ENEMY_PARTY, COLLECTION_MON_DATA_SPECIES, &target);
        FN_CALCULATE_STATS(G_ENEMY_PARTY);
    }
    return result;
}

COLLECTION_EXPORT(CollectionSupply_EndWildBattleCommitInternal)
void CollectionSupply_EndWildBattleCommitInternal(void)
{
    ensure_state();
    if (G_STATE->raid_active)
        complete_raid((u8)(*G_BATTLE_OUTCOME
                           == COLLECTION_BATTLE_OUTCOME_CAUGHT));
}

COLLECTION_EXPORT(CollectionSupply_EndWildBattleAdapter)
__attribute__((naked)) void CollectionSupply_EndWildBattleAdapter(void)
{
    __asm__ volatile(
        "push {r4, lr}\n"
        "bl CollectionSupply_EndWildBattleCommitInternal\n"
        "pop {r4}\n"
        "pop {r3}\n"
        "mov lr, r3\n"
        "ldr r3, =%c0\n"
        "bx r3\n"
        :
        : "i" (COLLECTION_DELEGATE_WILD_END)
        : "r3", "memory");
}

COLLECTION_EXPORT(CollectionSupply_TestInitialize)
u16 CollectionSupply_TestInitialize(void)
{
    clear_bytes(G_STATE, COLLECTION_SUPPLY_VOLATILE_SIZE);
    G_STATE->magic = COLLECTION_STATE_MAGIC;
    G_STATE->magic_inverse = ~(u32)COLLECTION_STATE_MAGIC;
    G_STATE->test_mode = 1u;
    G_STATE->window_id = COLLECTION_WINDOW_INVALID;
    G_STATE->active_entry = 0xFFFFu;
    G_STATE->pending_index = 0xFFFFu;
    G_STATE->test_bag_capacity = 999u;
    G_STATE->test_rng = 0x13579BDFu;
    VegaSaveInitNew(gVegaModernSaveData, 1u);
    gVegaModernSaveData->kanto_travel_unlocked = 1u;
    gVegaModernSaveData->vega_hall_of_fame = 1u;
    gVegaModernSaveData->league_i_cleared = 1u;
    gVegaModernSaveData->league_ii_cleared = 1u;
    VegaSaveFinalize(gVegaModernSaveData);
    *G_PARTY_COUNT = 0u;
    owner_initialize();
    set_result(COLLECTION_RESULT_SUCCESS);
    return COLLECTION_RESULT_SUCCESS;
}

COLLECTION_EXPORT(CollectionSupply_TestPurchase)
u16 CollectionSupply_TestPurchase(u16 item_index)
{
    u16 result = acquire_item(item_index, COLLECTION_CLAIM_NONE);
    set_result(result);
    return result;
}

COLLECTION_EXPORT(CollectionSupply_TestApplyForm)
u16 CollectionSupply_TestApplyForm(u16 form_index, u16 slot)
{
    u16 result = apply_form(form_index, slot);
    set_result(result);
    return result;
}

COLLECTION_EXPORT(CollectionSupply_TestToggleGmax)
u16 CollectionSupply_TestToggleGmax(u16 slot)
{
    u16 result = toggle_gmax(slot);
    set_result(result);
    return result;
}

COLLECTION_EXPORT(CollectionSupply_TestPrepareRaid)
u16 CollectionSupply_TestPrepareRaid(u16 host)
{
    ensure_state();
    G_STATE->test_mode = 1u;
    set_result(prepare_raid((u8)host));
    return G_STATE->last_result;
}

COLLECTION_EXPORT(CollectionSupply_TestCompleteRaid)
u16 CollectionSupply_TestCompleteRaid(u16 caught)
{
    u16 result = complete_raid((u8)(caught != 0u));
    set_result(result);
    return result;
}

COLLECTION_EXPORT(CollectionSupply_TestGift)
u16 CollectionSupply_TestGift(u16 gift_index)
{
    u16 result = deliver_gift(gift_index);
    set_result(result);
    return result;
}

COLLECTION_EXPORT(CollectionSupply_TestClaimRelic)
u16 CollectionSupply_TestClaimRelic(u16 item_index)
{
    u16 result = acquire_item(item_index, COLLECTION_CLAIM_ITEM);
    set_result(result);
    return result;
}

COLLECTION_EXPORT(CollectionSupply_TestOwnerField)
u32 CollectionSupply_TestOwnerField(u16 field)
{
    if (!ensure_owner())
        return 0u;
    if (field == 0u) return G_OWNER->generation;
    if (field == 1u) return G_OWNER->pending_phase;
    if (field == 2u) return G_OWNER->transaction_id;
    if (field == 3u) return G_OWNER->raid_first_clear_bits;
    if (field == 4u) return G_OWNER->form_gift_bits;
    if (field == 5u) return G_OWNER->raid_form_capture_bits;
    if (field == 6u) return G_OWNER->pending_reward_host;
    if (field == 7u) return G_OWNER->crc32;
    if (field >= 16u && field < 30u)
        return G_OWNER->rotation[field - 16u];
    return 0u;
}

COLLECTION_EXPORT(CollectionSupply_TestBalance)
u32 CollectionSupply_TestBalance(u16 currency)
{
    ensure_state();
    if (currency < COLLECTION_CURRENCY_MONEY
        || currency > COLLECTION_CURRENCY_RESEARCH)
        return 0u;
    return currency_balance((u8)currency);
}

COLLECTION_EXPORT(CollectionSupply_TestSectorRoundTrip)
u16 CollectionSupply_TestSectorRoundTrip(void)
{
    u8 test_mode;
    if (!ensure_owner())
        return COLLECTION_RESULT_INVALID;
    test_mode = G_STATE->test_mode;
    G_STATE->test_mode = 0u;
    if (!persist_sector()) {
        G_STATE->test_mode = test_mode;
        return COLLECTION_RESULT_PERSIST_FAILED;
    }
    clear_bytes(G_OWNER, COLLECTION_SUPPLY_OWNER_SIZE);
    FN_READ_FLASH(COLLECTION_SECTOR, COLLECTION_OWNER_FLASH_OFFSET,
                  (void *)G_OWNER, COLLECTION_SUPPLY_OWNER_SIZE);
    G_STATE->test_mode = test_mode;
    return owner_valid() ? COLLECTION_RESULT_SUCCESS
                         : COLLECTION_RESULT_INVALID;
}

COLLECTION_EXPORT(CollectionSupply_TestSetFault)
u16 CollectionSupply_TestSetFault(u16 fault)
{
    ensure_state();
    if (fault > 3u)
        return COLLECTION_RESULT_INVALID;
    G_STATE->test_fault = (u8)fault;
    return COLLECTION_RESULT_SUCCESS;
}

COLLECTION_EXPORT(CollectionSupply_TestSetBalances)
u16 CollectionSupply_TestSetBalances(u32 money, u16 bp, u16 research)
{
    ensure_state();
    G_STATE->test_money = money;
    G_STATE->test_bp = bp;
    G_STATE->test_research = research;
    return COLLECTION_RESULT_SUCCESS;
}

COLLECTION_EXPORT(CollectionSupply_TestSetBag)
u16 CollectionSupply_TestSetBag(u16 item, u16 quantity, u16 capacity)
{
    ensure_state();
    if (quantity > capacity)
        return COLLECTION_RESULT_INVALID;
    G_STATE->test_bag_item = quantity != 0u ? item : 0u;
    G_STATE->test_bag_quantity = quantity;
    G_STATE->test_bag_capacity = capacity;
    return COLLECTION_RESULT_SUCCESS;
}

COLLECTION_EXPORT(CollectionSupply_TestSeedParty)
u16 CollectionSupply_TestSeedParty(u16 species, u16 slot, u16 gmax)
{
    u8 *mon;
    if (slot >= COLLECTION_PARTY_SIZE || species == 0u)
        return COLLECTION_RESULT_INVALID;
    mon = G_PLAYER_PARTY + (u32)slot * COLLECTION_MON_SIZE;
    clear_bytes(mon, COLLECTION_MON_SIZE);
    FN_CREATE_MON(mon, species, 50u, 32u, 0u, 0u, 0u, 0u);
    if (gmax)
        mon[COLLECTION_GMAX_BYTE_OFFSET] |= COLLECTION_GMAX_MASK;
    if (*G_PARTY_COUNT <= slot)
        *G_PARTY_COUNT = (u8)(slot + 1u);
    return COLLECTION_RESULT_SUCCESS;
}

COLLECTION_EXPORT(CollectionSupply_TestPartyField)
u32 CollectionSupply_TestPartyField(u16 slot, u16 field)
{
    u8 *mon;
    if (slot >= *G_PARTY_COUNT || slot >= COLLECTION_PARTY_SIZE)
        return 0u;
    mon = G_PLAYER_PARTY + (u32)slot * COLLECTION_MON_SIZE;
    if (field == 0u)
        return FN_GET_MON_DATA(mon, COLLECTION_MON_DATA_SPECIES2, (u8 *)0);
    if (field == 1u)
        return (u32)((mon[COLLECTION_GMAX_BYTE_OFFSET]
                      & COLLECTION_GMAX_MASK) != 0u);
    if (field == 2u)
        return FN_GET_MON_DATA(mon, COLLECTION_MON_DATA_PERSONALITY, (u8 *)0);
    if (field == 3u)
        return FN_GET_MON_DATA(mon, COLLECTION_MON_DATA_IS_EGG, (u8 *)0);
    return 0u;
}

COLLECTION_EXPORT(CollectionSupply_TestBagCount)
u16 CollectionSupply_TestBagCount(u16 item)
{
    ensure_state();
    return bag_count(item);
}

COLLECTION_EXPORT(CollectionSupply_TestBagItem)
u16 CollectionSupply_TestBagItem(void)
{
    ensure_state();
    return G_STATE->test_mode ? G_STATE->test_bag_item : 0u;
}

COLLECTION_EXPORT(CollectionSupply_TestGiftField)
u32 CollectionSupply_TestGiftField(u16 field)
{
    ensure_state();
    if (field == 0u)
        return G_STATE->test_gift_species;
    if (field == 1u)
        return G_STATE->test_gift_personality;
    return 0u;
}

COLLECTION_EXPORT(CollectionSupply_TestRaidField)
u32 CollectionSupply_TestRaidField(u16 field)
{
    ensure_state();
    if (field == 0u) return G_STATE->host;
    if (field == 1u) return G_STATE->active_entry;
    if (field == 2u) return G_STATE->active_species;
    if (field == 3u) return G_STATE->active_gmax;
    if (field == 4u) return G_STATE->raid_active;
    return 0u;
}
