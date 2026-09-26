/*
 * USER-MODERNIZATION-MEGA-STONE-BP-SHOP
 *
 * A separate 45-row Factory BP catalog for the post-Stage67 Mega Stones.
 * Claim durability deliberately uses the already-persistent expanded event
 * flags instead of extending VegaModernSaveData's 999-item bitmap.  Each
 * purchase is compensated across Bag, BP, standard save, and sector 31.
 */

#include "modernization_mega_shop.h"

#include <stddef.h>
#include <stdint.h>

#include "../save_migration/save_migration.h"

typedef uint8_t u8;
typedef int8_t s8;
typedef uint16_t u16;
typedef int16_t s16;
typedef uint32_t u32;

#define PTR(type, address) ((type)(uintptr_t)(address))
#define MEGA_SHOP_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))

enum {
    MEGA_SHOP_PAGE_SIZE = 5,
    MEGA_SHOP_MENU_NOTHING = -2,
    MEGA_SHOP_MENU_B = -1,
    MEGA_SHOP_WINDOW_INVALID = 0xFF,
    MEGA_SHOP_NUM_TASKS = 16,
    MEGA_SHOP_COPYWIN_BOTH = 3,
    MEGA_SHOP_SE_SELECT = 5,
    MEGA_SHOP_SAVE_SECTOR = 31,
    MEGA_SHOP_SAVE_SECTOR_DATA_SIZE = 0x0FF0,
    MEGA_SHOP_SAVE_SECTOR_SIZE = 0x1000,
    MEGA_SHOP_FLAG_BADGE_1 = 0x0820,
    MEGA_SHOP_KEY_STONE_ITEM = 580,
    MEGA_SHOP_RESULT_NOT_SET = 0xFFFF
};

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

typedef struct MegaShopCatalogEntry {
    u16 item_id;
    u16 price;
    u16 claim_flag;
    u8 quantity;
    u8 reserved;
    const u8 *row_text;
} MegaShopCatalogEntry;

typedef struct MegaShopVolatileState {
    u16 eligible[MODERNIZATION_MEGA_SHOP_ENTRY_COUNT];
    u16 last_result;
    u16 last_catalog_index;
    u8 eligible_count;
    u8 page;
    u8 window_id;
    u8 reserved0;
    u8 balance_text[16];
    u8 reserved[14];
} MegaShopVolatileState;

#ifndef MODERNIZATION_MEGA_SHOP_HOST_TEST
_Static_assert(sizeof(struct Task) == 40, "FireRed Task ABI changed");
#endif
_Static_assert(sizeof(struct WindowTemplate) == 8,
               "FireRed WindowTemplate ABI changed");
_Static_assert(sizeof(MegaShopVolatileState) == 128,
               "shared BP shop volatile reservation changed");

typedef void (*TaskFunc)(u8 task_id);
typedef u8 (*CreateTaskFn)(TaskFunc func, u8 priority);
typedef void (*TaskIdFn)(u8 task_id);
typedef void (*VoidFn)(void);
typedef u8 (*FlagFn)(u16 flag);
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

#ifdef MODERNIZATION_MEGA_SHOP_HOST_TEST
extern u8 gMegaShopHostVolatileState[128];
extern volatile u16 gMegaShopHostSpecialResult;
extern volatile u16 gMegaShopHostSpecialVar8004;
extern struct Task gMegaShopHostTasks[MEGA_SHOP_NUM_TASKS];
extern VegaModernSaveData gMegaShopHostModernSave;
extern VegaModernSaveData gMegaShopHostFlashRead;
extern u8 MegaShopHost_FlagSet(u16 flag);
extern u8 MegaShopHost_FlagClear(u16 flag);
extern u8 MegaShopHost_FlagGet(u16 flag);
extern u8 MegaShopHost_CheckBagHasItem(u16 item, u16 quantity);
extern u8 MegaShopHost_AddBagItem(u16 item, u16 quantity);
extern u8 MegaShopHost_RemoveBagItem(u16 item, u16 quantity);
extern u8 MegaShopHost_TryWriteSector(u16 sector, const void *source);
extern u8 MegaShopHost_TrySavingData(u8 save_type);
extern void MegaShopHost_ReadFlash(u16 sector, u32 offset, void *destination,
                                   u32 size);
extern void MegaShopHost_Void(void);
extern u8 MegaShopHost_CreateTask(TaskFunc func, u8 priority);
extern void MegaShopHost_TaskId(u8 task_id);
extern u16 MegaShopHost_AddWindow(const struct WindowTemplate *template);
extern void MegaShopHost_WindowU8(u8 window_id);
extern void MegaShopHost_WindowPair(u8 window_id, u8 value);
extern void MegaShopHost_TextPrinter(u8 window_id, u8 font_id,
                                     const u8 *text, u8 x, u8 y, u8 speed,
                                     void *callback);
extern u8 MegaShopHost_MenuInitCursor(u8 window_id, u8 font_id, u8 left,
                                      u8 top, u8 cursor_height, u8 count,
                                      u8 cursor);
extern s8 MegaShopHost_MenuInput(void);
extern u16 MegaShopHost_GetBaseTile(void);
extern void MegaShopHost_PlaySe(u16 song);

#undef gVegaModernSaveData
#define gVegaModernSaveData (&gMegaShopHostModernSave)
#define G_MEGA_SHOP_STATE ((MegaShopVolatileState *)(void *)gMegaShopHostVolatileState)
#define G_SPECIAL_RESULT (&gMegaShopHostSpecialResult)
#define G_SPECIAL_VAR_8004 (&gMegaShopHostSpecialVar8004)
#define G_TASKS gMegaShopHostTasks
#define FN_FLAG_SET MegaShopHost_FlagSet
#define FN_FLAG_CLEAR MegaShopHost_FlagClear
#define FN_FLAG_GET MegaShopHost_FlagGet
#define FN_CHECK_BAG_HAS_ITEM MegaShopHost_CheckBagHasItem
#define FN_ADD_BAG_ITEM MegaShopHost_AddBagItem
#define FN_REMOVE_BAG_ITEM MegaShopHost_RemoveBagItem
#define FN_TRY_WRITE_SECTOR MegaShopHost_TryWriteSector
#define FN_TRY_SAVING_DATA MegaShopHost_TrySavingData
#define FN_READ_FLASH MegaShopHost_ReadFlash
#define FN_SCRIPT_CONTEXT2_ENABLE MegaShopHost_Void
#define FN_ENABLE_BOTH_SCRIPT_CONTEXTS MegaShopHost_Void
#define FN_CREATE_TASK MegaShopHost_CreateTask
#define FN_DESTROY_TASK MegaShopHost_TaskId
#define FN_ADD_WINDOW MegaShopHost_AddWindow
#define FN_REMOVE_WINDOW MegaShopHost_WindowU8
#define FN_COPY_WINDOW_TO_VRAM MegaShopHost_WindowPair
#define FN_PUT_WINDOW_TILEMAP MegaShopHost_WindowU8
#define FN_FILL_WINDOW_PIXEL_BUFFER MegaShopHost_WindowPair
#define FN_ADD_TEXT_PRINTER MegaShopHost_TextPrinter
#define FN_SCHEDULE_BG_COPY MegaShopHost_WindowU8
#define FN_DRAW_STD_WINDOW_FRAME MegaShopHost_WindowPair
#define FN_CLEAR_STD_WINDOW_FRAME MegaShopHost_WindowPair
#define FN_GET_STD_WINDOW_BASE_TILE MegaShopHost_GetBaseTile
#define FN_MENU_INIT_CURSOR MegaShopHost_MenuInitCursor
#define FN_MENU_PROCESS_INPUT MegaShopHost_MenuInput
#define FN_PLAY_SE MegaShopHost_PlaySe
#else
#define G_MEGA_SHOP_STATE PTR(MegaShopVolatileState *, 0x0203ED40u)
#define G_SPECIAL_RESULT PTR(volatile u16 *, 0x02037004u)
#define G_SPECIAL_VAR_8004 PTR(volatile u16 *, 0x02036FF4u)
#define G_TASKS PTR(struct Task *, 0x030050D0u)

#define FN_FLAG_SET PTR(FlagFn, 0x0806DE75u)
#define FN_FLAG_CLEAR PTR(FlagFn, 0x0806DE9Du)
#define FN_FLAG_GET PTR(FlagFn, 0x0806DEC5u)
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

#define MEGA_SHOP_SAVE_BUFFER PTR(u8 *, 0x020399B0u)
#define MEGA_SHOP_SECTOR31_IMAGE PTR(const u8 *, 0x0203CF9Cu)
#endif

#include "modernization_mega_shop_catalog_generated.h"

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
    G_MEGA_SHOP_STATE->last_result = result;
    *G_SPECIAL_RESULT = result;
}

static u8 persist_save_sector(void)
{
#ifdef MODERNIZATION_MEGA_SHOP_HOST_TEST
    return (u8)(FN_TRY_WRITE_SECTOR(MEGA_SHOP_SAVE_SECTOR,
                                    gVegaModernSaveData) == 1u);
#else
    clear_bytes(MEGA_SHOP_SAVE_BUFFER, MEGA_SHOP_SAVE_SECTOR_SIZE);
    copy_bytes(MEGA_SHOP_SAVE_BUFFER, MEGA_SHOP_SECTOR31_IMAGE,
               MEGA_SHOP_SAVE_SECTOR_DATA_SIZE);
    return (u8)(FN_TRY_WRITE_SECTOR(MEGA_SHOP_SAVE_SECTOR,
                                    MEGA_SHOP_SAVE_BUFFER) == 1u);
#endif
}

static u8 persist_standard_save(void)
{
    return (u8)(FN_TRY_SAVING_DATA(0u) == 1u);
}

static u8 restore_durable_ledger(void)
{
    VegaModernSaveData *candidate;
#ifdef MODERNIZATION_MEGA_SHOP_HOST_TEST
    FN_READ_FLASH(MEGA_SHOP_SAVE_SECTOR, 0u, &gMegaShopHostFlashRead,
                  sizeof(gMegaShopHostFlashRead));
    candidate = &gMegaShopHostFlashRead;
#else
    FN_READ_FLASH(MEGA_SHOP_SAVE_SECTOR, 0u, MEGA_SHOP_SAVE_BUFFER,
                  MEGA_SHOP_SAVE_SECTOR_SIZE);
    candidate = (VegaModernSaveData *)(void *)(
        MEGA_SHOP_SAVE_BUFFER
        + (VEGA_SAVE_EWRAM_ADDRESS
           - (u32)(uintptr_t)MEGA_SHOP_SECTOR31_IMAGE));
#endif
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
                        FN_FLAG_GET(MEGA_SHOP_FLAG_BADGE_1));
        if (!persist_standard_save() || !persist_save_sector())
            return 0u;
        return 1u;
    }
    return (u8)(status == VEGA_SAVE_OK);
}

static u8 index_valid(u16 catalog_index)
{
    return (u8)(catalog_index < MODERNIZATION_MEGA_SHOP_ENTRY_COUNT);
}

static u8 has_key_stone(void)
{
    return FN_CHECK_BAG_HAS_ITEM(MEGA_SHOP_KEY_STONE_ITEM, 1u);
}

static u8 claimed(u16 catalog_index)
{
    if (!index_valid(catalog_index))
        return 0u;
    return FN_FLAG_GET(gMegaShopCatalog[catalog_index].claim_flag);
}

static void compensate_purchase(const MegaShopCatalogEntry *entry, u16 old_bp)
{
    (void)FN_FLAG_CLEAR(entry->claim_flag);
    gVegaModernSaveData->factory.battle_points = old_bp;
    VegaSaveFinalize(gVegaModernSaveData);
    (void)FN_REMOVE_BAG_ITEM(entry->item_id, entry->quantity);
    (void)persist_standard_save();
    (void)persist_save_sector();
}

static u16 purchase_by_index(u16 catalog_index)
{
    const MegaShopCatalogEntry *entry;
    u16 old_bp;
    if (!index_valid(catalog_index))
        return MEGA_SHOP_RESULT_INVALID_SELECTION;
    if (!has_key_stone())
        return MEGA_SHOP_RESULT_LOCKED;
    if (claimed(catalog_index))
        return MEGA_SHOP_RESULT_ALREADY_CLAIMED;
    if (!ensure_save())
        return MEGA_SHOP_RESULT_PERSIST_FAILED;
    entry = &gMegaShopCatalog[catalog_index];
    if (gVegaModernSaveData->factory.battle_points < entry->price)
        return MEGA_SHOP_RESULT_INSUFFICIENT_BP;
    if (!FN_ADD_BAG_ITEM(entry->item_id, entry->quantity))
        return MEGA_SHOP_RESULT_BAG_FULL;

    old_bp = gVegaModernSaveData->factory.battle_points;
    if (VegaFactorySpendBattlePoints(gVegaModernSaveData, entry->price)
        != VEGA_SAVE_OK) {
        (void)FN_REMOVE_BAG_ITEM(entry->item_id, entry->quantity);
        return MEGA_SHOP_RESULT_INSUFFICIENT_BP;
    }
    (void)FN_FLAG_SET(entry->claim_flag);
    if (!persist_standard_save()) {
        compensate_purchase(entry, old_bp);
        return MEGA_SHOP_RESULT_PERSIST_FAILED;
    }
    if (!persist_save_sector()) {
        compensate_purchase(entry, old_bp);
        return MEGA_SHOP_RESULT_PERSIST_FAILED;
    }
    return MEGA_SHOP_RESULT_SUCCESS;
}

static void close_window(u8 task_id)
{
    u8 window_id = (u8)G_TASKS[task_id].data[0];
    if (window_id == MEGA_SHOP_WINDOW_INVALID)
        return;
    FN_CLEAR_STD_WINDOW_FRAME(window_id, 0u);
    FN_REMOVE_WINDOW(window_id);
    FN_SCHEDULE_BG_COPY(0u);
    G_TASKS[task_id].data[0] = MEGA_SHOP_WINDOW_INVALID;
    G_MEGA_SHOP_STATE->window_id = MEGA_SHOP_WINDOW_INVALID;
}

static u8 page_row_count(void)
{
    u8 first = (u8)(G_MEGA_SHOP_STATE->page * MEGA_SHOP_PAGE_SIZE);
    u8 remaining = first < G_MEGA_SHOP_STATE->eligible_count
        ? (u8)(G_MEGA_SHOP_STATE->eligible_count - first) : 0u;
    return remaining > MEGA_SHOP_PAGE_SIZE ? MEGA_SHOP_PAGE_SIZE : remaining;
}

static void append_balance_text(u16 balance)
{
    u8 *out = G_MEGA_SHOP_STATE->balance_text;
    u8 index = 0u;
    u16 divisor = 1000u;
    u8 started = 0u;
    while (gMegaShopBalancePrefix[index] != 0xFFu
           && index + 1u < sizeof(G_MEGA_SHOP_STATE->balance_text)) {
        out[index] = gMegaShopBalancePrefix[index];
        ++index;
    }
    while (divisor != 0u && index + 1u < sizeof(G_MEGA_SHOP_STATE->balance_text)) {
        u8 digit = (u8)(balance / divisor);
        if (digit != 0u || started || divisor == 1u) {
            out[index++] = gMegaShopDigitGlyphs[digit];
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
    u8 first = (u8)(G_MEGA_SHOP_STATE->page * MEGA_SHOP_PAGE_SIZE);
    u8 rows = page_row_count();
    u8 has_next = (u8)(first + rows < G_MEGA_SHOP_STATE->eligible_count);
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
    if (window_id == MEGA_SHOP_WINDOW_INVALID)
        return 0u;
    G_TASKS[task_id].data[0] = window_id;
    G_MEGA_SHOP_STATE->window_id = window_id;
    FN_FILL_WINDOW_PIXEL_BUFFER(window_id, 0x11u);
    FN_DRAW_STD_WINDOW_FRAME(window_id, 0u);
    FN_PUT_WINDOW_TILEMAP(window_id);

    append_balance_text(gVegaModernSaveData->factory.battle_points);
    FN_ADD_TEXT_PRINTER(window_id, 2u, G_MEGA_SHOP_STATE->balance_text,
                        8u, 1u, 0u, NULL);
    for (index = 0u; index < rows; ++index) {
        u16 catalog_index = G_MEGA_SHOP_STATE->eligible[first + index];
        FN_ADD_TEXT_PRINTER(window_id, 2u,
                            gMegaShopCatalog[catalog_index].row_text,
                            8u, (u8)(17u + index * 16u), 0u, NULL);
    }
    FN_ADD_TEXT_PRINTER(window_id, 2u,
                        has_next ? gMegaShopTextNext : gMegaShopTextCancel,
                        8u, (u8)(17u + rows * 16u), 0u, NULL);
    FN_MENU_INIT_CURSOR(window_id, 2u, 0u, 17u, 16u, menu_count, 0u);
    FN_COPY_WINDOW_TO_VRAM(window_id, MEGA_SHOP_COPYWIN_BOTH);
    FN_SCHEDULE_BG_COPY(0u);
    return 1u;
}

static void finish_menu(u8 task_id, u16 catalog_index, u16 result)
{
    close_window(task_id);
    FN_DESTROY_TASK(task_id);
    FN_PLAY_SE(MEGA_SHOP_SE_SELECT);
    G_MEGA_SHOP_STATE->last_catalog_index = catalog_index;
    set_result(result);
    FN_ENABLE_BOTH_SCRIPT_CONTEXTS();
}

static void Task_HandleMegaShopMenu(u8 task_id)
{
    s8 choice = FN_MENU_PROCESS_INPUT();
    u8 first;
    u8 rows;
    u8 has_next;
    u16 selected;
    if (choice == MEGA_SHOP_MENU_NOTHING)
        return;
    first = (u8)(G_MEGA_SHOP_STATE->page * MEGA_SHOP_PAGE_SIZE);
    rows = page_row_count();
    has_next = (u8)(first + rows < G_MEGA_SHOP_STATE->eligible_count);
    if (choice == MEGA_SHOP_MENU_B || choice < 0) {
        finish_menu(task_id, 0xFFFFu, MEGA_SHOP_RESULT_CANCELLED);
        return;
    }
    if ((u8)choice == rows) {
        if (has_next) {
            close_window(task_id);
            ++G_MEGA_SHOP_STATE->page;
            if (!render_menu(task_id))
                finish_menu(task_id, 0xFFFFu,
                            MEGA_SHOP_RESULT_ENGINE_REJECTED);
        } else {
            finish_menu(task_id, 0xFFFFu, MEGA_SHOP_RESULT_CANCELLED);
        }
        return;
    }
    if (choice < 0 || (u8)choice >= rows) {
        finish_menu(task_id, 0xFFFFu,
                    MEGA_SHOP_RESULT_INVALID_SELECTION);
        return;
    }
    selected = G_MEGA_SHOP_STATE->eligible[first + (u8)choice];
    finish_menu(task_id, selected, purchase_by_index(selected));
}

MEGA_SHOP_EXPORT(MegaShop_Probe)
u16 MegaShop_Probe(void)
{
    set_result(MODERNIZATION_MEGA_SHOP_ABI_VERSION);
    return MODERNIZATION_MEGA_SHOP_ABI_VERSION;
}

MEGA_SHOP_EXPORT(MegaShop_EnsureSave)
u16 MegaShop_EnsureSave(void)
{
    u16 result = ensure_save() ? 1u : 0u;
    set_result(result);
    return result;
}

MEGA_SHOP_EXPORT(MegaShop_GetBalance)
u16 MegaShop_GetBalance(void)
{
    u16 result = ensure_save()
        ? gVegaModernSaveData->factory.battle_points : 0u;
    *G_SPECIAL_RESULT = result;
    return result;
}

MEGA_SHOP_EXPORT(MegaShop_IsUnlocked)
u16 MegaShop_IsUnlocked(u16 catalog_index)
{
    u16 result = (ensure_save() && index_valid(catalog_index)
                  && has_key_stone() && !claimed(catalog_index)) ? 1u : 0u;
    *G_SPECIAL_RESULT = result;
    return result;
}

MEGA_SHOP_EXPORT(MegaShop_IsClaimed)
u16 MegaShop_IsClaimed(u16 catalog_index)
{
    u16 result = index_valid(catalog_index) ? claimed(catalog_index) : 0u;
    *G_SPECIAL_RESULT = result;
    return result;
}

MEGA_SHOP_EXPORT(MegaShop_PurchaseByIndex)
u16 MegaShop_PurchaseByIndex(u16 catalog_index)
{
    u16 result = purchase_by_index(catalog_index);
    G_MEGA_SHOP_STATE->last_catalog_index = catalog_index;
    set_result(result);
    return result;
}

MEGA_SHOP_EXPORT(MegaShop_PurchaseSelected)
u16 MegaShop_PurchaseSelected(void)
{
    return MegaShop_PurchaseByIndex(*G_SPECIAL_VAR_8004);
}

MEGA_SHOP_EXPORT(MegaShop_Open)
u16 MegaShop_Open(void)
{
    u16 index;
    u8 task_id;
    if (!has_key_stone()) {
        set_result(MEGA_SHOP_RESULT_LOCKED);
        return MEGA_SHOP_RESULT_LOCKED;
    }
    if (!ensure_save()) {
        set_result(MEGA_SHOP_RESULT_PERSIST_FAILED);
        return MEGA_SHOP_RESULT_PERSIST_FAILED;
    }
    clear_bytes(G_MEGA_SHOP_STATE, sizeof(*G_MEGA_SHOP_STATE));
    G_MEGA_SHOP_STATE->window_id = MEGA_SHOP_WINDOW_INVALID;
    G_MEGA_SHOP_STATE->last_result = MEGA_SHOP_RESULT_NOT_SET;
    G_MEGA_SHOP_STATE->last_catalog_index = 0xFFFFu;
    for (index = 0u; index < MODERNIZATION_MEGA_SHOP_ENTRY_COUNT; ++index) {
        if (!claimed(index))
            G_MEGA_SHOP_STATE->eligible[G_MEGA_SHOP_STATE->eligible_count++] = index;
    }
    if (G_MEGA_SHOP_STATE->eligible_count == 0u) {
        set_result(MEGA_SHOP_RESULT_ALL_CLAIMED);
        return MEGA_SHOP_RESULT_ALL_CLAIMED;
    }
    task_id = FN_CREATE_TASK(Task_HandleMegaShopMenu, 0x50u);
    if (task_id >= MEGA_SHOP_NUM_TASKS) {
        set_result(MEGA_SHOP_RESULT_ENGINE_REJECTED);
        return MEGA_SHOP_RESULT_ENGINE_REJECTED;
    }
    G_TASKS[task_id].data[0] = MEGA_SHOP_WINDOW_INVALID;
    if (!render_menu(task_id)) {
        FN_DESTROY_TASK(task_id);
        set_result(MEGA_SHOP_RESULT_ENGINE_REJECTED);
        return MEGA_SHOP_RESULT_ENGINE_REJECTED;
    }
    set_result(MEGA_SHOP_RESULT_BUSY);
    FN_SCRIPT_CONTEXT2_ENABLE();
    return MEGA_SHOP_RESULT_BUSY;
}

MEGA_SHOP_EXPORT(MegaShop_PostMenu)
void MegaShop_PostMenu(void)
{
    u16 result = G_MEGA_SHOP_STATE->last_result;
    if (result == MEGA_SHOP_RESULT_NOT_SET)
        result = MEGA_SHOP_RESULT_CANCELLED;
    *G_SPECIAL_RESULT = result;
}
