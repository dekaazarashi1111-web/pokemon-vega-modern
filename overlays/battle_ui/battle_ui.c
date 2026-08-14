/*
 * USER-20260814-BATTLE-UI
 *
 * 固定CFRU-JP e24a16f の move_menu.c にある
 * DISPLAY_REAL_MOVE_TYPE_ON_MENU / DISPLAY_EFFECTIVENESS_ON_MENU 経路を、
 * stage 23の既存CFRU ABIへ結合する小さなThumb adapter。
 *
 * Factory ROMのbyteや独自相性表は持たず、EmitChooseMoveが実damage側の
 * VisualTypeCalcから作ったmoveTypes/moveResultsを唯一の判定元にする。
 */

#include "battle_ui.h"

#include <stddef.h>
#include <stdint.h>

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;

enum {
    MAX_MON_MOVES = 4,
    MAX_BATTLERS = 4,

    BATTLE_TYPE_DOUBLE = 0x00000001,
    BATTLE_TYPE_LINK = 0x00000002,
    BATTLE_TYPE_SCRIPTED_WILD_1 = 0x00002000,
    BATTLE_TYPE_GHOST = 0x00008000,

    MOVE_RESULT_MISSED = 1 << 0,
    MOVE_RESULT_SUPER_EFFECTIVE = 1 << 1,
    MOVE_RESULT_NOT_VERY_EFFECTIVE = 1 << 2,
    MOVE_RESULT_DOESNT_AFFECT_FOE = 1 << 3,
    MOVE_RESULT_FAILED = 1 << 5,
    MOVE_RESULT_NO_EFFECT = MOVE_RESULT_MISSED
        | MOVE_RESULT_DOESNT_AFFECT_FOE | MOVE_RESULT_FAILED,

    SPLIT_STATUS = 2,
    BATTLE_ALIVE_DEF_SIDE = 2,
    COPYWIN_BOTH = 3,

    MOVE_TERABLAST = 1037,
    MOVE_TERASTARSTORM = 1050,

    SUPER_EFFECTIVE_COLOURS = 0,
    NOT_VERY_EFFECTIVE_COLOURS = 4,
    NO_EFFECT_COLOURS = 8,
    REGULAR_COLOURS = 12,

    STAB_PALETTE_INDEX = 5 * 0x10 + 6,
    EFFECT_PALETTE_INDEX = STAB_PALETTE_INDEX + 2,
};

struct ChooseMoveStruct {
    u16 moves[MAX_MON_MOVES];
    u8 current_pp[MAX_MON_MOVES];
    u8 max_pp[MAX_MON_MOVES];
    u16 species;
    u8 mon_type1;
    u8 mon_type2;
    u8 move_types[MAX_MON_MOVES];
    u8 move_results[MAX_BATTLERS][MAX_MON_MOVES];
    u8 z_move_results[MAX_BATTLERS][MAX_MON_MOVES];
    u16 move_powers[MAX_MON_MOVES];
    u16 move_accuracy[MAX_MON_MOVES];
    u8 move_split[MAX_MON_MOVES];
    u8 makes_contact[MAX_MON_MOVES];
    u8 mon_type3;
    u8 mon_tera_type;
    u8 can_mega_evolve;
    u8 mega_variance;
    u8 state_flags;
    u8 bank;
    u8 z_party_index;
    u8 padding_57;
    u16 possible_z_moves[MAX_MON_MOVES];
    u16 ability;
    u8 can_dynamax;
    u8 padding_63;
    u16 possible_max_moves[MAX_MON_MOVES];
    u16 max_move_powers[MAX_MON_MOVES];
    u8 dynamax_party_index;
    u8 terastal_party_index;
    u8 can_terastal;
    u8 padding_77;
};

_Static_assert(offsetof(struct ChooseMoveStruct, move_types) == 0x14,
               "ChooseMove moveTypes ABI changed");
_Static_assert(offsetof(struct ChooseMoveStruct, move_results) == 0x18,
               "ChooseMove moveResults ABI changed");
_Static_assert(offsetof(struct ChooseMoveStruct, z_move_results) == 0x28,
               "ChooseMove zMoveResults ABI changed");
_Static_assert(offsetof(struct ChooseMoveStruct, move_split) == 0x48,
               "ChooseMove moveSplit ABI changed");
_Static_assert(offsetof(struct ChooseMoveStruct, mon_type3) == 0x50,
               "ChooseMove monType3 ABI changed");
_Static_assert(sizeof(struct ChooseMoveStruct) == 0x78,
               "ChooseMoveStruct ABI changed");

typedef u8 *(*StringCopyFn)(u8 *destination, const u8 *source);
typedef void (*BattlePutTextOnWindowFn)(const u8 *text, u8 window_id);
typedef void (*FillWindowPixelBufferFn)(u8 window_id, u8 fill_value);
typedef void (*BlitMoveInfoIconFn)(u8 window_id, u8 icon_id, u8 x, u8 y);
typedef void (*BlitBitmapToWindowFn)(u8 window_id, const u8 *source,
                                     u16 x, u16 y, u16 width, u16 height);
typedef void (*WindowUnaryFn)(u8 window_id);
typedef void (*CopyWindowToVramFn)(u8 window_id, u8 mode);
typedef u8 (*GetBattlerPositionFn)(u8 battler);
typedef u8 (*CountAliveMonsFn)(u8 case_id, u8 attacker, u8 defender);
typedef u8 (*TeraTypeActiveFn)(u8 battler);
typedef u8 (*CheckMoveEffectTableFn)(u16 move, const u8 *table);

#define PTR(type, address) ((type)(uintptr_t)(address))

#define G_ACTIVE_BATTLER PTR(volatile u8 *, 0x02023B24)
#define G_BATTLE_TYPE_FLAGS PTR(volatile u32 *, 0x02022AAC)
#define G_BATTLE_BUFFER_A PTR(volatile u8 *, 0x02022B24)
#define G_MOVE_SELECTION_CURSOR PTR(volatile u8 *, 0x02023F5C)
#define G_BATTLER_CONTROLLER_FUNCS PTR(volatile u32 *, 0x03005020)
#define G_MULTI_USE_PLAYER_CURSOR PTR(volatile u8 *, 0x03005034)
#define G_NEW_BATTLE_STRUCT PTR(volatile u32 *, 0x0203DFB0)
#define G_BATTLE_MONS PTR(volatile u8 *, 0x02023B44)
#define G_DISPLAYED_STRING PTR(u8 *, 0x020228FC)
#define G_PLTT_BUFFER_UNFADED PTR(volatile u16 *, 0x0203712C)
#define G_PLTT_BUFFER_FADED PTR(volatile u16 *, 0x0203752C)

#define G_TYPE_HIGHLIGHT_PALETTE PTR(const u16 *, 0x091B66B8)
#define G_PSS_ICONS PTR(const u8 *, 0x091B5360)
#define G_IGNORE_WEAKNESS_EFFECTS PTR(const u8 *, 0x0903FE65)
#define G_TEXT_SUPER_EFFECTIVE PTR(const u8 *, 0x091430FB)
#define G_TEXT_NOT_VERY_EFFECTIVE PTR(const u8 *, 0x091430FE)
#define G_TEXT_NO_EFFECT PTR(const u8 *, 0x09143101)
#define G_TEXT_STAB PTR(const u8 *, 0x09143103)
#define G_TEXT_STAB_PREFIX PTR(const u8 *, 0x091683F4)
#define G_TEXT_EMPTY PTR(const u8 *, 0x09001CB5)

#define FN_STRING_COPY PTR(StringCopyFn, 0x08008901)
#define FN_BATTLE_PUT_TEXT PTR(BattlePutTextOnWindowFn, 0x080D980D)
#define FN_FILL_WINDOW PTR(FillWindowPixelBufferFn, 0x08004429)
#define FN_BLIT_MOVE_INFO_ICON PTR(BlitMoveInfoIconFn, 0x0810886D)
#define FN_BLIT_BITMAP PTR(BlitBitmapToWindowFn, 0x08004185)
#define FN_COPY_WINDOW PTR(CopyWindowToVramFn, 0x08003EED)
#define FN_PUT_WINDOW_TILEMAP PTR(WindowUnaryFn, 0x08003F6D)
#define FN_GET_BATTLER_POSITION PTR(GetBattlerPositionFn, 0x0807497D)
#define FN_COUNT_ALIVE_MONS PTR(CountAliveMonsFn, 0x090E8139)
#define FN_TERA_TYPE_ACTIVE PTR(TeraTypeActiveFn, 0x09130541)
#define FN_CHECK_MOVE_EFFECT_TABLE PTR(CheckMoveEffectTableFn, 0x09130E2D)

#define HANDLE_INPUT_CHOOSE_TARGET ((u32)0x09115D05)

static struct ChooseMoveStruct *move_info(u8 active)
{
    return PTR(struct ChooseMoveStruct *,
               (uintptr_t)G_BATTLE_BUFFER_A + (u32)active * 0x200u + 4u);
}

static u8 selected_slot(u8 active)
{
    u8 slot = G_MOVE_SELECTION_CURSOR[active];
    return slot < MAX_MON_MOVES ? slot : 0;
}

static u8 displayed_move_type(const struct ChooseMoveStruct *info,
                              u8 active, u8 slot)
{
    u16 move = info->moves[slot];
    if ((move == MOVE_TERABLAST || move == MOVE_TERASTARSTORM)
        && FN_TERA_TYPE_ACTIVE(active)) {
        return info->mon_tera_type;
    }
    return info->move_types[slot];
}

static u8 foe_for_effectiveness(u8 active, u8 *known)
{
    u8 foe = (u8)((active ^ 1u) & 1u);
    *known = 1;
    if (!(*G_BATTLE_TYPE_FLAGS & BATTLE_TYPE_DOUBLE)) {
        return foe;
    }
    if (G_BATTLER_CONTROLLER_FUNCS[active] == HANDLE_INPUT_CHOOSE_TARGET) {
        return *G_MULTI_USE_PLAYER_CURSOR;
    }
    if (FN_COUNT_ALIVE_MONS(BATTLE_ALIVE_DEF_SIDE, active, foe) <= 1u) {
        if (*(volatile u16 *)(G_BATTLE_MONS + (u32)foe * 0x58u + 0x28u) == 0u) {
            foe ^= 2u;
        }
        return foe;
    }
    *known = 0;
    return foe;
}

__attribute__((section(".text.VegaBattleUI_ClassifyResult"), used, noinline))
u8 VegaBattleUI_ClassifyResult(u8 move_result)
{
    if (move_result & MOVE_RESULT_NO_EFFECT) {
        return VEGA_BATTLE_UI_EFFECT_NONE;
    }
    if (move_result & MOVE_RESULT_SUPER_EFFECTIVE) {
        return VEGA_BATTLE_UI_EFFECT_SUPER;
    }
    if (move_result & MOVE_RESULT_NOT_VERY_EFFECTIVE) {
        return VEGA_BATTLE_UI_EFFECT_RESISTED;
    }
    return VEGA_BATTLE_UI_EFFECT_NORMAL;
}

__attribute__((section(".text.VegaBattleUI_GetSelectedMoveType"), used, noinline))
u8 VegaBattleUI_GetSelectedMoveType(void)
{
    u8 active = *G_ACTIVE_BATTLER;
    u8 slot = selected_slot(active);
    return displayed_move_type(move_info(active), active, slot);
}

__attribute__((section(".text.VegaBattleUI_DisplayMoveType"), used, noinline))
void VegaBattleUI_DisplayMoveType(void)
{
    u8 active = *G_ACTIVE_BATTLER;
    u8 slot = selected_slot(active);
    struct ChooseMoveStruct *info = move_info(active);
    u8 move_type = VegaBattleUI_GetSelectedMoveType();
    u8 split = info->move_split[slot];

    if (move_type > 24u) {
        move_type = 9u; /* fixed CFRU Mystery icon; fail visually closed */
    }
    if (split > SPLIT_STATUS) {
        split = SPLIT_STATUS;
    }

    FN_FILL_WINDOW(8, 0xFF);
    FN_BLIT_MOVE_INFO_ICON(8, (u8)(move_type + 1u), 2, 3);
    FN_BLIT_BITMAP(8, G_PSS_ICONS + (u32)split * 24u * 8u,
                   38, 3, 24, 15);
    FN_COPY_WINDOW(8, COPYWIN_BOTH);
    FN_PUT_WINDOW_TILEMAP(8);
}

__attribute__((section(".text.VegaBattleUI_DisplayMoveEffectiveness"), used, noinline))
void VegaBattleUI_DisplayMoveEffectiveness(void)
{
    u8 active = *G_ACTIVE_BATTLER;
    u8 slot = selected_slot(active);
    struct ChooseMoveStruct *info = move_info(active);
    u16 move = info->moves[slot];
    u8 move_type = VegaBattleUI_GetSelectedMoveType();
    u8 effect_class = VEGA_BATTLE_UI_EFFECT_NORMAL;
    u8 stab = 0;
    const u8 *label = G_TEXT_EMPTY;
    u8 target_known = 0;
    u32 battle_flags = *G_BATTLE_TYPE_FLAGS;

    if (!(battle_flags & BATTLE_TYPE_LINK)
        && (battle_flags & (BATTLE_TYPE_SCRIPTED_WILD_1 | BATTLE_TYPE_GHOST))
            != BATTLE_TYPE_GHOST) {
        u8 foe = foe_for_effectiveness(active, &target_known);
        if (target_known && foe < MAX_BATTLERS) {
            u8 position = FN_GET_BATTLER_POSITION(foe);
            if (position < MAX_BATTLERS) {
                u32 new_battle_struct = *G_NEW_BATTLE_STRUCT;
                u8 z_viewing = new_battle_struct != 0u
                    && (*(volatile u8 *)(uintptr_t)(new_battle_struct + 0x248u)
                        & 0x08u);
                u8 result = info->z_move_results[position][slot];
                /* zMoveData starts at 0x23C and its packed flags are at
                 * +0x0C; viewing is bit 3 in the fixed e24a16f ABI. */
                if (!z_viewing) {
                    result = info->move_results[position][slot];
                }
                effect_class = VegaBattleUI_ClassifyResult(result);
            }
        }
        stab = info->move_split[slot] != SPLIT_STATUS
            && (move_type == info->mon_type1
                || move_type == info->mon_type2
                || move_type == info->mon_type3
                || (move_type == info->mon_tera_type
                    && FN_TERA_TYPE_ACTIVE(active)))
            && !FN_CHECK_MOVE_EFFECT_TABLE(move, G_IGNORE_WEAKNESS_EFFECTS);
    }

    switch (effect_class) {
    case VEGA_BATTLE_UI_EFFECT_NONE:
        G_PLTT_BUFFER_UNFADED[EFFECT_PALETTE_INDEX] =
            G_TYPE_HIGHLIGHT_PALETTE[NO_EFFECT_COLOURS];
        G_PLTT_BUFFER_UNFADED[EFFECT_PALETTE_INDEX + 1] =
            G_TYPE_HIGHLIGHT_PALETTE[NO_EFFECT_COLOURS + 1];
        label = G_TEXT_NO_EFFECT;
        stab = 0;
        break;
    case VEGA_BATTLE_UI_EFFECT_SUPER:
        G_PLTT_BUFFER_UNFADED[EFFECT_PALETTE_INDEX] =
            G_TYPE_HIGHLIGHT_PALETTE[SUPER_EFFECTIVE_COLOURS];
        G_PLTT_BUFFER_UNFADED[EFFECT_PALETTE_INDEX + 1] =
            G_TYPE_HIGHLIGHT_PALETTE[SUPER_EFFECTIVE_COLOURS + 1];
        label = G_TEXT_SUPER_EFFECTIVE;
        break;
    case VEGA_BATTLE_UI_EFFECT_RESISTED:
        G_PLTT_BUFFER_UNFADED[EFFECT_PALETTE_INDEX] =
            G_TYPE_HIGHLIGHT_PALETTE[NOT_VERY_EFFECTIVE_COLOURS];
        G_PLTT_BUFFER_UNFADED[EFFECT_PALETTE_INDEX + 1] =
            G_TYPE_HIGHLIGHT_PALETTE[NOT_VERY_EFFECTIVE_COLOURS + 1];
        label = G_TEXT_NOT_VERY_EFFECTIVE;
        break;
    default:
        G_PLTT_BUFFER_UNFADED[EFFECT_PALETTE_INDEX] =
            G_TYPE_HIGHLIGHT_PALETTE[REGULAR_COLOURS];
        G_PLTT_BUFFER_UNFADED[EFFECT_PALETTE_INDEX + 1] =
            G_TYPE_HIGHLIGHT_PALETTE[REGULAR_COLOURS + 1];
        break;
    }

    u8 *text = G_DISPLAYED_STRING;
    *text++ = 0xFC;
    *text++ = 6;
    *text++ = 1;
    text = FN_STRING_COPY(text, G_TEXT_STAB_PREFIX);
    text = FN_STRING_COPY(text, label);
    if (stab) {
        /* RGB(27,27,27) / RGB(4,4,4), fixed CFRU move_menu.c values. */
        G_PLTT_BUFFER_UNFADED[STAB_PALETTE_INDEX] = 0x6F7B;
        G_PLTT_BUFFER_UNFADED[STAB_PALETTE_INDEX + 1] = 0x1084;
        (void)FN_STRING_COPY(text, G_TEXT_STAB);
    }

    FN_BATTLE_PUT_TEXT(G_DISPLAYED_STRING, 7);
    for (u8 index = 0; index < 4; ++index) {
        G_PLTT_BUFFER_FADED[STAB_PALETTE_INDEX + index] =
            G_PLTT_BUFFER_UNFADED[STAB_PALETTE_INDEX + index];
    }
}
