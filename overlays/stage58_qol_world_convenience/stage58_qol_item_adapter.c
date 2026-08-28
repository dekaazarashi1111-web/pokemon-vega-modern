#include <stdint.h>

/*
 * Stage58 Bottle Cap normal-Bag adapter.
 *
 * This translation unit intentionally owns no mutable RAM or save state.
 * The stock party menu owns the selected slot, and the party task's data[]
 * owns the short-lived ListMenu handles and return callback.  The production
 * QOL service remains the sole mutation/consumption owner.
 */

typedef uint8_t u8;
typedef int16_t s16;
typedef uint16_t u16;
typedef int32_t s32;
typedef uint32_t u32;

typedef void (*TaskFunc)(u8 task_id);
typedef void (*VoidFn)(void);
typedef void (*ItemUseCallbackFn)(u8 task_id, TaskFunc return_task);
typedef void (*SetMainCallbackFn)(VoidFn callback);

typedef struct Task {
    TaskFunc func;
    u8 is_active;
    u8 prev;
    u8 next;
    u8 priority;
    s16 data[16];
} Task;

typedef struct WindowTemplate {
    u8 bg;
    u8 tilemap_left;
    u8 tilemap_top;
    u8 width;
    u8 height;
    u8 palette_num;
    u16 base_block;
} WindowTemplate;

typedef struct ListMenuItem {
    const u8 *name;
    s32 id;
} ListMenuItem;

typedef struct ListMenuTemplate {
    const ListMenuItem *items;
    void (*move_cursor)(s32 item_index, u8 on_init, void *list);
    void (*print_item)(u8 window_id, s32 item_id, u8 y);
    u16 total_items;
    u16 max_showed;
    u8 window_id;
    u8 header_x;
    u8 item_x;
    u8 cursor_x;
    u8 up_text_y : 4;
    u8 cursor_pal : 4;
    u8 fill_value : 4;
    u8 cursor_shadow_pal : 4;
    u8 letter_spacing : 3;
    u8 vertical_padding : 3;
    u8 scroll_multiple : 2;
    u8 font_id : 6;
    u8 cursor_kind : 2;
} ListMenuTemplate;

typedef void (*SetUpItemUseCallbackFn)(u8 task_id);
typedef u8 (*DisplayPartyMessageFn)(const u8 *text, u8 keep_open);
typedef u8 (*ListMenuInitFn)(const ListMenuTemplate *template_,
                             u16 cursor, u16 items_above);
typedef s32 (*ListMenuInputFn)(u8 list_task_id);
typedef void (*ListMenuDestroyFn)(u8 list_task_id, u16 *cursor,
                                  u16 *items_above);
typedef u16 (*AddWindowFn)(const WindowTemplate *template_);
typedef void (*WindowU8Fn)(u8 window_id);
typedef void (*WindowPairFn)(u8 window_id, u8 copy_to_vram);
typedef void (*FillWindowFn)(u8 window_id, u8 fill_value);
typedef void (*CopyWindowToVramFn)(u8 window_id, u8 mode);
typedef u32 (*QolDispatchFn)(u16 service, u32 a, u32 b, u32 c);

#define PTR(type, address) ((type)(uintptr_t)(address))
#define PUBLIC_TEXT(name) \
    __attribute__((section(".text." #name), used, noinline))

enum {
    STAGE58_QOL_ITEM_ADAPTER_MAGIC = 0x53384350u, /* "S8CP" */
    STAGE58_QOL_ITEM_ADAPTER_VERSION = 1u,
    ITEM_BOTTLE_CAP = 853u,
    ITEM_GOLD_BOTTLE_CAP = 854u,
    QOL_SERVICE_HYPER_TRAIN_PARTY = 17u,
    QOL_STATUS_OK = 0u,
    HYPER_TRAIN_ALL_STATS = 6u,
    HYPER_TRAIN_STAT_COUNT = 6u,
    LIST_NOTHING_CHOSEN = -1,
    LIST_CANCEL = -2,
    WINDOW_INVALID = 0xFFu,
    TASK_MENU_HANDLES = 10u,
    TASK_RETURN_CALLBACK_LO = 14u,
    TASK_RETURN_CALLBACK_HI = 15u,
    PARTY_DYNAMIC_WINDOW_BASE_BLOCK = 0x2BFu,
    CODEX_RUNTIME_MAGIC = 0x32524243u,
    CODEX_RUNTIME_ACTIVE_OFFSET = 20u,
    CODEX_RUNTIME_CODEX_SELECTION_VALID_OFFSET = 26u,
    CODEX_RUNTIME_PLAYER_SELECTION_VALID_OFFSET = 27u,
    CODEX_RUNTIME_FIELD_COMPLETION_PENDING_OFFSET = 30u,
    CODEX_RUNTIME_CLEANUP_REASON_OFFSET = 82u,
    CODEX_TRAINER_ID = 745u,
    BATTLE_TYPE_TRAINER = 0x00000008u,
    BATTLE_TYPE_TRAINER_TOWER = 0x00080000u,
    VEGA_DEX_BITMAP_SIZE = 52u,
    VEGA_SAVE1_DEX_SEEN_PRIMARY_OFFSET = 0x05F8u,
    VEGA_SAVE1_DEX_SEEN_SECONDARY_OFFSET = 0x3A18u,
    VEGA_SAVE2_DEX_OWNED_OFFSET = 0x0028u,
    VEGA_SAVE2_DEX_SEEN_OFFSET = 0x005Cu,
    VEGA_SAVE2_DEX_HEADER_OFFSET = 0x0018u,
    VEGA_SAVE2_DEX_HEADER_SIZE = 16u,
    VEGA_SAVE2_DEX_PERSONALITIES_OFFSET = 0x001Cu,
    VEGA_SAVE2_DEX_PERSONALITIES_SIZE = 8u,
    CODEX_SAVE1_SEEN_SNAPSHOT_OFFSET = 0x03A6u,
    CODEX_SAVE1_SEEN_SNAPSHOT_SIZE = 150u,
    CODEX_SAVE2_SEEN_SNAPSHOT_OFFSET = 0x053Cu,
    CODEX_SAVE2_SEEN_SNAPSHOT_SIZE = 16u,
};

enum {
    TASKS_ADDRESS = 0x030050D0u,
    ITEM_USE_CALLBACK_ADDRESS = 0x03005EE8u,
    SPECIAL_VAR_ITEM_ADDRESS = 0x0203ACA8u,
    PARTY_MENU_ADDRESS = 0x0203B014u,
    PARTY_MENU_SLOT_OFFSET = 9u,
    PARTY_MENU_USE_EXIT_ADDRESS = 0x0203B034u,
    CODEX_RUNTIME_STATE_ADDRESS = 0x0203FA00u,
    TRAINER_OPPONENT_A_ADDRESS = 0x020385E2u,
    BATTLE_TYPE_FLAGS_ADDRESS = 0x02022AACu,
    BATTLE_SCRIPT_POINTER_ADDRESS = 0x02023CD4u,
    MAIN_SAVED_CALLBACK_ADDRESS = 0x03003138u,
    BATTLE_OUTCOME_ADDRESS = 0x02023DEAu,
    SAVE_BLOCK1_POINTER_ADDRESS = 0x03005048u,
    SAVE_BLOCK2_POINTER_ADDRESS = 0x0300504Cu,
};

#define G_TASKS PTR(volatile Task *, TASKS_ADDRESS)
#define G_ITEM_USE_CALLBACK \
    (*(ItemUseCallbackFn *)(uintptr_t)ITEM_USE_CALLBACK_ADDRESS)
#define G_SPECIAL_ITEM \
    (*(volatile u16 *)(uintptr_t)SPECIAL_VAR_ITEM_ADDRESS)
#define G_PARTY_SLOT \
    (*(volatile int8_t *)(uintptr_t)(PARTY_MENU_ADDRESS \
                                     + PARTY_MENU_SLOT_OFFSET))
#define G_PARTY_USE_EXIT \
    (*(volatile u8 *)(uintptr_t)PARTY_MENU_USE_EXIT_ADDRESS)
#define G_TRAINER_OPPONENT_A \
    (*(volatile u16 *)(uintptr_t)TRAINER_OPPONENT_A_ADDRESS)
#define G_BATTLE_OUTCOME \
    (*(volatile u8 *)(uintptr_t)BATTLE_OUTCOME_ADDRESS)

#define FN_SET_UP_ITEM_USE_CALLBACK \
    PTR(SetUpItemUseCallbackFn, 0x080A29A5u)
#define FN_DISPLAY_PARTY_MESSAGE \
    PTR(DisplayPartyMessageFn, 0x08120AE9u)
#define FN_LIST_MENU_INIT PTR(ListMenuInitFn, 0x08107AFDu)
#define FN_LIST_MENU_INPUT PTR(ListMenuInputFn, 0x08107B7Du)
#define FN_LIST_MENU_DESTROY PTR(ListMenuDestroyFn, 0x08107C41u)
#define FN_ADD_WINDOW PTR(AddWindowFn, 0x08003CB1u)
#define FN_REMOVE_WINDOW PTR(WindowU8Fn, 0x08003E09u)
#define FN_PUT_WINDOW_TILEMAP PTR(WindowU8Fn, 0x08003F6Du)
#define FN_FILL_WINDOW PTR(FillWindowFn, 0x08004429u)
#define FN_COPY_WINDOW_TO_VRAM PTR(CopyWindowToVramFn, 0x08003EEDu)
#define FN_SCHEDULE_BG_COPY PTR(WindowU8Fn, 0x080F77FDu)
#define FN_DRAW_STD_WINDOW_FRAME PTR(WindowPairFn, 0x080F7F7Du)
#define FN_CLEAR_STD_WINDOW_FRAME PTR(WindowPairFn, 0x080F7FFDu)
#define FN_LOAD_STD_WINDOW_FRAME_GFX PTR(VoidFn, 0x080F7EFDu)
#define FN_QOL_DISPATCH PTR(QolDispatchFn, 0x09378799u)
#define FN_STOCK_BATTLE_WON PTR(VoidFn, 0x08014E91u)
#define FN_STOCK_BATTLE_LOST PTR(VoidFn, 0x08014FA5u)
#define FN_INHERITED_BATTLE_WON PTR(VoidFn, 0x093D203Du)
#define FN_INHERITED_BATTLE_LOST PTR(VoidFn, 0x093D2059u)
#define FN_SET_MAIN_CALLBACK2 PTR(SetMainCallbackFn, 0x08000545u)
#define FN_RETURN_TO_FIELD PTR(VoidFn, 0x080561A1u)
#define FN_INHERITED_RETURN_TO_FIELD PTR(VoidFn, 0x093D1E01u)
/* Stock Pickup + end2 tail.  It has no result text, money award or whiteout. */
#define CODEX_NONPUNITIVE_RESULT_SCRIPT 0x081BC8BBu

_Static_assert(sizeof(Task) == 40u, "Vega task ABI differs");
_Static_assert(sizeof(WindowTemplate) == 8u, "Vega window ABI differs");
_Static_assert(sizeof(ListMenuTemplate) == 24u,
               "Vega ListMenu ABI differs");
_Static_assert(3u * VEGA_DEX_BITMAP_SIZE
               + VEGA_SAVE2_DEX_PERSONALITIES_SIZE
               <= CODEX_SAVE1_SEEN_SNAPSHOT_SIZE
                  + CODEX_SAVE2_SEEN_SNAPSHOT_SIZE,
               "Codex existing snapshot buffers are too small");

/* Exact copies of generated/runtime/qol_production_generated.h labels.
 * Display order is HP/Atk/Def/SpAtk/SpDef/Speed.  Service stat ids retain
 * the Pokemon substructure order HP/Atk/Def/Speed/SpAtk/SpDef. */
static const u8 kBottleCapStatLabels[HYPER_TRAIN_STAT_COUNT][12] = {
    {0xC2, 0xCA, 0xFF, 0x00, 0x00, 0x00,
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00},
    {0x0A, 0x03, 0x3A, 0x07, 0xFF, 0x00,
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00},
    {0x4A, 0x03, 0x38, 0x36, 0xFF, 0x00,
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00},
    {0x14, 0x08, 0x0A, 0x03, 0xFF, 0x00,
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00},
    {0x14, 0x08, 0x4A, 0x03, 0xFF, 0x00,
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00},
    {0x0D, 0x46, 0x24, 0x0B, 0xFF, 0x00,
     0x00, 0x00, 0x00, 0x00, 0x00, 0x00},
};

/* generated gVegaQolSupplyCancel ("やめる") */
static const u8 kBottleCapCancelLabel[] = {0x24, 0x22, 0x29, 0xFF};

static const ListMenuItem kBottleCapStatItems[7] = {
    {kBottleCapStatLabels[0], 0},
    {kBottleCapStatLabels[1], 1},
    {kBottleCapStatLabels[2], 2},
    {kBottleCapStatLabels[3], 4},
    {kBottleCapStatLabels[4], 5},
    {kBottleCapStatLabels[5], 3},
    {kBottleCapCancelLabel, LIST_CANCEL},
};

/* Existing QOL-generated game strings. */
static const u8 kBottleCapAppliedMessage[] = {
    0x45, 0x03, 0x39, 0x2D, 0x00, 0x12, 0x06, 0x50, 0x10,
    0xAB, 0x00, 0xBB, 0x44, 0x12, 0x43, 0x09, 0x29, 0xFF,
};
static const u8 kBottleCapNoEffectMessage[] = {
    0x0A, 0x03, 0x06, 0x37, 0x00, 0x15, 0x02, 0x26, 0x03, 0x41, 0xFF,
};

static void clear_bytes(void *destination, u32 size)
{
    u8 *out = (u8 *)destination;
    while (size-- != 0u)
        *out++ = 0u;
}

static void task_store_pointer(u8 task_id, u8 index, TaskFunc value)
{
    u32 raw = (u32)(uintptr_t)value;
    G_TASKS[task_id].data[index] = (s16)(raw & 0xFFFFu);
    G_TASKS[task_id].data[index + 1u] = (s16)(raw >> 16);
}

static TaskFunc task_load_pointer(u8 task_id, u8 index)
{
    u32 raw = (u16)G_TASKS[task_id].data[index];
    raw |= (u32)(u16)G_TASKS[task_id].data[index + 1u] << 16;
    return (TaskFunc)(uintptr_t)raw;
}

static void show_result_and_return(u8 task_id, TaskFunc return_task,
                                   u32 status)
{
    u8 success = (u8)(status == QOL_STATUS_OK);
    G_PARTY_USE_EXIT = success;
    (void)FN_DISPLAY_PARTY_MESSAGE(success ? kBottleCapAppliedMessage
                                           : kBottleCapNoEffectMessage,
                                   1u);
    FN_SCHEDULE_BG_COPY(2u);
    G_TASKS[task_id].func = return_task;
}

static u8 open_bottle_cap_stat_menu(u8 task_id)
{
    WindowTemplate window;
    ListMenuTemplate menu;
    u8 window_id;
    u8 list_task_id;

    clear_bytes(&window, sizeof(window));
    clear_bytes(&menu, sizeof(menu));
    window.bg = 0u;
    window.tilemap_left = 16u;
    window.tilemap_top = 1u;
    window.width = 13u;
    window.height = 16u;
    window.palette_num = 15u;
    /* The party screen's stock dynamic windows are inactive while this list
     * owns BG0.  Keep its 208 content tiles at 0x2BF..0x38E, disjoint from
     * the standard dialogue/user-frame graphics at 0x200..0x21C and below
     * the 0x400-tile character-base limit. */
    window.base_block = PARTY_DYNAMIC_WINDOW_BASE_BLOCK;
    window_id = (u8)FN_ADD_WINDOW(&window);
    if (window_id == WINDOW_INVALID)
        return 0u;

    FN_LOAD_STD_WINDOW_FRAME_GFX();
    FN_FILL_WINDOW(window_id, 0x11u);
    FN_DRAW_STD_WINDOW_FRAME(window_id, 0u);
    FN_PUT_WINDOW_TILEMAP(window_id);
    menu.items = kBottleCapStatItems;
    menu.total_items = 7u;
    menu.max_showed = 7u;
    menu.window_id = window_id;
    menu.item_x = 9u;
    menu.cursor_x = 1u;
    menu.cursor_pal = 2u;
    menu.fill_value = 1u;
    menu.cursor_shadow_pal = 3u;
    menu.font_id = 2u;
    list_task_id = FN_LIST_MENU_INIT(&menu, 0u, 0u);
    if (list_task_id == WINDOW_INVALID) {
        FN_CLEAR_STD_WINDOW_FRAME(window_id, 0u);
        FN_REMOVE_WINDOW(window_id);
        FN_SCHEDULE_BG_COPY(0u);
        return 0u;
    }

    G_TASKS[task_id].data[TASK_MENU_HANDLES] =
        (s16)((u16)window_id | ((u16)list_task_id << 8));
    FN_COPY_WINDOW_TO_VRAM(window_id, 3u);
    FN_SCHEDULE_BG_COPY(0u);
    return 1u;
}

static void close_bottle_cap_stat_menu(u8 task_id)
{
    u16 packed = (u16)G_TASKS[task_id].data[TASK_MENU_HANDLES];
    u8 window_id = (u8)packed;
    u8 list_task_id = (u8)(packed >> 8);
    u16 cursor = 0u;
    u16 items_above = 0u;

    FN_LIST_MENU_DESTROY(list_task_id, &cursor, &items_above);
    FN_CLEAR_STD_WINDOW_FRAME(window_id, 0u);
    FN_REMOVE_WINDOW(window_id);
    FN_SCHEDULE_BG_COPY(0u);
    G_TASKS[task_id].data[TASK_MENU_HANDLES] = (s16)0xFFFFu;
}

static void bottle_cap_stat_menu_task(u8 task_id)
{
    u16 packed = (u16)G_TASKS[task_id].data[TASK_MENU_HANDLES];
    s32 choice = FN_LIST_MENU_INPUT((u8)(packed >> 8));
    TaskFunc return_task;
    u32 status;

    if (choice == LIST_NOTHING_CHOSEN)
        return;
    close_bottle_cap_stat_menu(task_id);
    return_task = task_load_pointer(task_id, TASK_RETURN_CALLBACK_LO);
    if (choice == LIST_CANCEL) {
        G_PARTY_USE_EXIT = 0u;
        G_TASKS[task_id].func = return_task;
        return;
    }
    if (choice < 0 || choice >= HYPER_TRAIN_STAT_COUNT) {
        show_result_and_return(task_id, return_task, 0xFFFFFFFFu);
        return;
    }

    status = FN_QOL_DISPATCH(QOL_SERVICE_HYPER_TRAIN_PARTY,
                             (u32)(u8)G_PARTY_SLOT, (u32)choice, 0u);
    show_result_and_return(task_id, return_task, status);
}

static void bottle_cap_party_callback(u8 task_id, TaskFunc return_task)
{
    u16 item = G_SPECIAL_ITEM;
    u32 status;

    if (item == ITEM_GOLD_BOTTLE_CAP) {
        status = FN_QOL_DISPATCH(QOL_SERVICE_HYPER_TRAIN_PARTY,
                                 (u32)(u8)G_PARTY_SLOT,
                                 HYPER_TRAIN_ALL_STATS, 0u);
        show_result_and_return(task_id, return_task, status);
        return;
    }
    if (item != ITEM_BOTTLE_CAP) {
        show_result_and_return(task_id, return_task, 0xFFFFFFFFu);
        return;
    }

    task_store_pointer(task_id, TASK_RETURN_CALLBACK_LO, return_task);
    G_TASKS[task_id].data[TASK_MENU_HANDLES] = (s16)0xFFFFu;
    if (open_bottle_cap_stat_menu(task_id)) {
        G_TASKS[task_id].func = bottle_cap_stat_menu_task;
        return;
    }
    show_result_and_return(task_id, return_task, 0xFFFFFFFFu);
}

PUBLIC_TEXT(Stage58QolItemAdapter_Probe)
u32 Stage58QolItemAdapter_Probe(u32 selector)
{
    switch (selector) {
    case 0u: return STAGE58_QOL_ITEM_ADAPTER_MAGIC;
    case 1u: return STAGE58_QOL_ITEM_ADAPTER_VERSION;
    case 2u: return ITEM_BOTTLE_CAP;
    case 3u: return ITEM_GOLD_BOTTLE_CAP;
    case 4u: return QOL_SERVICE_HYPER_TRAIN_PARTY;
    case 5u: return HYPER_TRAIN_STAT_COUNT;
    default: return 0u;
    }
}

PUBLIC_TEXT(Stage58QolItemAdapter_FieldUseBottleCapAdapter)
void Stage58QolItemAdapter_FieldUseBottleCapAdapter(u8 task_id)
{
    /* Function-pointer assignment preserves the Thumb bit at final link. */
    G_ITEM_USE_CALLBACK = bottle_cap_party_callback;
    FN_SET_UP_ITEM_USE_CALLBACK(task_id);
}

PUBLIC_TEXT(Stage58QolItemAdapter_CodexTransactionIdentityValid)
u8 Stage58QolItemAdapter_CodexTransactionIdentityValid(void)
{
    volatile u8 *state = PTR(volatile u8 *, CODEX_RUNTIME_STATE_ADDRESS);
    u32 magic = *(volatile u32 *)(void *)state;
    u32 inverse = *(volatile u32 *)(void *)(state + 4u);
    return (u8)(magic == CODEX_RUNTIME_MAGIC
        && inverse == ~(u32)CODEX_RUNTIME_MAGIC
        && state[CODEX_RUNTIME_ACTIVE_OFFSET] != 0u);
}

PUBLIC_TEXT(Stage58QolItemAdapter_CodexResultStateValid)
u8 Stage58QolItemAdapter_CodexResultStateValid(void)
{
    volatile u8 *state = PTR(volatile u8 *, CODEX_RUNTIME_STATE_ADDRESS);
    return (u8)(Stage58QolItemAdapter_CodexTransactionIdentityValid()
        && state[CODEX_RUNTIME_CODEX_SELECTION_VALID_OFFSET] != 0u
        && state[CODEX_RUNTIME_PLAYER_SELECTION_VALID_OFFSET] != 0u
        && *(volatile u16 *)(void *)(
            state + CODEX_RUNTIME_FIELD_COMPLETION_PENDING_OFFSET) == 1u);
}

PUBLIC_TEXT(Stage58QolItemAdapter_CodexBattleResultOwned)
u8 Stage58QolItemAdapter_CodexBattleResultOwned(void)
{
    volatile u32 *flags = PTR(volatile u32 *, BATTLE_TYPE_FLAGS_ADDRESS);
    return (u8)(Stage58QolItemAdapter_CodexResultStateValid()
        && (*flags & BATTLE_TYPE_TRAINER) != 0u
        && G_TRAINER_OPPONENT_A == CODEX_TRAINER_ID);
}

PUBLIC_TEXT(Stage58QolItemAdapter_CodexLegacyResultHazard)
u8 Stage58QolItemAdapter_CodexLegacyResultHazard(void)
{
    volatile u8 *state = PTR(volatile u8 *, CODEX_RUNTIME_STATE_ADDRESS);
    volatile u32 *flags = PTR(volatile u32 *, BATTLE_TYPE_FLAGS_ADDRESS);

    /* Stage47's inherited adapter arms Trainer Tower when its controller flag
     * is still set.  Treat the same predicate without that volatile flag as a
     * conservative superset: a partially damaged Codex transaction must not
     * be delegated into the unsafe Tower-name path. */
    return (u8)(Stage58QolItemAdapter_CodexTransactionIdentityValid()
        && state[CODEX_RUNTIME_PLAYER_SELECTION_VALID_OFFSET] != 0u
        && (*flags & BATTLE_TYPE_TRAINER) != 0u);
}

PUBLIC_TEXT(Stage58QolItemAdapter_CodexRewardResultKind)
u8 Stage58QolItemAdapter_CodexRewardResultKind(void)
{
    volatile u8 *state = PTR(volatile u8 *, CODEX_RUNTIME_STATE_ADDRESS);
    u16 cleanup = *(volatile u16 *)(void *)(
        state + CODEX_RUNTIME_CLEANUP_REASON_OFFSET);
    u8 outcome = (u8)(G_BATTLE_OUTCOME & 0x7Fu);

    /* Public Windows/CLI ABI: 1=WIN, 2=LOSS, 3=DRAW, 4=FORFEIT.
     * Stage47 accidentally mapped engine draw outcome 5 to FORFEIT and the
     * runtime's cleanup reason 3 to DRAW.  This function is called inside the
     * inherited reward opener after runtime restoration but before its CRC
     * finalization and sector-31 persistence, so both RAM and durable owner
     * receive the corrected taxonomy atomically. */
    if (cleanup == 3u)
        return 4u;
    if (outcome == 5u)
        return 3u;
    if (cleanup == 1u || cleanup == 2u)
        return (u8)cleanup;
    return 0u;
}

void Stage58QolItemAdapter_CodexReturnToFieldAdapter(void);

PUBLIC_TEXT(Stage58QolItemAdapter_FinishNonpunitiveCodexResult)
void Stage58QolItemAdapter_FinishNonpunitiveCodexResult(VoidFn stock_handler)
{
    volatile u32 *flags = PTR(volatile u32 *, BATTLE_TYPE_FLAGS_ADDRESS);
    volatile u32 *script = PTR(volatile u32 *, BATTLE_SCRIPT_POINTER_ADDRESS);
    volatile u32 *saved_callback =
        PTR(volatile u32 *, MAIN_SAVED_CALLBACK_ADDRESS);

    /* Stage45 used the Trainer Tower bit to suppress prize money/whiteout,
     * but BattleStringExpandPlaceholders observes that bit first and reads
     * the uninitialized Trainer Tower name owner.  The resulting unterminated
     * copy overruns gDisplayedStringBattle into battle allocation pointers.
     * Keep this battle an ordinary trainer battle, route field return through
     * the reward owner, and replace only its result script with the stock
     * no-money/no-whiteout Pickup+end2 tail. */
    *flags &= ~BATTLE_TYPE_TRAINER_TOWER;
    *saved_callback = ((u32)(uintptr_t)
        Stage58QolItemAdapter_CodexReturnToFieldAdapter) | 1u;
    stock_handler();
    *script = CODEX_NONPUNITIVE_RESULT_SCRIPT;
}

PUBLIC_TEXT(Stage58QolItemAdapter_CodexReturnToFieldAdapter)
void Stage58QolItemAdapter_CodexReturnToFieldAdapter(void)
{
    /* DISCONNECT_CPU deliberately clears controller_installed before the
     * result.  The durable field transaction remains identified by both
     * selected teams plus field_completion_pending until the resumed
     * trainerbattle script calls AfterBattle and eventually FieldFinish. */
    if (Stage58QolItemAdapter_CodexTransactionIdentityValid())
        FN_SET_MAIN_CALLBACK2(FN_RETURN_TO_FIELD);
    else
        FN_INHERITED_RETURN_TO_FIELD();
}

PUBLIC_TEXT(Stage58QolItemAdapter_CodexBattleWonAdapter)
void Stage58QolItemAdapter_CodexBattleWonAdapter(void)
{
    if (Stage58QolItemAdapter_CodexBattleResultOwned())
        Stage58QolItemAdapter_FinishNonpunitiveCodexResult(
            FN_STOCK_BATTLE_WON);
    else if (Stage58QolItemAdapter_CodexLegacyResultHazard())
        FN_STOCK_BATTLE_WON();
    else
        FN_INHERITED_BATTLE_WON();
}

PUBLIC_TEXT(Stage58QolItemAdapter_CodexBattleLostAdapter)
void Stage58QolItemAdapter_CodexBattleLostAdapter(void)
{
    if (Stage58QolItemAdapter_CodexBattleResultOwned())
        Stage58QolItemAdapter_FinishNonpunitiveCodexResult(
            FN_STOCK_BATTLE_LOST);
    else if (Stage58QolItemAdapter_CodexLegacyResultHazard())
        FN_STOCK_BATTLE_LOST();
    else
        FN_INHERITED_BATTLE_LOST();
}

PUBLIC_TEXT(Stage58QolItemAdapter_CodexSnapshotSeenMirrors)
void Stage58QolItemAdapter_CodexSnapshotSeenMirrors(
    const volatile u8 *save1)
{
    const volatile u8 *save2 =
        *PTR(const volatile u8 * volatile *, SAVE_BLOCK2_POINTER_ADDRESS);
    volatile u8 *primary = PTR(
        volatile u8 *, CODEX_RUNTIME_STATE_ADDRESS
        + CODEX_SAVE1_SEEN_SNAPSHOT_OFFSET);
    volatile u8 *spill = PTR(
        volatile u8 *, CODEX_RUNTIME_STATE_ADDRESS
        + CODEX_SAVE2_SEEN_SNAPSHOT_OFFSET);
    u32 index;

    if (save1 == (const volatile u8 *)0
        || save2 == (const volatile u8 *)0)
        return;
    for (index = 0u; index < VEGA_DEX_BITMAP_SIZE; ++index)
        primary[index] =
            save1[VEGA_SAVE1_DEX_SEEN_PRIMARY_OFFSET + index];
    for (index = 0u; index < VEGA_DEX_BITMAP_SIZE; ++index)
        primary[VEGA_DEX_BITMAP_SIZE + index] =
            save1[VEGA_SAVE1_DEX_SEEN_SECONDARY_OFFSET + index];
    for (index = 0u;
         index < CODEX_SAVE1_SEEN_SNAPSHOT_SIZE
            - 2u * VEGA_DEX_BITMAP_SIZE;
         ++index)
        primary[2u * VEGA_DEX_BITMAP_SIZE + index] =
            save2[VEGA_SAVE2_DEX_SEEN_OFFSET + index];
    for (index = 0u;
         index < VEGA_DEX_BITMAP_SIZE
            - (CODEX_SAVE1_SEEN_SNAPSHOT_SIZE
               - 2u * VEGA_DEX_BITMAP_SIZE);
         ++index)
        spill[index] = save2[
            VEGA_SAVE2_DEX_SEEN_OFFSET
            + CODEX_SAVE1_SEEN_SNAPSHOT_SIZE
            - 2u * VEGA_DEX_BITMAP_SIZE + index];
    for (index = 0u; index < VEGA_SAVE2_DEX_PERSONALITIES_SIZE; ++index)
        spill[VEGA_DEX_BITMAP_SIZE
              - (CODEX_SAVE1_SEEN_SNAPSHOT_SIZE
                 - 2u * VEGA_DEX_BITMAP_SIZE) + index] =
            save2[VEGA_SAVE2_DEX_PERSONALITIES_OFFSET + index];
}

PUBLIC_TEXT(Stage58QolItemAdapter_CodexRestoreSeenMirrors)
void Stage58QolItemAdapter_CodexRestoreSeenMirrors(volatile u8 *save1)
{
    volatile u8 *save2 =
        *PTR(volatile u8 * volatile *, SAVE_BLOCK2_POINTER_ADDRESS);
    const volatile u8 *primary = PTR(
        const volatile u8 *, CODEX_RUNTIME_STATE_ADDRESS
        + CODEX_SAVE1_SEEN_SNAPSHOT_OFFSET);
    const volatile u8 *spill = PTR(
        const volatile u8 *, CODEX_RUNTIME_STATE_ADDRESS
        + CODEX_SAVE2_SEEN_SNAPSHOT_OFFSET);
    u32 index;

    if (save1 == (volatile u8 *)0 || save2 == (volatile u8 *)0)
        return;
    for (index = 0u; index < VEGA_DEX_BITMAP_SIZE; ++index)
        save1[VEGA_SAVE1_DEX_SEEN_PRIMARY_OFFSET + index] = primary[index];
    for (index = 0u; index < VEGA_DEX_BITMAP_SIZE; ++index)
        save1[VEGA_SAVE1_DEX_SEEN_SECONDARY_OFFSET + index] =
            primary[VEGA_DEX_BITMAP_SIZE + index];
    for (index = 0u;
         index < CODEX_SAVE1_SEEN_SNAPSHOT_SIZE
            - 2u * VEGA_DEX_BITMAP_SIZE;
         ++index)
        save2[VEGA_SAVE2_DEX_SEEN_OFFSET + index] =
            primary[2u * VEGA_DEX_BITMAP_SIZE + index];
    for (index = 0u;
         index < VEGA_DEX_BITMAP_SIZE
            - (CODEX_SAVE1_SEEN_SNAPSHOT_SIZE
               - 2u * VEGA_DEX_BITMAP_SIZE);
         ++index)
        save2[VEGA_SAVE2_DEX_SEEN_OFFSET
              + CODEX_SAVE1_SEEN_SNAPSHOT_SIZE
              - 2u * VEGA_DEX_BITMAP_SIZE + index] = spill[index];
    for (index = 0u; index < VEGA_SAVE2_DEX_PERSONALITIES_SIZE; ++index)
        save2[VEGA_SAVE2_DEX_PERSONALITIES_OFFSET + index] =
            spill[VEGA_DEX_BITMAP_SIZE
                  - (CODEX_SAVE1_SEEN_SNAPSHOT_SIZE
                     - 2u * VEGA_DEX_BITMAP_SIZE) + index];
}

PUBLIC_TEXT(Stage58QolItemAdapter_CodexContinueSeenHash)
u32 Stage58QolItemAdapter_CodexContinueSeenHash(u32 value)
{
    const volatile u8 *save1 =
        *PTR(const volatile u8 * volatile *, SAVE_BLOCK1_POINTER_ADDRESS);
    const volatile u8 *save2 =
        *PTR(const volatile u8 * volatile *, SAVE_BLOCK2_POINTER_ADDRESS);
    const volatile u8 *sources[4];
    u32 source;
    u32 index;

    if (save1 == (const volatile u8 *)0
        || save2 == (const volatile u8 *)0)
        return 0u;
    sources[0] = save1 + VEGA_SAVE1_DEX_SEEN_PRIMARY_OFFSET;
    sources[1] = save1 + VEGA_SAVE1_DEX_SEEN_SECONDARY_OFFSET;
    sources[2] = save2 + VEGA_SAVE2_DEX_OWNED_OFFSET;
    sources[3] = save2 + VEGA_SAVE2_DEX_SEEN_OFFSET;
    for (source = 0u; source < 4u; ++source) {
        for (index = 0u; index < VEGA_DEX_BITMAP_SIZE; ++index) {
            value ^= sources[source][index];
            value *= 16777619u;
        }
    }
    for (index = 0u; index < VEGA_SAVE2_DEX_HEADER_SIZE; ++index) {
        value ^= save2[VEGA_SAVE2_DEX_HEADER_OFFSET + index];
        value *= 16777619u;
    }
    return value;
}
