/*
 * USER-20260817-BP-SHOP-RUNTIME
 *
 * The existing Factory Trial earns BP in VegaModernSaveData::factory.  This
 * runtime exposes the manifest-owned BP catalog through a paged field menu and
 * commits item + BP as one compensating transaction across the normal save and
 * the project-owned sector 31 ledger.
 */

#include "bp_shop_runtime.h"

#include <stddef.h>
#include <stdint.h>

#include "../save_migration/save_migration.h"

typedef uint8_t u8;
typedef int8_t s8;
typedef uint16_t u16;
typedef int16_t s16;
typedef uint32_t u32;

#define PTR(type, address) ((type)(uintptr_t)(address))

#define BP_SHOP_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))

enum {
    BP_SHOP_PAGE_SIZE = 5,
    BP_SHOP_MENU_MAX_ROWS = 6,
    BP_SHOP_MENU_NOTHING = -2,
    BP_SHOP_MENU_B = -1,
    BP_SHOP_WINDOW_INVALID = 0xFF,
    BP_SHOP_NUM_TASKS = 16,
    BP_SHOP_COPYWIN_BOTH = 3,
    BP_SHOP_SE_SELECT = 5,
    BP_SHOP_SAVE_SECTOR = 31,
    BP_SHOP_SAVE_SECTOR_DATA_SIZE = 0x0FF0,
    BP_SHOP_SAVE_SECTOR_SIZE = 0x1000,
    BP_SHOP_FLAG_BADGE_1 = 0x0820,
    BP_SHOP_FLAG_HALL_OF_FAME = 0x082C,
    BP_SHOP_FLAG_SHIOU_CLEAR = 0x0824,
    BP_SHOP_FLAG_DH_CLEAR = 0x114B,
    BP_SHOP_RESULT_NOT_SET = 0xFFFF
};

typedef enum BpShopUnlockKind {
    BP_UNLOCK_DH_CLEAR = 0,
    BP_UNLOCK_KANTO_EARLY_ACCESS = 1,
    BP_UNLOCK_BADGE_1 = 2,
    BP_UNLOCK_KANTO_DAYCARE_QUEST = 3,
    BP_UNLOCK_BADGE_5 = 4,
    BP_UNLOCK_BADGE_6 = 5,
    BP_UNLOCK_COMPETITIVE_SUPPLY = 6,
    BP_UNLOCK_BADGE_7 = 7,
    BP_UNLOCK_BADGE_8 = 8,
    BP_UNLOCK_KANTO_LEAGUE_CLEAR = 9,
    BP_UNLOCK_UB_PARADOX = 10
} BpShopUnlockKind;

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

typedef struct BpShopCatalogEntry {
    u16 item_id;
    u16 price;
    u8 unlock_kind;
    u8 quantity;
    const u8 *row_text;
} BpShopCatalogEntry;

typedef struct BpShopVolatileState {
    u16 eligible[18];
    u16 last_result;
    u16 last_catalog_index;
    u8 eligible_count;
    u8 page;
    u8 window_id;
    u8 reserved0;
    u8 balance_text[16];
    u8 reserved[68];
} BpShopVolatileState;

_Static_assert(sizeof(struct Task) == 40, "FireRed Task ABI changed");
_Static_assert(sizeof(struct WindowTemplate) == 8,
               "FireRed WindowTemplate ABI changed");
_Static_assert(sizeof(BpShopVolatileState) == VEGA_BP_SHOP_VOLATILE_STATE_BYTES,
               "BP shop volatile reservation changed");

typedef void (*TaskFunc)(u8 task_id);
typedef u8 (*CreateTaskFn)(TaskFunc func, u8 priority);
typedef void (*TaskIdFn)(u8 task_id);
typedef void (*VoidFn)(void);
typedef u8 (*FlagGetFn)(u16 flag);
typedef u8 (*BagFn)(u16 item, u16 quantity);
typedef u8 (*TryWriteSectorFn)(u16 sector, const void *source);
typedef u8 (*TrySavingDataFn)(u8 save_type);
typedef void (*ReadFlashFn)(u16 sector, u32 offset, void *destination,
                            u32 size);
typedef u16 (*AddWindowFn)(const struct WindowTemplate *template);
typedef void (*WindowU8Fn)(u8 window_id);
typedef void (*WindowPairFn)(u8 window_id, u8 value);
typedef void (*TextPrinterFn)(u8 window_id, u8 font_id, const u8 *text,
                              u8 x, u8 y, u8 speed, void *callback);
typedef u8 (*MenuInitCursorFn)(u8 window_id, u8 font_id, u8 left, u8 top,
                               u8 cursor_height, u8 count, u8 cursor);
typedef s8 (*MenuInputFn)(void);
typedef u16 (*GetBaseTileFn)(void);
typedef void (*PlaySeFn)(u16 song);

#define G_BP_SHOP_STATE \
    PTR(BpShopVolatileState *, VEGA_BP_SHOP_VOLATILE_STATE_ADDRESS)
#define G_SPECIAL_RESULT PTR(volatile u16 *, 0x02037004u)
#define G_SPECIAL_VAR_8004 PTR(volatile u16 *, 0x02036FF4u)
#define G_TASKS PTR(struct Task *, 0x030050D0u)

#define FN_FLAG_GET PTR(FlagGetFn, 0x0806DEC5u)
#define FN_CHECK_BAG_HAS_ITEM PTR(BagFn, 0x08099949u)
#define FN_ADD_BAG_ITEM PTR(BagFn, 0x08099A8Du)
#define FN_REMOVE_BAG_ITEM PTR(BagFn, 0x08099BE1u)
#define FN_TRY_WRITE_SECTOR PTR(TryWriteSectorFn, 0x080DA9C1u)
#define FN_TRY_SAVING_DATA PTR(TrySavingDataFn, 0x080DB34Du)
#define FN_READ_FLASH PTR(ReadFlashFn, 0x081C2A55u)
#define FN_SCRIPT_CONTEXT2_ENABLE PTR(VoidFn, 0x08069201u)
#define FN_ENABLE_BOTH_SCRIPT_CONTEXTS PTR(VoidFn, 0x080693F5u)
#define FN_CREATE_TASK PTR(CreateTaskFn, 0x08076BB5u)
#define FN_DESTROY_TASK PTR(TaskIdFn, 0x08076CA1u)
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

#define BP_SHOP_SAVE_BUFFER PTR(u8 *, 0x020399B0u)
#define BP_SHOP_SECTOR31_IMAGE PTR(const u8 *, 0x0203CF9Cu)

/* Generated from manifests/qol_rewards.csv + manifests/item_ids.csv. */
#include "bp_shop_catalog_generated.h"

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
    G_BP_SHOP_STATE->last_result = result;
    *G_SPECIAL_RESULT = result;
}

static u8 persist_save_sector(void)
{
    clear_bytes(BP_SHOP_SAVE_BUFFER, BP_SHOP_SAVE_SECTOR_SIZE);
    copy_bytes(BP_SHOP_SAVE_BUFFER, BP_SHOP_SECTOR31_IMAGE,
               BP_SHOP_SAVE_SECTOR_DATA_SIZE);
    return (u8)(FN_TRY_WRITE_SECTOR(BP_SHOP_SAVE_SECTOR,
                                    BP_SHOP_SAVE_BUFFER) == 1u);
}

static u8 persist_standard_save(void)
{
    return (u8)(FN_TRY_SAVING_DATA(0u) == 1u);
}

static u8 restore_durable_ledger(void)
{
    VegaModernSaveData *candidate;
    FN_READ_FLASH(BP_SHOP_SAVE_SECTOR, 0u, BP_SHOP_SAVE_BUFFER,
                  BP_SHOP_SAVE_SECTOR_SIZE);
    candidate = (VegaModernSaveData *)(void *)(
        BP_SHOP_SAVE_BUFFER
        + (VEGA_SAVE_EWRAM_ADDRESS
           - (u32)(uintptr_t)BP_SHOP_SECTOR31_IMAGE));
    if (VegaSaveValidate(candidate, VEGA_SAVE_LEDGER_SIZE) != VEGA_SAVE_OK)
        return 0u;
    copy_bytes(gVegaModernSaveData, candidate, VEGA_SAVE_LEDGER_SIZE);
    return 1u;
}

static u8 ensure_save(void)
{
    VegaSaveStatus status = VegaSaveValidate(gVegaModernSaveData,
                                             VEGA_SAVE_LEDGER_SIZE);
    if (status == VEGA_SAVE_EMPTY_OR_LEGACY && restore_durable_ledger())
        status = VEGA_SAVE_OK;
    if (status == VEGA_SAVE_EMPTY_OR_LEGACY) {
        VegaSaveInitNew(gVegaModernSaveData,
                        FN_FLAG_GET(BP_SHOP_FLAG_BADGE_1));
        /* The base first save clears expansion sectors; sector 31 is last. */
        if (!persist_standard_save() || !persist_save_sector())
            return 0u;
        return 1u;
    }
    return (u8)(status == VEGA_SAVE_OK);
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

static u8 hall_of_fame(void)
{
    return (u8)(gVegaModernSaveData->vega_hall_of_fame
                || FN_FLAG_GET(BP_SHOP_FLAG_HALL_OF_FAME));
}

static u8 kanto_access(void)
{
    return (u8)(gVegaModernSaveData->kanto_travel_unlocked
                || hall_of_fame()
                || (FN_FLAG_GET(BP_SHOP_FLAG_SHIOU_CLEAR)
                    && FN_FLAG_GET(BP_SHOP_FLAG_DH_CLEAR)));
}

static u8 unlock_satisfied(u8 kind)
{
    switch ((BpShopUnlockKind)kind) {
    case BP_UNLOCK_DH_CLEAR:
        return FN_FLAG_GET(BP_SHOP_FLAG_DH_CLEAR);
    case BP_UNLOCK_KANTO_EARLY_ACCESS:
        return kanto_access();
    case BP_UNLOCK_BADGE_1:
        return FN_FLAG_GET(BP_SHOP_FLAG_BADGE_1);
    case BP_UNLOCK_KANTO_DAYCARE_QUEST:
        /* No second quest bit exists in the v1 save ABI: first Kanto visit is
         * the monotonic physical completion signal for this immediate node. */
        return (u8)(kanto_access() && gVegaModernSaveData->kanto_visited);
    case BP_UNLOCK_BADGE_5:
        return FN_FLAG_GET((u16)(BP_SHOP_FLAG_BADGE_1 + 4u));
    case BP_UNLOCK_BADGE_6:
        return FN_FLAG_GET((u16)(BP_SHOP_FLAG_BADGE_1 + 5u));
    case BP_UNLOCK_COMPETITIVE_SUPPLY:
        return (u8)(hall_of_fame()
                    && popcount8(gVegaModernSaveData->kanto_certifications)
                       >= 4u);
    case BP_UNLOCK_BADGE_7:
        return FN_FLAG_GET((u16)(BP_SHOP_FLAG_BADGE_1 + 6u));
    case BP_UNLOCK_BADGE_8:
        return FN_FLAG_GET((u16)(BP_SHOP_FLAG_BADGE_1 + 7u));
    case BP_UNLOCK_KANTO_LEAGUE_CLEAR:
        return gVegaModernSaveData->league_ii_cleared;
    case BP_UNLOCK_UB_PARADOX:
        return gVegaModernSaveData->league_ii_cleared;
    default:
        return 0u;
    }
}

static u16 purchase_by_index(u16 catalog_index)
{
    const BpShopCatalogEntry *entry;
    u16 old_bp;
    if (!ensure_save())
        return BP_SHOP_RESULT_PERSIST_FAILED;
    if (catalog_index >= BP_SHOP_CATALOG_COUNT)
        return BP_SHOP_RESULT_INVALID_SELECTION;
    entry = &gBpShopCatalog[catalog_index];
    if (!unlock_satisfied(entry->unlock_kind))
        return BP_SHOP_RESULT_LOCKED;
    if (gVegaModernSaveData->factory.battle_points < entry->price)
        return BP_SHOP_RESULT_INSUFFICIENT_BP;

    /* Add first.  AddBagItem is the authoritative pocket/stack capacity check. */
    if (!FN_ADD_BAG_ITEM(entry->item_id, entry->quantity))
        return BP_SHOP_RESULT_BAG_FULL;
    old_bp = gVegaModernSaveData->factory.battle_points;
    if (VegaFactorySpendBattlePoints(gVegaModernSaveData, entry->price)
        != VEGA_SAVE_OK) {
        (void)FN_REMOVE_BAG_ITEM(entry->item_id, entry->quantity);
        return BP_SHOP_RESULT_INSUFFICIENT_BP;
    }

    if (!persist_standard_save()) {
        gVegaModernSaveData->factory.battle_points = old_bp;
        VegaSaveFinalize(gVegaModernSaveData);
        (void)FN_REMOVE_BAG_ITEM(entry->item_id, entry->quantity);
        (void)persist_standard_save();
        (void)persist_save_sector();
        return BP_SHOP_RESULT_PERSIST_FAILED;
    }
    if (!persist_save_sector()) {
        /* The item may already be in the normal save.  Compensate both stores
         * before returning failure so a retry cannot receive a free item. */
        gVegaModernSaveData->factory.battle_points = old_bp;
        VegaSaveFinalize(gVegaModernSaveData);
        (void)FN_REMOVE_BAG_ITEM(entry->item_id, entry->quantity);
        (void)persist_standard_save();
        (void)persist_save_sector();
        return BP_SHOP_RESULT_PERSIST_FAILED;
    }
    return BP_SHOP_RESULT_SUCCESS;
}

static void close_window(u8 task_id)
{
    u8 window_id = (u8)G_TASKS[task_id].data[0];
    if (window_id == BP_SHOP_WINDOW_INVALID)
        return;
    FN_CLEAR_STD_WINDOW_FRAME(window_id, 0u);
    FN_REMOVE_WINDOW(window_id);
    FN_SCHEDULE_BG_COPY(0u);
    G_TASKS[task_id].data[0] = BP_SHOP_WINDOW_INVALID;
    G_BP_SHOP_STATE->window_id = BP_SHOP_WINDOW_INVALID;
}

static u8 page_row_count(void)
{
    u8 first = (u8)(G_BP_SHOP_STATE->page * BP_SHOP_PAGE_SIZE);
    u8 remaining = first < G_BP_SHOP_STATE->eligible_count
        ? (u8)(G_BP_SHOP_STATE->eligible_count - first) : 0u;
    return remaining > BP_SHOP_PAGE_SIZE ? BP_SHOP_PAGE_SIZE : remaining;
}

static void append_balance_text(u16 balance)
{
    u8 *out = G_BP_SHOP_STATE->balance_text;
    u8 index = 0u;
    u16 divisor = 1000u;
    u8 started = 0u;
    while (gBpShopBalancePrefix[index] != 0xFFu
           && index + 1u < sizeof(G_BP_SHOP_STATE->balance_text)) {
        out[index] = gBpShopBalancePrefix[index];
        ++index;
    }
    while (divisor != 0u && index + 1u < sizeof(G_BP_SHOP_STATE->balance_text)) {
        u8 digit = (u8)(balance / divisor);
        if (digit != 0u || started || divisor == 1u) {
            out[index++] = gBpShopDigitGlyphs[digit];
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
    u8 first = (u8)(G_BP_SHOP_STATE->page * BP_SHOP_PAGE_SIZE);
    u8 rows = page_row_count();
    u8 has_next = (u8)(first + rows < G_BP_SHOP_STATE->eligible_count);
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
    if (window_id == BP_SHOP_WINDOW_INVALID)
        return 0u;
    G_TASKS[task_id].data[0] = window_id;
    G_BP_SHOP_STATE->window_id = window_id;
    FN_FILL_WINDOW_PIXEL_BUFFER(window_id, 0x11u);
    FN_DRAW_STD_WINDOW_FRAME(window_id, 0u);
    FN_PUT_WINDOW_TILEMAP(window_id);

    append_balance_text(gVegaModernSaveData->factory.battle_points);
    FN_ADD_TEXT_PRINTER(window_id, 2u, G_BP_SHOP_STATE->balance_text,
                        8u, 1u, 0u, NULL);
    for (index = 0u; index < rows; ++index) {
        u16 catalog_index = G_BP_SHOP_STATE->eligible[first + index];
        FN_ADD_TEXT_PRINTER(window_id, 2u,
                            gBpShopCatalog[catalog_index].row_text,
                            8u, (u8)(17u + index * 16u), 0u, NULL);
    }
    FN_ADD_TEXT_PRINTER(window_id, 2u,
                        has_next ? gBpShopTextNext : gBpShopTextCancel,
                        8u, (u8)(17u + rows * 16u), 0u, NULL);
    FN_MENU_INIT_CURSOR(window_id, 2u, 0u, 17u, 16u, menu_count, 0u);
    FN_COPY_WINDOW_TO_VRAM(window_id, BP_SHOP_COPYWIN_BOTH);
    FN_SCHEDULE_BG_COPY(0u);
    return 1u;
}

static void finish_menu(u8 task_id, u16 catalog_index, u16 result)
{
    close_window(task_id);
    FN_DESTROY_TASK(task_id);
    FN_PLAY_SE(BP_SHOP_SE_SELECT);
    G_BP_SHOP_STATE->last_catalog_index = catalog_index;
    set_result(result);
    FN_ENABLE_BOTH_SCRIPT_CONTEXTS();
}

static void Task_HandleBpShopMenu(u8 task_id)
{
    s8 choice = FN_MENU_PROCESS_INPUT();
    u8 first;
    u8 rows;
    u8 has_next;
    u16 selected;
    u16 result;
    if (choice == BP_SHOP_MENU_NOTHING)
        return;
    first = (u8)(G_BP_SHOP_STATE->page * BP_SHOP_PAGE_SIZE);
    rows = page_row_count();
    has_next = (u8)(first + rows < G_BP_SHOP_STATE->eligible_count);
    if (choice == BP_SHOP_MENU_B || choice < 0) {
        finish_menu(task_id, 0xFFFFu, BP_SHOP_RESULT_CANCELLED);
        return;
    }
    if ((u8)choice == rows) {
        if (has_next) {
            close_window(task_id);
            ++G_BP_SHOP_STATE->page;
            if (!render_menu(task_id))
                finish_menu(task_id, 0xFFFFu,
                            BP_SHOP_RESULT_ENGINE_REJECTED);
        } else {
            finish_menu(task_id, 0xFFFFu, BP_SHOP_RESULT_CANCELLED);
        }
        return;
    }
    if (choice < 0 || (u8)choice >= rows) {
        finish_menu(task_id, 0xFFFFu,
                    BP_SHOP_RESULT_INVALID_SELECTION);
        return;
    }
    selected = G_BP_SHOP_STATE->eligible[first + (u8)choice];
    result = purchase_by_index(selected);
    finish_menu(task_id, selected, result);
}

BP_SHOP_EXPORT(BpShop_Probe)
u16 BpShop_Probe(void)
{
    set_result(VEGA_BP_SHOP_ABI_VERSION);
    return VEGA_BP_SHOP_ABI_VERSION;
}

BP_SHOP_EXPORT(BpShop_EnsureSave)
u16 BpShop_EnsureSave(void)
{
    u16 result = ensure_save() ? 1u : 0u;
    set_result(result);
    return result;
}

BP_SHOP_EXPORT(BpShop_GetBalance)
u16 BpShop_GetBalance(void)
{
    u16 result = ensure_save()
        ? gVegaModernSaveData->factory.battle_points : 0u;
    *G_SPECIAL_RESULT = result;
    return result;
}

BP_SHOP_EXPORT(BpShop_IsItemUnlocked)
u16 BpShop_IsItemUnlocked(u16 catalog_index)
{
    u16 result = (ensure_save() && catalog_index < BP_SHOP_CATALOG_COUNT)
        ? unlock_satisfied(gBpShopCatalog[catalog_index].unlock_kind) : 0u;
    *G_SPECIAL_RESULT = result;
    return result;
}

BP_SHOP_EXPORT(BpShop_PurchaseByIndex)
u16 BpShop_PurchaseByIndex(u16 catalog_index)
{
    u16 result = purchase_by_index(catalog_index);
    G_BP_SHOP_STATE->last_catalog_index = catalog_index;
    set_result(result);
    return result;
}

BP_SHOP_EXPORT(BpShop_PurchaseSelected)
u16 BpShop_PurchaseSelected(void)
{
    return BpShop_PurchaseByIndex(*G_SPECIAL_VAR_8004);
}

BP_SHOP_EXPORT(BpShop_Open)
u16 BpShop_Open(void)
{
    u16 index;
    u8 task_id;
    if (!ensure_save()) {
        set_result(BP_SHOP_RESULT_PERSIST_FAILED);
        return BP_SHOP_RESULT_PERSIST_FAILED;
    }
    clear_bytes(G_BP_SHOP_STATE, sizeof(*G_BP_SHOP_STATE));
    G_BP_SHOP_STATE->window_id = BP_SHOP_WINDOW_INVALID;
    G_BP_SHOP_STATE->last_result = BP_SHOP_RESULT_NOT_SET;
    G_BP_SHOP_STATE->last_catalog_index = 0xFFFFu;
    for (index = 0u; index < BP_SHOP_CATALOG_COUNT; ++index) {
        if (unlock_satisfied(gBpShopCatalog[index].unlock_kind))
            G_BP_SHOP_STATE->eligible[G_BP_SHOP_STATE->eligible_count++] = index;
    }
    if (G_BP_SHOP_STATE->eligible_count == 0u) {
        set_result(BP_SHOP_RESULT_LOCKED);
        return BP_SHOP_RESULT_LOCKED;
    }
    task_id = FN_CREATE_TASK(Task_HandleBpShopMenu, 0x50u);
    if (task_id >= BP_SHOP_NUM_TASKS) {
        set_result(BP_SHOP_RESULT_ENGINE_REJECTED);
        return BP_SHOP_RESULT_ENGINE_REJECTED;
    }
    G_TASKS[task_id].data[0] = BP_SHOP_WINDOW_INVALID;
    if (!render_menu(task_id)) {
        FN_DESTROY_TASK(task_id);
        set_result(BP_SHOP_RESULT_ENGINE_REJECTED);
        return BP_SHOP_RESULT_ENGINE_REJECTED;
    }
    set_result(BP_SHOP_RESULT_BUSY);
    FN_SCRIPT_CONTEXT2_ENABLE();
    return BP_SHOP_RESULT_BUSY;
}

BP_SHOP_EXPORT(BpShop_PostMenu)
void BpShop_PostMenu(void)
{
    u16 result = G_BP_SHOP_STATE->last_result;
    if (result == BP_SHOP_RESULT_NOT_SET)
        result = BP_SHOP_RESULT_CANCELLED;
    *G_SPECIAL_RESULT = result;
}
