/*
 * USER-20260814-MOVE-MEMORY
 *
 * stage 24の固定CFRU-JP ABIへ、item/NPC共通の技管理coreを接続する。
 * 一時modeはflashへ保存せず、config/ram_layout.csvで予約した1 byteだけを使う。
 */

#include "move_memory.h"

#include <stddef.h>
#include <stdint.h>

typedef uint8_t u8;
typedef int8_t s8;
typedef uint16_t u16;
typedef int16_t s16;
typedef uint32_t u32;
typedef int32_t s32;

enum {
    PARTY_SIZE = 6,
    POKEMON_SIZE = 100,
    MAX_MON_MOVES = 4,
    MAX_LEARNABLE_MOVES = 40,
    EGG_MOVE_BUFFER_COUNT = 50,
    SPECIES_COUNT = 1621,

    MON_DATA_MOVE1 = 13,
    MON_DATA_PP_BONUSES = 21,
    MON_DATA_LEVEL = 56,
    MON_DATA_SPECIES = 11,

    FLAG_DH_BUILD_CLEAR = 0x114B,
    FLAG_HALL_OF_FAME = 0x082C,
    FLAG_RAID_ACTIVE = 0x0919,
    FLAG_BATTLE_FACILITY = 0x0930,
    ITEM_MIRROR_HERB = 965,

    MOVE_NONE = 0,
    MOVE_SURF = 57,
    MOVE_BEHEMOTH_BLADE = 768,
    MOVE_BEHEMOTH_BASH = 769,

    MENU_NOTHING_CHOSEN = -2,
    MENU_B_PRESSED = -1,
    MENU_CANCEL_INDEX = 3,
    MENU_COUNT = 4,
    MENU_WINDOW_INVALID = 0xFF,
    NUM_TASKS = 16,
    COPYWIN_BOTH = 3,
    SE_SELECT = 5,
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

_Static_assert(sizeof(struct Task) == 40, "FireRed Task ABI changed");
_Static_assert(offsetof(struct Task, data) == 8, "FireRed Task data ABI changed");
_Static_assert(sizeof(struct WindowTemplate) == 8, "FireRed WindowTemplate ABI changed");

typedef void (*TaskFunc)(u8 task_id);
typedef void (*TaskIdFn)(u8 task_id);
typedef u8 (*CreateTaskFn)(TaskFunc func, u8 priority);
typedef void (*VoidFn)(void);
typedef void (*SetupScriptFn)(const u8 *script);
typedef u8 (*FlagGetFn)(u16 flag);
typedef u8 (*CheckBagHasItemFn)(u16 item, u16 quantity);
typedef u32 (*GetMonDataFn)(const void *mon, s32 field, u8 *destination);
typedef u8 (*GetAllEggMovesFn)(void *mon, u16 *moves, u8 ignore_known);
typedef void (*SetMonMoveSlotFn)(void *mon, u16 move, u8 slot);
typedef void (*MonMoveSlotFn)(void *mon, u8 slot);
typedef void (*ShiftMoveSlotFn)(void *mon, u8 slot_to, u8 slot_from);
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

#define PTR(type, address) ((type)(uintptr_t)(address))

#ifndef VEGA_MOVE_MEMORY_LINKED_ABI
#error "move-memory linked addresses must come from the verified T06 contract"
#endif

#define G_MOVE_MANAGER_MODE PTR(volatile u8 *, 0x0203EC00)
#define G_BATTLE_TYPE_FLAGS PTR(volatile u32 *, 0x02022AAC)
#define G_PLAYER_PARTY PTR(u8 *, 0x020241E4)
#define G_SPECIAL_VAR_8004 PTR(volatile u16 *, 0x02036FF4)
#define G_SPECIAL_VAR_8005 PTR(volatile u16 *, 0x02036FF6)
#define G_SPECIAL_VAR_RESULT PTR(volatile u16 *, 0x02037004)
#define G_TASKS PTR(struct Task *, 0x030050D0)
#define S_ITEM_USE_ON_FIELD_CB PTR(volatile TaskFunc *, 0x02039910)
/* T09の正規root。全1,621種がu16 move + u8 levelの3-byte ABI。 */
#define G_LEVEL_UP_LEARNSET_ROOT PTR(const u8 *const *const *, 0x0804346C)

#define FN_GET_MON_DATA PTR(GetMonDataFn, 0x0803F355)
#define FN_FLAG_GET PTR(FlagGetFn, 0x0806DEC5)
#define FN_SCRIPT_CONTEXT2_ENABLE PTR(VoidFn, 0x08069201)
#define FN_ENABLE_BOTH_SCRIPT_CONTEXTS PTR(VoidFn, 0x080693F5)
#define FN_SCRIPT_CONTEXT1_SETUP PTR(SetupScriptFn, 0x080693A5)
#define FN_PLAY_SE PTR(PlaySeFn, 0x08071A71)
#define FN_CREATE_TASK PTR(CreateTaskFn, 0x08076BB5)
#define FN_DESTROY_TASK PTR(TaskIdFn, 0x08076CA1)
#define FN_CHECK_BAG_HAS_ITEM PTR(CheckBagHasItemFn, 0x08099949)
#define FN_SETUP_ITEM_USE_ON_FIELD PTR(TaskIdFn, 0x080A2311)
#define FN_ADD_WINDOW PTR(AddWindowFn, 0x08003CB1)
#define FN_REMOVE_WINDOW PTR(WindowU8Fn, 0x08003E09)
#define FN_COPY_WINDOW_TO_VRAM PTR(WindowPairFn, 0x08003EED)
#define FN_PUT_WINDOW_TILEMAP PTR(WindowU8Fn, 0x08003F6D)
#define FN_FILL_WINDOW_PIXEL_BUFFER PTR(WindowPairFn, 0x08004429)
#define FN_ADD_TEXT_PRINTER PTR(TextPrinterFn, 0x08002C45)
#define FN_SCHEDULE_BG_COPY PTR(WindowU8Fn, 0x080F77FD)
#define FN_DRAW_STD_WINDOW_FRAME PTR(WindowPairFn, 0x080F7F7D)
#define FN_CLEAR_STD_WINDOW_FRAME PTR(WindowPairFn, 0x080F7FFD)
#define FN_GET_STD_WINDOW_BASE_TILE PTR(GetBaseTileFn, 0x080F89CD)
#define FN_MENU_INIT_CURSOR PTR(MenuInitCursorFn, 0x0811030D)
#define FN_MENU_PROCESS_INPUT PTR(MenuInputFn, 0x08110BF9)
#define FN_GET_ALL_EGG_MOVES \
    PTR(GetAllEggMovesFn, VEGA_MOVE_MEMORY_GET_ALL_EGG_MOVES_ADDRESS)
#define FN_SET_MON_MOVE_SLOT \
    PTR(SetMonMoveSlotFn, VEGA_MOVE_MEMORY_SET_MON_MOVE_SLOT_ADDRESS)
#define FN_REMOVE_MON_PP_BONUS PTR(MonMoveSlotFn, 0x08040755)
#define FN_SHIFT_MOVE_SLOT PTR(ShiftMoveSlotFn, 0x080C0C79)

#define PUBLIC_TEXT(name) \
    __attribute__((section(".text." #name), used, noinline))

static const u8 sTextRemember[] = {0x05, 0x23, 0x02, 0x41, 0x0D, 0xFF};
static const u8 sTextForget[] = {0x2C, 0x0D, 0x2A, 0x29, 0xFF};
static const u8 sTextEggMove[] = {0x60, 0x6F, 0x8B, 0x2C, 0x3C, 0xFF};
static const u8 sTextCancel[] = {0x24, 0x22, 0x29, 0xFF};
static const u8 *const sMenuTexts[MENU_COUNT] = {
    sTextRemember, sTextForget, sTextEggMove, sTextCancel,
};

__attribute__((section(".rodata.VegaMoveMemory_ItemScriptPointer"), used))
volatile const u32 VegaMoveMemory_ItemScriptPointer = 0;

static void Task_StartItemScript(u8 task_id);
static void Task_HandleModeMenu(u8 task_id);

static void set_result(u16 value)
{
    *G_SPECIAL_VAR_RESULT = value;
}

static void close_mode_menu(u8 task_id, u8 selection)
{
    u8 window_id = (u8)G_TASKS[task_id].data[0];
    set_result(selection);
    FN_PLAY_SE(SE_SELECT);
    FN_CLEAR_STD_WINDOW_FRAME(window_id, 1);
    FN_REMOVE_WINDOW(window_id);
    FN_SCHEDULE_BG_COPY(0);
    FN_DESTROY_TASK(task_id);
    FN_ENABLE_BOTH_SCRIPT_CONTEXTS();
}

static void Task_HandleModeMenu(u8 task_id)
{
    s8 choice = FN_MENU_PROCESS_INPUT();
    if (choice == MENU_NOTHING_CHOSEN) {
        return;
    }
    if (choice == MENU_B_PRESSED || choice < 0 || choice >= MENU_COUNT) {
        close_mode_menu(task_id, MENU_CANCEL_INDEX);
    } else {
        close_mode_menu(task_id, (u8)choice);
    }
}

static void Task_StartItemScript(u8 task_id)
{
    const u8 *script = PTR(const u8 *, VegaMoveMemory_ItemScriptPointer);
    *G_MOVE_MANAGER_MODE = VEGA_MOVE_MEMORY_MODE_NORMAL;
    if ((uintptr_t)script >= 0x08000000u && (uintptr_t)script < 0x0A000000u) {
        FN_SCRIPT_CONTEXT1_SETUP(script);
    } else {
        FN_ENABLE_BOTH_SCRIPT_CONTEXTS();
    }
    FN_DESTROY_TASK(task_id);
}

PUBLIC_TEXT(VegaMoveMemory_FieldUse)
void VegaMoveMemory_FieldUse(u8 task_id)
{
    *G_MOVE_MANAGER_MODE = VEGA_MOVE_MEMORY_MODE_NORMAL;
    *S_ITEM_USE_ON_FIELD_CB = Task_StartItemScript;
    FN_SETUP_ITEM_USE_ON_FIELD(task_id);
}

PUBLIC_TEXT(VegaMoveMemory_ContextAllowedFromState)
u8 VegaMoveMemory_ContextAllowedFromState(u32 battle_type_flags, u8 facility,
                                           u8 raid)
{
    /* field-use item入口そのものが戦闘中の呼出しを遮断する。gBattleTypeFlagsは
     * 戦闘終了後も直前の種別を保持するため、フィールド判定には使わない。 */
    (void)battle_type_flags;
    return facility == 0 && raid == 0;
}

PUBLIC_TEXT(VegaMoveMemory_CheckContext)
void VegaMoveMemory_CheckContext(void)
{
    set_result(VegaMoveMemory_ContextAllowedFromState(
        *G_BATTLE_TYPE_FLAGS, FN_FLAG_GET(FLAG_BATTLE_FACILITY),
        FN_FLAG_GET(FLAG_RAID_ACTIVE)));
}

PUBLIC_TEXT(VegaMoveMemory_OpenModeMenu)
void VegaMoveMemory_OpenModeMenu(void)
{
    struct WindowTemplate template;
    u8 task_id;
    u8 window_id;
    u8 index;

    task_id = FN_CREATE_TASK(Task_HandleModeMenu, 0x50);
    if (task_id >= NUM_TASKS) {
        set_result(MENU_CANCEL_INDEX);
        return;
    }

    template.bg = 0;
    template.tilemap_left = 12;
    template.tilemap_top = 1;
    template.width = 17;
    template.height = 10;
    template.palette_num = 15;
    template.base_block = FN_GET_STD_WINDOW_BASE_TILE();
    window_id = (u8)FN_ADD_WINDOW(&template);
    if (window_id == MENU_WINDOW_INVALID) {
        FN_DESTROY_TASK(task_id);
        set_result(MENU_CANCEL_INDEX);
        return;
    }

    G_TASKS[task_id].data[0] = window_id;
    FN_FILL_WINDOW_PIXEL_BUFFER(window_id, 0x11);
    FN_DRAW_STD_WINDOW_FRAME(window_id, 0);
    FN_PUT_WINDOW_TILEMAP(window_id);
    for (index = 0; index < MENU_COUNT; ++index) {
        FN_ADD_TEXT_PRINTER(window_id, 2, sMenuTexts[index], 8,
                            (u8)(1 + index * 16), 0, NULL);
    }
    FN_MENU_INIT_CURSOR(window_id, 2, 0, 1, 16, MENU_COUNT, 0);
    FN_COPY_WINDOW_TO_VRAM(window_id, COPYWIN_BOTH);
    FN_SCHEDULE_BG_COPY(0);
    set_result(0xFFFF);
    FN_SCRIPT_CONTEXT2_ENABLE();
}

PUBLIC_TEXT(VegaMoveMemory_SetNormalMode)
void VegaMoveMemory_SetNormalMode(void)
{
    *G_MOVE_MANAGER_MODE = VEGA_MOVE_MEMORY_MODE_NORMAL;
}

PUBLIC_TEXT(VegaMoveMemory_SetEggMode)
void VegaMoveMemory_SetEggMode(void)
{
    *G_MOVE_MANAGER_MODE = VEGA_MOVE_MEMORY_MODE_EGG;
}

PUBLIC_TEXT(VegaMoveMemory_ResetMode)
void VegaMoveMemory_ResetMode(void)
{
    *G_MOVE_MANAGER_MODE = VEGA_MOVE_MEMORY_MODE_NORMAL;
}

static u8 normal_relearner_moves(void *mon, u16 *moves)
{
    const u8 *const *learnset_root;
    const u8 *learnset;
    u16 known[MAX_MON_MOVES];
    u16 species;
    u8 level;
    u8 count = 0;
    u8 index;

    species = (u16)FN_GET_MON_DATA(mon, MON_DATA_SPECIES, NULL);
    level = (u8)FN_GET_MON_DATA(mon, MON_DATA_LEVEL, NULL);
    if (species >= SPECIES_COUNT) {
        return 0;
    }
    for (index = 0; index < MAX_MON_MOVES; ++index) {
        known[index] = (u16)FN_GET_MON_DATA(mon, MON_DATA_MOVE1 + index, NULL);
    }

    learnset_root = *G_LEVEL_UP_LEARNSET_ROOT;
    learnset = learnset_root[species];
    if ((uintptr_t)learnset < 0x08000000u || (uintptr_t)learnset >= 0x0A000000u) {
        return 0;
    }

    for (index = 0; index < MAX_LEARNABLE_MOVES; ++index) {
        u16 move;
        u8 move_level;
        u8 slot;
        move = (u16)(learnset[0] | (u16)learnset[1] << 8);
        move_level = learnset[2];
        learnset += 3;
        if (move == MOVE_NONE && move_level == 0xFF) {
            break;
        }
        if (move == MOVE_NONE || move_level > level) {
            continue;
        }
        for (slot = 0; slot < MAX_MON_MOVES; ++slot) {
            if (known[slot] == move) {
                break;
            }
        }
        if (slot != MAX_MON_MOVES) {
            continue;
        }
        for (slot = 0; slot < count; ++slot) {
            if (moves[slot] == move) {
                break;
            }
        }
        if (slot == count && count < MAX_LEARNABLE_MOVES) {
            moves[count++] = move;
        }
    }
    return count;
}

PUBLIC_TEXT(VegaMoveMemory_GetMoveRelearnerMoves)
u8 VegaMoveMemory_GetMoveRelearnerMoves(void *mon, u16 *moves)
{
    if (*G_MOVE_MANAGER_MODE == VEGA_MOVE_MEMORY_MODE_EGG) {
        u16 egg_moves[EGG_MOVE_BUFFER_COUNT];
        u8 count = FN_GET_ALL_EGG_MOVES(mon, egg_moves, 1);
        u8 index;
        if (count > MAX_LEARNABLE_MOVES) {
            count = MAX_LEARNABLE_MOVES;
        }
        for (index = 0; index < count; ++index) {
            moves[index] = egg_moves[index];
        }
        return count;
    }
    return normal_relearner_moves(mon, moves);
}

static u8 selected_mon_has_empty_slot(void)
{
    u16 party_id = *G_SPECIAL_VAR_8004;
    u8 *mon;
    u8 slot;
    if (party_id >= PARTY_SIZE) {
        return 0;
    }
    mon = G_PLAYER_PARTY + party_id * POKEMON_SIZE;
    for (slot = 0; slot < MAX_MON_MOVES; ++slot) {
        if (FN_GET_MON_DATA(mon, MON_DATA_MOVE1 + slot, NULL) == MOVE_NONE) {
            return 1;
        }
    }
    return 0;
}

PUBLIC_TEXT(VegaMoveMemory_SelectedMonHasEmptySlot)
void VegaMoveMemory_SelectedMonHasEmptySlot(void)
{
    set_result(selected_mon_has_empty_slot());
}

PUBLIC_TEXT(VegaMoveMemory_EvaluateEggPolicy)
u8 VegaMoveMemory_EvaluateEggPolicy(u8 dh_clear, u8 hall_of_fame,
                                    u8 has_mirror_herb, u8 has_empty_slot)
{
    if (!dh_clear) {
        return VEGA_MOVE_MEMORY_EGG_LOCKED;
    }
    if (hall_of_fame) {
        return VEGA_MOVE_MEMORY_EGG_ALLOWED;
    }
    if (!has_mirror_herb) {
        return VEGA_MOVE_MEMORY_EGG_NEEDS_HERB;
    }
    if (!has_empty_slot) {
        return VEGA_MOVE_MEMORY_EGG_NEEDS_EMPTY_SLOT;
    }
    return VEGA_MOVE_MEMORY_EGG_ALLOWED;
}

PUBLIC_TEXT(VegaMoveMemory_CheckEggEntry)
void VegaMoveMemory_CheckEggEntry(void)
{
    set_result(VegaMoveMemory_EvaluateEggPolicy(
        FN_FLAG_GET(FLAG_DH_BUILD_CLEAR), FN_FLAG_GET(FLAG_HALL_OF_FAME),
        FN_CHECK_BAG_HAS_ITEM(ITEM_MIRROR_HERB, 1), 1));
}

PUBLIC_TEXT(VegaMoveMemory_CheckEggSlot)
void VegaMoveMemory_CheckEggSlot(void)
{
    set_result(VegaMoveMemory_EvaluateEggPolicy(
        FN_FLAG_GET(FLAG_DH_BUILD_CLEAR), FN_FLAG_GET(FLAG_HALL_OF_FAME),
        FN_CHECK_BAG_HAS_ITEM(ITEM_MIRROR_HERB, 1),
        selected_mon_has_empty_slot()));
}

PUBLIC_TEXT(VegaMoveMemory_SelectedMoveHasPpUps)
void VegaMoveMemory_SelectedMoveHasPpUps(void)
{
    u16 party_id = *G_SPECIAL_VAR_8004;
    u16 slot = *G_SPECIAL_VAR_8005;
    u8 bonuses = 0;
    u16 has_pp_ups = 0;
    if (party_id < PARTY_SIZE && slot < MAX_MON_MOVES) {
        u8 *mon = G_PLAYER_PARTY + party_id * POKEMON_SIZE;
        bonuses = (u8)FN_GET_MON_DATA(mon, MON_DATA_PP_BONUSES, NULL);
        has_pp_ups = (u16)((bonuses >> (slot * 2u)) & 3u) != 0;
    }
    set_result(has_pp_ups);
}

PUBLIC_TEXT(VegaMoveMemory_CanForgetMove)
u8 VegaMoveMemory_CanForgetMove(u16 move)
{
    if (move == MOVE_NONE || move == MOVE_BEHEMOTH_BLADE
        || move == MOVE_BEHEMOTH_BASH) {
        return 0;
    }
    /* HMも通常技と同じ扱い。field能力はstage 22で分離済み。 */
    if (move == MOVE_SURF) {
        return 1;
    }
    return 1;
}

PUBLIC_TEXT(VegaMoveMemory_SelectedMoveCanForget)
void VegaMoveMemory_SelectedMoveCanForget(void)
{
    u16 party_id = *G_SPECIAL_VAR_8004;
    u16 slot = *G_SPECIAL_VAR_8005;
    u16 move = MOVE_NONE;
    if (party_id < PARTY_SIZE && slot < MAX_MON_MOVES) {
        u8 *mon = G_PLAYER_PARTY + party_id * POKEMON_SIZE;
        move = (u16)FN_GET_MON_DATA(mon, MON_DATA_MOVE1 + slot, NULL);
    }
    set_result(VegaMoveMemory_CanForgetMove(move));
}

PUBLIC_TEXT(VegaMoveMemory_DeleteSelectedMove)
void VegaMoveMemory_DeleteSelectedMove(void)
{
    u16 party_id = *G_SPECIAL_VAR_8004;
    u16 slot = *G_SPECIAL_VAR_8005;
    u8 *mon;
    u8 index;

    if (party_id >= PARTY_SIZE || slot >= MAX_MON_MOVES) {
        set_result(0);
        return;
    }

    mon = G_PLAYER_PARTY + party_id * POKEMON_SIZE;
    /* CFRU側のform連動を保ち、既存のPP bonus対応shiftで空きを末尾へ送る。 */
    FN_SET_MON_MOVE_SLOT(mon, MOVE_NONE, (u8)slot);
    FN_REMOVE_MON_PP_BONUS(mon, (u8)slot);
    for (index = (u8)slot; index < MAX_MON_MOVES - 1; ++index) {
        FN_SHIFT_MOVE_SLOT(mon, index, (u8)(index + 1));
    }
    set_result(1);
}
