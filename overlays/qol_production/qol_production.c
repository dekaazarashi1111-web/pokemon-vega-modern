#include "qol_production.h"
#include <qol_production_generated.h>
#include "../save_migration/save_migration.h"

typedef uint8_t u8;
typedef int8_t s8;
typedef uint16_t u16;
typedef int16_t s16;
typedef uint32_t u32;
typedef int32_t s32;

typedef void (*TaskFunc)(u8 task_id);

typedef struct Task {
    TaskFunc func;
    u8 is_active;
    u8 prev;
    u8 next;
    u8 priority;
    s16 data[16];
} Task;

typedef struct VegaQolExpResult {
    u32 old_exp;
    u32 new_exp;
    u32 applied_exp;
    u16 requested_items;
    u16 consumed_items;
    u8 old_level;
    u8 new_level;
    u8 levels_crossed;
    u8 stopped_at_cap;
} VegaQolExpResult;

#define PTR(type, address) ((type)(uintptr_t)(address))
#define PUBLIC_TEXT(name) __attribute__((section(".text." #name), used, noinline))

enum {
    MON_DATA_PERSONALITY = 0,
    MON_DATA_OT_ID = 1,
    KEY_A = 0x0001u,
    KEY_B = 0x0002u,
    KEY_SELECT = 0x0004u,
    KEY_START = 0x0008u,
    KEY_RIGHT = 0x0010u,
    KEY_LEFT = 0x0020u,
    KEY_UP = 0x0040u,
    KEY_DOWN = 0x0080u,
    KEY_R = 0x0100u,
    KEY_L = 0x0200u,
};

enum {
    MON_DATA_NICKNAME = 2,
    MON_DATA_SANITY_IS_BAD_EGG = 4,
    MON_DATA_SPECIES = 11,
    MON_DATA_HELD_ITEM = 12,
    MON_DATA_MOVE1 = 13,
    MON_DATA_PP1 = 17,
    MON_DATA_PP_BONUSES = 21,
    MON_DATA_EXP = 25,
    MON_DATA_HP_EV = 26,
    MON_DATA_HP_IV = 39,
    MON_DATA_IS_EGG = 45,
    MON_DATA_ALT_ABILITY = 46,
    MON_DATA_LEVEL = 56,
    MON_DATA_HP = 57,
    MON_DATA_FATEFUL_ENCOUNTER = 79,
    MOVE_NONE = 0,
    MON_HAS_MAX_MOVES = 0xFFFFu,
    MON_ALREADY_KNOWS_MOVE = 0xFFFEu,
};

enum {
    FLAG_BADGE_1 = 0x0820u,
    FLAG_BADGE_2 = 0x0821u,
    FLAG_BADGE_3 = 0x0822u,
    FLAG_BADGE_5 = 0x0824u,
    FLAG_BADGE_6 = 0x0825u,
    FLAG_BADGE_7 = 0x0826u,
    FLAG_BADGE_8 = 0x0827u,
    FLAG_HALL_OF_FAME = 0x082Cu,
    FLAG_DH_CLEAR = 0x114Bu,
    FLAG_EXP_SHARE = 0x0906u,
    FLAG_QOL_EXP_SHARE_INITIALIZED = 0x12FDu,
    FLAG_QOL_DAYCARE_QUEST = 0x12FEu,
    FLAG_QOL_EGG_BASKET = 0x12FFu,
    FLAG_PENDING_DAYCARE_EGG = 0x0266u,
};

enum {
    BATTLE_TYPE_DOUBLE = 0x00000001u,
    BATTLE_TYPE_IS_MASTER = 0x00000004u,
    BATTLE_TYPE_LINK = 0x00000002u,
    BATTLE_TYPE_TRAINER = 0x00000008u,
    BATTLE_TYPE_MULTI = 0x00000040u,
    BATTLE_TYPE_SAFARI = 0x00000080u,
    BATTLE_TYPE_SCRIPTED_WILD_1 = 0x00002000u,
    BATTLE_TYPE_SCRIPTED_WILD_2 = 0x00020000u,
    BATTLE_TYPE_LEGENDARY = 0x00040000u,
    BATTLE_TYPE_FRONTIER_MASK = 0x06000100u,
    BATTLE_TYPE_INGAME_PARTNER = 0x00400000u,
    BATTLE_TYPE_DYNAMAX = 0x40000000u,
    QOL_STATE_HIGH_RAID_PENDING = 0x40u,
    QOL_STATE_LATE_GIMMICK_PENDING = 0x80u,
};

enum {
    /* Expanded vars 0x5180..0x51FD are stable across every heap reset.  The
     * load adapter clears this block, so UI/battle provenance remains
     * volatile even though the backing range participates in normal saves. */
    QOL_STATE_ADDRESS = 0x0203B5E8u,
    QOL_STATE_SIZE = 0xFCu,
    MAIN_ADDRESS = 0x03003130u,
    MAIN_CALLBACK2_OFFSET = 4u,
    MAIN_HELD_KEYS_RAW_OFFSET = 0x28u,
    MAIN_NEW_KEYS_RAW_OFFSET = 0x2Au,
    MAIN_HELD_KEYS_OFFSET = 0x2Cu,
    MAIN_NEW_KEYS_OFFSET = 0x2Eu,
    MAIN_REPEAT_KEYS_OFFSET = 0x30u,
    START_MENU_CALLBACK_SLOT = 0x02037024u,
    START_MENU_INPUT_CALLBACK = 0x0806EA75u,
    OVERWORLD_CALLBACK = 0x08055E75u,
    PSS_DATA_SLOT = 0x020396FCu,
    PSS_CURSOR_AREA = 0x0203976Cu,
    PSS_CURSOR_POSITION = 0x0203976Du,
    PSS_BOX_SPRITES_OFFSET = 0x0A84u,
    PSS_CURSOR_TEXT_OFFSET = 0x0CF5u,
    PSS_CURSOR_TEXT_STRIDE = 36u,
    SUMMARY_DATA_SLOT = 0x0203B0B4u,
    SUMMARY_WINDOW_IDS_OFFSET = 0x3000u,
    SUMMARY_INPUT_STATE_OFFSET = 0x321Cu,
    SUMMARY_PAGE_OFFSET = 0x31C0u,
    SUMMARY_CURRENT_MON_OFFSET = 0x323Cu,
    SAVE_BLOCK2_SLOT = 0x0300504Cu,
    SAVE_OPTIONS_BUTTON_MODE_OFFSET = 0x13u,
    SAVE_BLOCK1_SLOT = 0x03005048u,
    SAVE_LOCATION_OFFSET = 4u,
    SAVE_DAYCARE_OFFSET = 0x2F80u,
    DAYCARE_MON_STRIDE = 140u,
    DAYCARE_OFFSPRING_OFFSET = DAYCARE_MON_STRIDE * 2u,
    PLAYER_PARTY = 0x020241E4u,
    PLAYER_PARTY_COUNT = 0x02023F89u,
    ENEMY_PARTY = 0x02023F8Cu,
    BATTLE_TYPE_FLAGS = 0x02022AACu,
    ACTIVE_BATTLER = 0x02023B24u,
    BATTLE_MONS = 0x02023B44u,
    BATTLE_MON_STRIDE = 0x58u,
    BATTLE_MON_MOVES = 0x0Cu,
    BATTLE_MON_PP = 0x24u,
    BATTLE_MON_HP = 0x28u,
    ACTION_CURSOR = 0x02023F58u,
    MOVE_CURSOR = 0x02023F5Cu,
    MOVE_MANAGER_MODE = 0x0203EC00u,
    QOL_BASKET_COUNTER = 0x0203B6E4u,
    EGG_HATCH_DATA_SLOT = 0x03000E74u,
    PARTY_MENU = 0x0203B014u,
    PARTY_MENU_SLOT_OFFSET = 9u,
    PARTY_MENU_LEARN_METHOD_OFFSET = 16u,
    PARTY_MENU_USE_EXIT_CALLBACK = 0x0203B034u,
    ITEM_USE_CALLBACK = 0x03005EE8u,
    TASKS = 0x030050D0u,
    SPECIAL_VAR_ITEM = 0x0203ACA8u,
    MOVE_TO_LEARN = 0x02023F82u,
    SPECIAL_VAR_8004 = 0x02036FF4u,
    SPECIAL_VAR_8005 = 0x02036FF6u,
    SAVE_BUFFER = 0x020399B0u,
    SECTOR31_IMAGE = 0x0203CF9Cu,
    SAVE_SECTOR_SIZE = 0x1000u,
    SAVE_SECTOR_DATA_SIZE = 0x0FF0u,
};

typedef u8 (*FlagGetFn)(u16);
typedef void (*FlagChangeFn)(u16);
typedef u32 (*GetBoxMonDataFn)(void *, s32, u8 *);
typedef void (*SetBoxMonDataFn)(void *, s32, const void *);
typedef u32 (*GetBoxMonDataAtFn)(u8, u8, s32);
typedef void *(*GetBoxedMonPtrFn)(u8, u8);
typedef void (*SetBoxMonAtFn)(u8, u8, void *);
typedef void (*ZeroBoxMonAtFn)(u8, u8);
typedef u8 (*StorageGetCurrentBoxFn)(void);
typedef u8 (*BagCheckFn)(u16, u16);
typedef u8 (*IsMailFn)(u16);
typedef u8 (*GetPocketFn)(u16);
typedef u8 (*CalculatePpFn)(u16, u8, u8);
typedef u8 (*MovePoolFn)(void *, u16 *);
typedef u8 (*TrySavingDataFn)(u8);
typedef void (*SaveFinalizeFn)(VegaModernSaveData *);
typedef VegaSaveStatus (*SaveValidateFn)(const VegaModernSaveData *, u32);
typedef void (*SaveInitFn)(VegaModernSaveData *, u8);
typedef void (*VoidFn)(void);
typedef u8 (*PssInputFn)(void);
typedef void (*DaycareFn)(void *);
typedef u8 (*DaycareScoreFn)(void *);
typedef u32 (*SubtractEggStepsFn)(u32, void *);
typedef u8 (*IsMonShinyFn)(void *);
typedef u8 (*MoveLimitFn)(u8, u8, u8);
typedef u8 (*ScriptContextFn)(void);
typedef void (*PrintHelpFn)(const u8 *, u8);
typedef void (*WindowPrintFn)(u8, u8, u8, u8, const void *, u8, const u8 *);
typedef u8 (*ShowPssFn)(void);
typedef void (*BoxMonAtToMonFn)(u8, u8, void *);
typedef void (*SetMonMoveSlotFn)(void *, u16, u8);
typedef void (*RemoveMonPpBonusFn)(void *, u8);
typedef u16 (*GetMonAbilityFn)(const void *);
typedef u8 (*ApplyExpCandyFn)(void *, u16, u8, u16, void *);
typedef u8 (*ApplyEvResetItemFn)(void *, u16, void *);
typedef u8 (*ApplyEvResetAllFn)(void *, void *);
typedef u8 (*HyperTrainingFn)(void);
typedef void (*CalculateMonStatsFn)(void *);
typedef u8 (*WildGenerateFn)(const void *, u8, u8);
typedef u16 (*FishingGenerateFn)(const void *, u8);
typedef u8 (*ShouldEggHatchFn)(void);
typedef void (*TryDecrementEggFn)(void *, u8);
typedef u8 (*ModifyBreedingScoreFn)(u8);
typedef u8 (*ReusableTmFn)(u16);
typedef u8 (*TmIdFn)(u16);
typedef u32 (*ItemPriceFn)(u16);
typedef u8 (*GetSetPokedexFlagFn)(u16, u8);
typedef u16 (*RandomFn)(void);
typedef void (*CreateMonFn)(void *, u16, u8, u8, u8, u32, u8, u32);
typedef u8 (*GetAllEggMovesFn)(void *, u16 *, u8);
typedef u32 (*InUnionRoomFn)(void);
typedef u8 (*ContextFlagFn)(void);
typedef u8 (*CalculatePartyCountFn)(void);
typedef u16 (*GiveMoveToMonFn)(void *, u16);
typedef u16 (*MonTryLearningMoveFn)(void *, u8);
typedef void (*SetUpItemUseCallbackFn)(u8);
typedef u8 (*DisplayPartyMessageFn)(const u8 *, u8);
typedef u8 (*PartyTextActiveFn)(void);
typedef void (*PartyMoveMessageFn)(u8, u16);
typedef void (*PartyTaskFn)(u8);
typedef u8 (*UpdatePartyMonFn)(u8, void *);
typedef void (*BoxMonToMonFn)(void *, void *);
typedef u32 (*EcologySelectFn)(u16, u8, u8, u8, u8);
typedef void (*GenerateWildDirectFn)(u16, u8, u8);
typedef u8 (*ExecuteItemEffectFn)(u8, u16, u8);
typedef u32 (*GetSpeciesExpFn)(u16, u8);
typedef u32 (*CandyValueFn)(u16);
typedef u8 (*EffectiveLevelCapFn)(void);
typedef u16 (*EvolutionTargetFn)(void *, u8, u16);
typedef void (*BeginEvolutionFn)(void *, u16, u8, u8);
typedef void (*DestroyTaskFn)(u8);
typedef void (*InitPartyMenuFn)(u8, u8, u8, u8, u8, TaskFunc, VoidFn);
typedef const u8 *(*ConfigureTrainerBattleFn)(const u8 *);
typedef void (*TrainerBattleEndFn)(u8);
typedef u8 (*ConfigureRaidFn)(u8, u8, u8, u8, u8);

typedef struct QolTextPrinterTemplate {
    const u8 *current_char;
    u8 attributes[12];
} QolTextPrinterTemplate;

typedef void (*QolTextPrinterCallback)(QolTextPrinterTemplate *, u16);

/* Vega JP uses the original 32-byte FireRed TextPrinter ABI.  In
 * particular, active/state/textSpeed live at 0x1b/0x1c/0x1d; the later
 * pret minLetterSpacing/japanese tail is not present in this ROM. */
typedef struct QolTextPrinter {
    QolTextPrinterTemplate printer_template;
    QolTextPrinterCallback callback;
    u8 sub_union[7];
    u8 active;
    u8 state;
    u8 text_speed;
    u8 delay_counter;
    u8 scroll_distance;
} QolTextPrinter;

typedef u32 (*RenderFontFn)(QolTextPrinter *);
typedef void (*CopyWindowToVramFn)(u8, u8);
typedef void (*FillWindowFn)(u8, u8);
typedef void (*WindowU8Fn)(u8);
typedef u8 (*ListMenuInitFn)(const void *, u16, u16);
typedef s32 (*ListMenuInputFn)(u8);
typedef void (*ListMenuDestroyFn)(u8, u16 *, u16 *);
typedef void *(*AllocZeroedFn)(u32);
typedef void (*FreeFn)(void *);
typedef void (*SetPssTaskFn)(TaskFunc);
typedef void (*NamingScreenFn)(u8, u8 *, u16, u16, u32, VoidFn);
typedef u8 (*CreateTaskFn)(TaskFunc, u8);
typedef u8 (*TryWriteSectorFn)(u16, const void *);
typedef void (*ReadFlashFn)(u16, u32, void *, u32);
typedef u16 (*AddWindowFn)(const void *);
typedef void (*WindowPairFn)(u8, u8);
typedef void (*TextPrinterFn)(u8, u8, const u8 *, u8, u8, u8, void *);
typedef u8 (*MenuInitCursorFn)(u8, u8, u8, u8, u8, u8, u8);
typedef s8 (*MenuInputFn)(void);
typedef u16 (*GetBaseTileFn)(void);
typedef void (*PlaySeFn)(u16);

typedef struct QolWindowTemplate {
    u8 bg;
    u8 tilemap_left;
    u8 tilemap_top;
    u8 width;
    u8 height;
    u8 palette_num;
    u16 base_block;
} QolWindowTemplate;

typedef struct QolSupplyShopState {
    u16 eligible[VEGA_QOL_SUPPLY_CATALOG_COUNT];
    u16 last_result;
    u16 last_catalog_index;
    u8 eligible_count;
    u8 page;
    u8 window_id;
    u8 reserved0;
    u8 balance_text[16];
    u8 limited_session_bits;
    u8 reserved[3];
} QolSupplyShopState;

typedef struct QolListMenuTemplate {
    const VegaQolGeneratedListItem *items;
    void (*move_cursor)(s32, u8, void *);
    void (*print_item)(u8, s32, u8);
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
} QolListMenuTemplate;

#define FN_FLAG_GET PTR(FlagGetFn, 0x0806DEC5u)
#define FN_FLAG_SET PTR(FlagChangeFn, 0x0806DE75u)
#define FN_FLAG_CLEAR PTR(FlagChangeFn, 0x0806DE9Du)
#define FN_GET_BOX_MON_DATA PTR(GetBoxMonDataFn, 0x0803F4B1u)
/* Party-only fields (notably LEVEL) require GetMonData. */
#define FN_GET_MON_DATA PTR(GetBoxMonDataFn, 0x0803F355u)
#define FN_SET_BOX_MON_DATA PTR(SetBoxMonDataFn, 0x0803FBC5u)
#define FN_GET_BOX_MON_DATA_AT PTR(GetBoxMonDataAtFn, 0x0808B4B5u)
#define FN_GET_BOXED_MON PTR(GetBoxedMonPtrFn, 0x0808B7CDu)
#define FN_SET_BOX_MON_AT PTR(SetBoxMonAtFn, 0x0808B651u)
#define FN_ZERO_BOX_MON_AT PTR(ZeroBoxMonAtFn, 0x0808B751u)
#define FN_STORAGE_CURRENT_BOX PTR(StorageGetCurrentBoxFn, 0x0808B491u)
#define FN_BOX_MON_AT_TO_MON PTR(BoxMonAtToMonFn, 0x0808B78Du)
#define FN_CHECK_BAG_SPACE PTR(BagCheckFn, 0x08099A09u)
#define FN_ADD_BAG_ITEM PTR(BagCheckFn, 0x08099A8Du)
#define FN_REMOVE_BAG_ITEM PTR(BagCheckFn, 0x08099BE1u)
#define FN_IS_MAIL PTR(IsMailFn, 0x08097AE9u)
#define FN_GET_POCKET PTR(GetPocketFn, 0x0809A3E9u)
#define FN_CALCULATE_PP PTR(CalculatePpFn, 0x0804070Du)
#define FN_REMOVE_MON_PP_BONUS PTR(RemoveMonPpBonusFn, 0x08040755u)
#define FN_SET_MON_MOVE_SLOT PTR(SetMonMoveSlotFn, 0x09114699u)
#define FN_GET_MON_ABILITY PTR(GetMonAbilityFn, 0x090DA23Du)
#define FN_MOVE_RELEARN_POOL PTR(MovePoolFn, 0x091141D5u)
#define FN_TRY_SAVING_DATA PTR(TrySavingDataFn, 0x080DB34Du)
#define FN_SAVE_FINALIZE PTR(SaveFinalizeFn, 0x092D28D9u)
#define FN_SAVE_VALIDATE PTR(SaveValidateFn, 0x092D12E1u)
#define FN_SAVE_INIT PTR(SaveInitFn, 0x092D2979u)
#define FN_STAGE35_SAVE_LOAD PTR(TrySavingDataFn, 0x0930375Du)
#define FN_STAGE35_CONFIGURE_TRAINER \
    PTR(ConfigureTrainerBattleFn, 0x09302DE5u)
#define FN_STAGE35_TRAINER_BATTLE_END PTR(TrainerBattleEndFn, 0x09303501u)
#define FN_CONFIGURE_HIGH_RAID PTR(ConfigureRaidFn, 0x0912632Du)
#define FN_CFRU_PENDING_CLEAR PTR(VoidFn, 0x0910EE79u)
#define FN_CFRU_IS_RAID PTR(ContextFlagFn, 0x091263A9u)
#define FN_PRINT_HELP PTR(PrintHelpFn, 0x08113B65u)
#define FN_WINDOW_PRINT PTR(WindowPrintFn, 0x0812ED25u)
#define FN_CLOSE_START_MENU PTR(VoidFn, 0x0806F645u)
#define FN_DESTROY_HELP PTR(VoidFn, 0x080F89F9u)
#define FN_SHOW_PSS PTR(ShowPssFn, 0x0808C0E5u)
#define FN_SCRIPT_CONTEXT_ENABLED PTR(ScriptContextFn, 0x08069219u)
#define FN_ORIGINAL_BATTLE_ACTION PTR(VoidFn, 0x09118CBDu)
#define FN_ORIGINAL_BATTLE_MOVE PTR(VoidFn, 0x09116F91u)
#define FN_ORIGINAL_PSS_INPUT PTR(PssInputFn, 0x080942E9u)
#define FN_REFRESH_PSS_MON_DATA PTR(VoidFn, 0x08092989u)
#define FN_PRINT_PSS_MON_INFO PTR(VoidFn, 0x0808EED9u)
#define FN_CHECK_MOVE_LIMITATIONS PTR(MoveLimitFn, 0x090D4D79u)
#define FN_IS_MON_SHINY PTR(IsMonShinyFn, 0x08043AB9u)
#define FN_DAYCARE_GIVE_EGG PTR(DaycareFn, 0x090EAC51u)
#define FN_DAYCARE_TRIGGER_PENDING PTR(DaycareFn, 0x090EB541u)
#define FN_DAYCARE_COMPATIBILITY PTR(DaycareScoreFn, 0x090EB825u)
#define FN_SUBTRACT_EGG_STEPS PTR(SubtractEggStepsFn, 0x090EB771u)
#define FN_SHOULD_EGG_HATCH PTR(ShouldEggHatchFn, 0x0804594Du)
#define FN_TRY_DECREMENT_EGG_STEPS PTR(TryDecrementEggFn, 0x090EB7A1u)
#define FN_MODIFY_BREEDING_SCORE PTR(ModifyBreedingScoreFn, 0x090EB93Du)
#define FN_REUSABLE_TM PTR(ReusableTmFn, 0x091108E9u)
#define FN_ITEM_MYSTERY2 PTR(TmIdFn, 0x0809A3C5u)
#define FN_ITEM_PRICE PTR(ItemPriceFn, 0x0809A30Du)
#define FN_GET_SET_DEX PTR(GetSetPokedexFlagFn, 0x08088A51u)
#define FN_APPLY_EXP_CANDY PTR(ApplyExpCandyFn, 0x09132015u)
#define FN_APPLY_EV_RESET_ITEM PTR(ApplyEvResetItemFn, 0x09132325u)
#define FN_APPLY_EV_RESET_ALL PTR(ApplyEvResetAllFn, 0x091324DDu)
#define FN_HYPER_TRAINING PTR(HyperTrainingFn, 0x09128E11u)
#define FN_CALCULATE_MON_STATS PTR(CalculateMonStatsFn, 0x090D939Du)
#define FN_WILD_GENERATE PTR(WildGenerateFn, 0x09220065u)
#define FN_FISHING_GENERATE PTR(FishingGenerateFn, 0x092200FDu)
#define FN_STANDARD_WILD_BATTLE PTR(VoidFn, 0x0913341Du)
#define FN_CHECK_BAG_HAS_ITEM PTR(BagCheckFn, 0x08099949u)
#define FN_RANDOM PTR(RandomFn, 0x0804448Du)
#define FN_CREATE_MON PTR(CreateMonFn, 0x0803D1C1u)
#define FN_GET_ALL_EGG_MOVES PTR(GetAllEggMovesFn, 0x090EB971u)
#define FN_IN_UNION_ROOM PTR(InUnionRoomFn, 0x0811B915u)
#define FN_LINK_STATE_ACTIVE PTR(ContextFlagFn, 0x08055CEDu)
#define FN_GET_SAFARI_ZONE_FLAG PTR(ContextFlagFn, 0x080A2165u)
#define FN_CALCULATE_PARTY_COUNT PTR(CalculatePartyCountFn, 0x08040331u)
#define FN_GIVE_MOVE_TO_MON PTR(GiveMoveToMonFn, 0x0803E009u)
#define FN_ORIGINAL_MON_TRY_LEARNING PTR(MonTryLearningMoveFn, 0x09114039u)
#define FN_SET_UP_ITEM_USE_CALLBACK PTR(SetUpItemUseCallbackFn, 0x080A29A5u)
#define FN_DISPLAY_PARTY_MESSAGE PTR(DisplayPartyMessageFn, 0x08120AE9u)
#define FN_PARTY_TEXT_ACTIVE PTR(PartyTextActiveFn, 0x08120B61u)
#define FN_UPDATE_PARTY_MON PTR(UpdatePartyMonFn, 0x08126D85u)
#define FN_PARTY_TRY_EVOLUTION PTR(PartyTaskFn, 0x08127049u)
#define FN_PARTY_MOVE_NEEDS_REPLACE PTR(PartyTaskFn, 0x081270B5u)
#define FN_PARTY_MOVE_LEARNED PTR(PartyMoveMessageFn, 0x08127145u)
#define FN_BOX_MON_TO_MON PTR(BoxMonToMonFn, 0x0803DEE1u)
#define FN_ECOLOGY_SELECT PTR(EcologySelectFn, 0x092204ADu)
#define FN_GENERATE_WILD_DIRECT PTR(GenerateWildDirectFn, 0x080825E9u)
#define FN_START_WILD_DIRECT PTR(VoidFn, 0x0807EE2Du)
#define FN_EXECUTE_ITEM_EFFECT PTR(ExecuteItemEffectFn, 0x08125BCDu)
#define FN_GET_SPECIES_EXP PTR(GetSpeciesExpFn, 0x090FC505u)
#define FN_CANDY_VALUE PTR(CandyValueFn, 0x09131FD5u)
#define FN_EFFECTIVE_LEVEL_CAP PTR(EffectiveLevelCapFn, 0x09132011u)
#define FN_GET_EVOLUTION_TARGET PTR(EvolutionTargetFn, 0x090FB775u)
#define FN_FREE_PARTY_POINTERS PTR(VoidFn, 0x0811F879u)
#define FN_BEGIN_EVOLUTION PTR(BeginEvolutionFn, 0x080CEF01u)
#define FN_DESTROY_TASK PTR(DestroyTaskFn, 0x08076CA1u)
#define FN_INIT_PARTY_MENU PTR(InitPartyMenuFn, 0x0811F24Du)
#define FN_RENDER_FONT PTR(RenderFontFn, 0x08002E4Du)
#define FN_COPY_WINDOW_TO_VRAM PTR(CopyWindowToVramFn, 0x08003EEDu)
#define FN_FILL_WINDOW PTR(FillWindowFn, 0x08004429u)
#define FN_SCHEDULE_BG_COPY PTR(WindowU8Fn, 0x080F77FDu)
#define FN_ORIGINAL_SUMMARY_INPUT PTR(TaskFunc, 0x08135029u)
#define FN_LIST_MENU_INIT PTR(ListMenuInitFn, 0x08107AFDu)
#define FN_LIST_MENU_INPUT PTR(ListMenuInputFn, 0x08107B7Du)
#define FN_LIST_MENU_DESTROY PTR(ListMenuDestroyFn, 0x08107C41u)
#define FN_ALLOC_ZEROED PTR(AllocZeroedFn, 0x08002BB1u)
#define FN_FREE PTR(FreeFn, 0x08002BC5u)
#define FN_SET_PSS_TASK PTR(SetPssTaskFn, 0x0808CA35u)
#define FN_STANDARD_PSS_RETURN PTR(VoidFn, 0x0808C89Du)
#define FN_CREATE_TASK PTR(CreateTaskFn, 0x08076BB5u)
#define FN_TRY_WRITE_SECTOR PTR(TryWriteSectorFn, 0x080DA9C1u)
#define FN_READ_FLASH PTR(ReadFlashFn, 0x081C2A55u)
#define FN_ADD_WINDOW PTR(AddWindowFn, 0x08003CB1u)
#define FN_REMOVE_WINDOW PTR(WindowU8Fn, 0x08003E09u)
#define FN_PUT_WINDOW_TILEMAP PTR(WindowU8Fn, 0x08003F6Du)
#define FN_ADD_TEXT_PRINTER PTR(TextPrinterFn, 0x08002C45u)
#define FN_DRAW_STD_WINDOW_FRAME PTR(WindowPairFn, 0x080F7F7Du)
#define FN_CLEAR_STD_WINDOW_FRAME PTR(WindowPairFn, 0x080F7FFDu)
#define FN_GET_STD_WINDOW_BASE_TILE PTR(GetBaseTileFn, 0x080F89CDu)
#define FN_MENU_INIT_CURSOR PTR(MenuInitCursorFn, 0x0811030Du)
#define FN_MENU_PROCESS_INPUT PTR(MenuInputFn, 0x08110BF9u)
#define FN_PLAY_SE PTR(PlaySeFn, 0x08071A71u)
#define FN_SCRIPT_CONTEXT2_ENABLE PTR(VoidFn, 0x08069201u)
#define FN_ENABLE_BOTH_SCRIPT_CONTEXTS PTR(VoidFn, 0x080693F5u)
#define G_TEXT_PRINTERS PTR(QolTextPrinter *, 0x02020030u)
#define G_SUPPLY_SHOP_STATE PTR(QolSupplyShopState *, 0x0203ED40u)
#define G_SPECIAL_RESULT PTR(volatile u16 *, 0x02037004u)

extern void VegaQolProduction_OriginalReadKeys(void);
extern void VegaQolProduction_OriginalPrintSkillsPage(void);
extern u8 VegaQolProduction_OriginalTrySavingData(u8 save_type);
extern u8 VegaQolProduction_OriginalFlagSet(u16 flag);
extern u8 VegaQolProduction_OriginalFlagClear(u16 flag);
extern void VegaQolProduction_OriginalEggHatchCallback(void);
extern void VegaQolProduction_OriginalDoNamingScreen(
    u8 template_num, u8 *destination, u16 species, u16 gender,
    u32 personality, VoidFn return_callback);
extern void VegaQolProduction_OriginalPartyMenuTryEvolution(u8 task_id);

typedef struct QolState {
    u32 magic;
    u32 inverse;
    u32 selection[VEGA_QOL_BOX_COUNT];
    VegaQolSearchFilter filter;
    u16 last_result;
    u8 panel_index;
    u8 panel_active;
    u8 filter_mode;
    u8 auto_active;
    u8 auto_move_slot;
    u8 last_box;
    u8 hyper_stat;
    u8 wild_token_armed;
    u8 battle_auto_eligible;
    u32 wild_token_pid;
    u32 battle_token_pid;
    u8 marker_modes[VEGA_QOL_BOX_CAPACITY];
    u8 marker_box;
    u8 marker_initialized;
    u8 judge_iv[36];
    u8 judge_ev[36];
    u8 relearn_text[36];
    u16 relearn_move;
    u8 relearn_slot;
    u8 relearn_box;
    u8 relearn_position;
    u8 relearn_index;
    u8 relearn_active;
    u8 panel_confirm;
    u8 pss_confirm_op;
    u8 panel_status_active;
    u8 help_button_mode_suppressed;
} QolState;

typedef struct BaseStatsView {
    u8 stats[6];
    u8 type1;
    u8 type2;
    u8 catch_rate;
    u8 padding;
    u16 ev_yield;
    u16 item1;
    u16 item2;
    u8 growth[6];
    u16 ability1;
    u8 middle[2];
    u16 ability2;
    u16 hidden_ability;
    u16 exp_yield;
} BaseStatsView;

typedef struct TextColor {
    u8 foreground;
    u8 background;
    u8 shadow;
} TextColor;

#define G_QOL_STATE PTR(QolState *, QOL_STATE_ADDRESS)
#define G_MAIN_CALLBACK2 (*(volatile u32 *)(uintptr_t)(MAIN_ADDRESS + MAIN_CALLBACK2_OFFSET))
#define G_MAIN_HELD_KEYS_RAW (*(volatile u16 *)(uintptr_t)(MAIN_ADDRESS + MAIN_HELD_KEYS_RAW_OFFSET))
#define G_MAIN_NEW_KEYS_RAW (*(volatile u16 *)(uintptr_t)(MAIN_ADDRESS + MAIN_NEW_KEYS_RAW_OFFSET))
#define G_MAIN_HELD_KEYS (*(volatile u16 *)(uintptr_t)(MAIN_ADDRESS + MAIN_HELD_KEYS_OFFSET))
#define G_MAIN_NEW_KEYS (*(volatile u16 *)(uintptr_t)(MAIN_ADDRESS + MAIN_NEW_KEYS_OFFSET))
#define G_MAIN_REPEAT_KEYS (*(volatile u16 *)(uintptr_t)(MAIN_ADDRESS + MAIN_REPEAT_KEYS_OFFSET))
#define G_START_MENU_CALLBACK (*(volatile u32 *)(uintptr_t)START_MENU_CALLBACK_SLOT)
#define G_PSS_DATA (*(volatile u32 *)(uintptr_t)PSS_DATA_SLOT)
#define G_BATTLE_FLAGS (*(volatile u32 *)(uintptr_t)BATTLE_TYPE_FLAGS)
#define G_TRAINER_OPPONENT_A (*(volatile u16 *)(uintptr_t)0x020385E2u)
#define G_ACTIVE_BATTLER (*(volatile u8 *)(uintptr_t)ACTIVE_BATTLER)
#define G_TASKS PTR(volatile Task *, TASKS)
#define G_PARTY_SLOT (*(volatile s8 *)(uintptr_t)(PARTY_MENU + PARTY_MENU_SLOT_OFFSET))
#define G_PARTY_EXIT_CALLBACK (*(volatile u32 *)(uintptr_t)PARTY_MENU)
#define G_PARTY_LEARN_METHOD (*(volatile u16 *)(uintptr_t)(PARTY_MENU + PARTY_MENU_LEARN_METHOD_OFFSET))
#define G_PARTY_USE_EXIT (*(volatile u8 *)(uintptr_t)PARTY_MENU_USE_EXIT_CALLBACK)
#define G_SPECIAL_ITEM (*(volatile u16 *)(uintptr_t)SPECIAL_VAR_ITEM)
#define G_MOVE_TO_LEARN (*(volatile u16 *)(uintptr_t)MOVE_TO_LEARN)
#define G_AFTER_EVOLUTION (*(volatile u32 *)(uintptr_t)0x030053CCu)

_Static_assert(sizeof(QolState) <= QOL_STATE_SIZE, "QOL state exceeds RAM ledger");
_Static_assert(sizeof(BaseStatsView) == 32u, "BaseStats ABI differs");
_Static_assert(sizeof(QolTextPrinterTemplate) == 16u,
               "Vega text-printer template ABI differs");
_Static_assert(sizeof(QolTextPrinter) == 32u,
               "Vega text-printer ABI differs");
_Static_assert(sizeof(QolListMenuTemplate) == 24u,
               "Vega list-menu template ABI differs");
_Static_assert(sizeof(QolWindowTemplate) == 8u,
               "Vega window-template ABI differs");
_Static_assert(sizeof(QolSupplyShopState) == 128u,
               "Stage27 BP-shop volatile ABI differs");

static void copy_bytes(void *destination, const void *source, u32 size)
{
    u8 *out = (u8 *)destination;
    const u8 *in = (const u8 *)source;
    while (size-- != 0u)
        *out++ = *in++;
}

static void clear_bytes(void *destination, u32 size)
{
    u8 *out = (u8 *)destination;
    while (size-- != 0u)
        *out++ = 0u;
}

static u8 bytes_differ(const void *left, const void *right, u32 size)
{
    const u8 *a = (const u8 *)left;
    const u8 *b = (const u8 *)right;
    while (size-- != 0u) {
        if (*a++ != *b++)
            return 1u;
    }
    return 0u;
}

static u8 pointer_is_ewram(u32 value, u32 size)
{
    return (u8)(value >= 0x02000000u && value + size >= value
                && value + size <= 0x02040000u);
}

static void ensure_state(void)
{
    QolState *state = G_QOL_STATE;
    if (state->magic == VEGA_QOL_PRODUCTION_MAGIC
        && state->inverse == ~VEGA_QOL_PRODUCTION_MAGIC)
        return;
    clear_bytes(state, sizeof(*state));
    state->magic = VEGA_QOL_PRODUCTION_MAGIC;
    state->inverse = ~VEGA_QOL_PRODUCTION_MAGIC;
}

static void clear_owned_high_raid_pending(void)
{
    if ((G_QOL_STATE->auto_move_slot & QOL_STATE_HIGH_RAID_PENDING) == 0u)
        return;
    FN_CFRU_PENDING_CLEAR();
    G_BATTLE_FLAGS &= ~(BATTLE_TYPE_DYNAMAX | BATTLE_TYPE_DOUBLE
                        | BATTLE_TYPE_INGAME_PARTNER);
    G_QOL_STATE->auto_move_slot &= (u8)~QOL_STATE_HIGH_RAID_PENDING;
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

static u8 pss_judge_mode(void)
{
    return (u8)(G_QOL_STATE->filter_mode & 3u);
}

static void set_pss_judge_mode(u8 mode)
{
    G_QOL_STATE->filter_mode = (u8)((G_QOL_STATE->filter_mode & ~3u)
                                     | (mode & 3u));
}

static u8 summary_judge_mode(void)
{
    return (u8)((G_QOL_STATE->filter_mode >> 2) & 3u);
}

static void set_summary_judge_mode(u8 mode)
{
    G_QOL_STATE->filter_mode = (u8)((G_QOL_STATE->filter_mode & ~12u)
                                     | ((mode & 3u) << 2));
}

enum {
    OPTIONS_BUTTON_MODE_HELP = 0u,
    OPTIONS_BUTTON_MODE_LR = 1u,
};

static volatile u8 *options_button_mode(void)
{
    u32 save = *(volatile u32 *)(uintptr_t)SAVE_BLOCK2_SLOT;
    if (!pointer_is_ewram(save, SAVE_OPTIONS_BUTTON_MODE_OFFSET + 1u))
        return (volatile u8 *)0;
    return PTR(volatile u8 *, save + SAVE_OPTIONS_BUTTON_MODE_OFFSET);
}

static void suppress_help_button_mode(void)
{
    volatile u8 *mode = options_button_mode();
    if (mode != (volatile u8 *)0 && *mode == OPTIONS_BUTTON_MODE_HELP) {
        *mode = OPTIONS_BUTTON_MODE_LR;
        G_QOL_STATE->help_button_mode_suppressed = 1u;
    }
}

static void restore_help_button_mode(void)
{
    volatile u8 *mode = options_button_mode();
    if (G_QOL_STATE->help_button_mode_suppressed != 0u
        && mode != (volatile u8 *)0
        && *mode == OPTIONS_BUTTON_MODE_LR)
        *mode = OPTIONS_BUTTON_MODE_HELP;
    G_QOL_STATE->help_button_mode_suppressed = 0u;
}

static void *save_block1(void)
{
    u32 pointer = *(volatile u32 *)(uintptr_t)SAVE_BLOCK1_SLOT;
    if (!pointer_is_ewram(pointer, 0x3000u))
        return (void *)0;
    return (void *)(uintptr_t)pointer;
}

static void *daycare(void)
{
    u8 *save = (u8 *)save_block1();
    return save == (void *)0 ? (void *)0 : save + SAVE_DAYCARE_OFFSET;
}

static u8 hall_of_fame(void)
{
    return (u8)(FN_FLAG_GET(FLAG_HALL_OF_FAME)
                || gVegaModernSaveData->vega_hall_of_fame);
}

static u8 kanto_access(void)
{
    return (u8)(gVegaModernSaveData->kanto_travel_unlocked
                || hall_of_fame()
                || (FN_FLAG_GET(FLAG_BADGE_5) && FN_FLAG_GET(FLAG_DH_CLEAR)));
}

static u8 kanto_daycare_quest(void)
{
    return (u8)(kanto_access() && FN_FLAG_GET(FLAG_QOL_DAYCARE_QUEST));
}

static u8 daycare_first_use(void)
{
    void *data = daycare();
    if (data == (void *)0)
        return 0u;
    return (u8)(FN_GET_BOX_MON_DATA(data, MON_DATA_SPECIES, (u8 *)0) != 0u
                || FN_GET_BOX_MON_DATA((u8 *)data + DAYCARE_MON_STRIDE,
                                       MON_DATA_SPECIES, (u8 *)0) != 0u);
}

static u8 official_caught_at_least_100(void)
{
    u16 index;
    u16 caught = 0u;
    for (index = 0u; index < VEGA_QOL_OFFICIAL_DEX_COUNT; ++index) {
        if (FN_GET_SET_DEX(gVegaQolOfficialNationalDex[index], 1u)
            && ++caught >= 100u)
            return 1u;
    }
    return 0u;
}

PUBLIC_TEXT(VegaQolProduction_FeatureUnlocked)
u8 VegaQolProduction_FeatureUnlocked(u16 feature)
{
    if (feature >= VEGA_QOL_FEATURE_COUNT)
        return 0u;
    switch ((VegaQolFeature)feature) {
    case VEGA_QOL_TEXT_SPEED_INSTANT:
    case VEGA_QOL_FAST_MOVEMENT:
    case VEGA_QOL_IV_EV_JUDGE:
    case VEGA_QOL_PC_SEARCH_MULTISELECT:
        return 1u;
    case VEGA_QOL_EXP_SHARE:
    case VEGA_QOL_EVERSTONE_SUPPLY:
    case VEGA_QOL_EGG_PC_TRANSFER:
        return FN_FLAG_GET(FLAG_BADGE_1);
    case VEGA_QOL_EGG_QUEUE_5:
        return daycare_first_use();
    case VEGA_QOL_FREE_MOVE_RELEARN:
        return FN_FLAG_GET(FLAG_BADGE_1);
    case VEGA_QOL_PC_MOVE_EDIT:
        return FN_FLAG_GET(FLAG_BADGE_2);
    case VEGA_QOL_EXP_CANDY_XS_S:
    case VEGA_QOL_EXP_CANDY_M_ONCE:
    case VEGA_QOL_ABILITY_CAPSULE_MINTS:
    case VEGA_QOL_EV_RESET_ALL:
    case VEGA_QOL_FIELD_PC:
    case VEGA_QOL_PC_HELD_ITEM_BULK:
    case VEGA_QOL_AUTO_BATTLE:
        return FN_FLAG_GET(FLAG_DH_CLEAR);
    case VEGA_QOL_DESTINY_KNOT:
    case VEGA_QOL_EGG_BASKET:
        return kanto_daycare_quest();
    case VEGA_QOL_OVAL_CHARM:
        return (u8)(kanto_daycare_quest()
                    || official_caught_at_least_100());
    case VEGA_QOL_POWER_ITEMS:
        return FN_FLAG_GET(FLAG_BADGE_5);
    case VEGA_QOL_EXP_CANDY_M_REPEAT:
        return FN_FLAG_GET(FLAG_BADGE_6);
    case VEGA_QOL_EXP_CANDY_L_SILVER_CAP:
        return FN_FLAG_GET(FLAG_BADGE_7);
    case VEGA_QOL_ABILITY_PATCH_ALL_MINTS:
    case VEGA_QOL_EV_RESET_ITEMS:
    case VEGA_QOL_STANDARD_TRAINING_SHOP:
        return FN_FLAG_GET(FLAG_BADGE_8);
    case VEGA_QOL_EXP_CANDY_XL_ONCE:
    case VEGA_QOL_RESEARCH_PROFILE:
    case VEGA_QOL_TM_REUSE_LICENSE:
    case VEGA_QOL_HIDDEN_ABILITY_DEXNAV:
        return hall_of_fame();
    case VEGA_QOL_COMPETITIVE_ITEM_SUPPLY:
    case VEGA_QOL_HIGH_DIFFICULTY_RAID:
        return (u8)(hall_of_fame()
                    && popcount8(gVegaModernSaveData->kanto_certifications) >= 4u);
    case VEGA_QOL_TERA_DYNAMAX_STORY:
    case VEGA_QOL_BOOST_ENERGY_UB_PARADOX:
    case VEGA_QOL_EXP_CANDY_XL_GOLD_CAP:
        return gVegaModernSaveData->league_ii_cleared;
    }
    return 0u;
}

PUBLIC_TEXT(VegaQolProduction_BpShopUnlockSatisfied)
u8 VegaQolProduction_BpShopUnlockSatisfied(u8 kind)
{
    switch (kind) {
    case 0u: return FN_FLAG_GET(FLAG_DH_CLEAR);
    case 1u: return kanto_access();
    case 2u: return FN_FLAG_GET(FLAG_BADGE_1);
    case 3u: return kanto_daycare_quest();
    case 4u: return FN_FLAG_GET(FLAG_BADGE_5);
    case 5u: return FN_FLAG_GET(FLAG_BADGE_6);
    case 6u:
        return (u8)(hall_of_fame()
                    && popcount8(gVegaModernSaveData->kanto_certifications)
                       >= 4u);
    case 7u: return FN_FLAG_GET(FLAG_BADGE_7);
    case 8u: return FN_FLAG_GET(FLAG_BADGE_8);
    case 9u:
    case 10u:
        return gVegaModernSaveData->league_ii_cleared;
    default:
        return 0u;
    }
}

static u8 restore_durable_ledger(void)
{
    VegaModernSaveData *candidate;
    FN_READ_FLASH(31u, 0u, PTR(void *, SAVE_BUFFER), SAVE_SECTOR_SIZE);
    candidate = (VegaModernSaveData *)(void *)(
        PTR(u8 *, SAVE_BUFFER)
        + (VEGA_SAVE_EWRAM_ADDRESS - SECTOR31_IMAGE));
    if (FN_SAVE_VALIDATE(candidate, VEGA_SAVE_LEDGER_SIZE) != VEGA_SAVE_OK)
        return 0u;
    copy_bytes(gVegaModernSaveData, candidate, VEGA_SAVE_LEDGER_SIZE);
    return 1u;
}

static u8 ensure_save(void)
{
    VegaSaveStatus status = FN_SAVE_VALIDATE(gVegaModernSaveData,
                                             VEGA_SAVE_LEDGER_SIZE);
    if (status == VEGA_SAVE_EMPTY_OR_LEGACY && restore_durable_ledger())
        status = VEGA_SAVE_OK;
    if (status == VEGA_SAVE_OK)
        return 1u;
    if (status == VEGA_SAVE_EMPTY_OR_LEGACY) {
        FN_SAVE_INIT(gVegaModernSaveData, FN_FLAG_GET(FLAG_BADGE_1));
        return 1u;
    }
    return 0u;
}

/* Cross-store transactions commit the stock save before the private sector.
 * Callers keep an exact RAM rollback image and compensate both stores if
 * either write fails.  The definitions live with the BP shop persistence
 * owner below; rewards and egg delivery share that single transaction order. */
static u8 persist_cross_store(void);
static void compensate_cross_store(void);

static u8 reward_claimed(u16 marker)
{
    if (marker >= VEGA_ITEM_COUNT)
        return 1u;
    return (u8)((gVegaModernSaveData->item_obtained_flags[marker >> 3]
                 >> (marker & 7u)) & 1u);
}

static void mark_reward_claimed(u16 marker)
{
    if (marker < VEGA_ITEM_COUNT)
        gVegaModernSaveData->item_obtained_flags[marker >> 3] |=
            (u8)(1u << (marker & 7u));
}

static VegaQolStatus claim_single_item_raw(u16 item, u16 marker, u8 unique)
{
    u8 added = 0u;
    if (reward_claimed(marker))
        return VEGA_QOL_ALREADY_CLAIMED;
    copy_bytes(gVegaSaveRollbackData, gVegaModernSaveData,
               VEGA_SAVE_LEDGER_SIZE);
    if (unique && FN_CHECK_BAG_HAS_ITEM(item, 1u)) {
        mark_reward_claimed(marker);
        FN_SAVE_FINALIZE(gVegaModernSaveData);
    } else {
        if (!FN_CHECK_BAG_SPACE(item, 1u) || !FN_ADD_BAG_ITEM(item, 1u))
            return VEGA_QOL_CAPACITY;
        added = 1u;
        mark_reward_claimed(marker);
        FN_SAVE_FINALIZE(gVegaModernSaveData);
    }
    if (!persist_cross_store()) {
        if (added)
            (void)FN_REMOVE_BAG_ITEM(item, 1u);
        copy_bytes(gVegaModernSaveData, gVegaSaveRollbackData,
                   VEGA_SAVE_LEDGER_SIZE);
        compensate_cross_store();
        return VEGA_QOL_PERSIST_FAILED;
    }
    return VEGA_QOL_OK;
}

static VegaQolStatus claim_power_set_raw(void)
{
    static const u16 items[6] = {861u, 856u, 857u, 858u, 859u, 860u};
    u8 added = 0u;
    u8 index;
    if (reward_claimed(856u))
        return VEGA_QOL_ALREADY_CLAIMED;
    copy_bytes(gVegaSaveRollbackData, gVegaModernSaveData,
               VEGA_SAVE_LEDGER_SIZE);
    for (index = 0u; index < 6u; ++index) {
        if (!FN_CHECK_BAG_SPACE(items[index], 1u)
            || !FN_ADD_BAG_ITEM(items[index], 1u)) {
            while (added != 0u) {
                --added;
                (void)FN_REMOVE_BAG_ITEM(items[added], 1u);
            }
            return VEGA_QOL_CAPACITY;
        }
        ++added;
    }
    mark_reward_claimed(856u);
    FN_SAVE_FINALIZE(gVegaModernSaveData);
    if (!persist_cross_store()) {
        while (added != 0u) {
            --added;
            (void)FN_REMOVE_BAG_ITEM(items[added], 1u);
        }
        copy_bytes(gVegaModernSaveData, gVegaSaveRollbackData,
                   VEGA_SAVE_LEDGER_SIZE);
        compensate_cross_store();
        return VEGA_QOL_PERSIST_FAILED;
    }
    return VEGA_QOL_OK;
}

static VegaQolStatus claim_daycare_set_raw(void)
{
    u8 add_knot = 0u;
    u8 add_oval = 0u;
    if (reward_claimed(902u) && reward_claimed(684u))
        return VEGA_QOL_ALREADY_CLAIMED;
    copy_bytes(gVegaSaveRollbackData, gVegaModernSaveData,
               VEGA_SAVE_LEDGER_SIZE);
    if (!reward_claimed(902u) && !FN_CHECK_BAG_HAS_ITEM(902u, 1u)) {
        if (!FN_CHECK_BAG_SPACE(902u, 1u) || !FN_ADD_BAG_ITEM(902u, 1u))
            return VEGA_QOL_CAPACITY;
        add_knot = 1u;
    }
    if (!reward_claimed(684u) && !FN_CHECK_BAG_HAS_ITEM(684u, 1u)) {
        if (!FN_CHECK_BAG_SPACE(684u, 1u) || !FN_ADD_BAG_ITEM(684u, 1u)) {
            if (add_knot)
                (void)FN_REMOVE_BAG_ITEM(902u, 1u);
            return VEGA_QOL_CAPACITY;
        }
        add_oval = 1u;
    }
    (void)add_oval;
    mark_reward_claimed(902u);
    mark_reward_claimed(684u);
    FN_SAVE_FINALIZE(gVegaModernSaveData);
    if (!persist_cross_store()) {
        if (add_oval)
            (void)FN_REMOVE_BAG_ITEM(684u, 1u);
        if (add_knot)
            (void)FN_REMOVE_BAG_ITEM(902u, 1u);
        copy_bytes(gVegaModernSaveData, gVegaSaveRollbackData,
                   VEGA_SAVE_LEDGER_SIZE);
        compensate_cross_store();
        return VEGA_QOL_PERSIST_FAILED;
    }
    return VEGA_QOL_OK;
}

PUBLIC_TEXT(VegaQolProduction_ClaimOneTimeReward)
u8 VegaQolProduction_ClaimOneTimeReward(u8 reward)
{
    VegaQolStatus status;
    if (!ensure_save())
        return VEGA_QOL_CORRUPT_SAVE;
    switch ((VegaQolOneTimeReward)reward) {
    case VEGA_QOL_REWARD_EVERSTONE:
        if (!VegaQolProduction_FeatureUnlocked(VEGA_QOL_EVERSTONE_SUPPLY))
            return VEGA_QOL_LOCKED;
        status = claim_single_item_raw(195u, 195u, 0u);
        break;
    case VEGA_QOL_REWARD_EXP_CANDY_M:
        if (!VegaQolProduction_FeatureUnlocked(VEGA_QOL_EXP_CANDY_M_ONCE))
            return VEGA_QOL_LOCKED;
        status = claim_single_item_raw(990u, 990u, 0u);
        break;
    case VEGA_QOL_REWARD_POWER_SET:
        if (!VegaQolProduction_FeatureUnlocked(VEGA_QOL_POWER_ITEMS))
            return VEGA_QOL_LOCKED;
        status = claim_power_set_raw();
        break;
    case VEGA_QOL_REWARD_EXP_CANDY_XL:
        if (!VegaQolProduction_FeatureUnlocked(VEGA_QOL_EXP_CANDY_XL_ONCE))
            return VEGA_QOL_LOCKED;
        status = claim_single_item_raw(992u, 992u, 0u);
        break;
    case VEGA_QOL_REWARD_DAYCARE_SET:
        if (!kanto_daycare_quest())
            return VEGA_QOL_LOCKED;
        status = claim_daycare_set_raw();
        break;
    default:
        status = VEGA_QOL_INVALID_ARGUMENT;
        break;
    }
    return (u8)status;
}

enum {
    SUPPLY_PAGE_SIZE = 5u,
    SUPPLY_WINDOW_INVALID = 0xFFu,
    SUPPLY_RESULT_SUCCESS = 0u,
    SUPPLY_RESULT_CANCELLED = 2u,
    SUPPLY_RESULT_LOCKED = 3u,
    SUPPLY_RESULT_INVALID = 5u,
    SUPPLY_RESULT_BUSY = 9u,
    SUPPLY_RESULT_PERSIST_FAILED = 13u,
    SUPPLY_RESULT_INSUFFICIENT_BP = 14u,
    SUPPLY_RESULT_BAG_FULL = 15u,
    SUPPLY_RESULT_ENGINE_REJECTED = 16u,
    SUPPLY_RESULT_LIMIT_REACHED = 17u,
    SUPPLY_RESULT_NOT_SET = 0xFFFFu,
    PERSIST_FAULT_STANDARD = 1u,
    PERSIST_FAULT_SECTOR31 = 2u,
    PERSIST_FAULT_STANDARD_BIT = 0x40u,
    PERSIST_FAULT_SECTOR31_BIT = 0x80u,
};

static u8 supply_entry_unlocked(u16 catalog_index)
{
    if (catalog_index >= VEGA_QOL_SUPPLY_CATALOG_COUNT)
        return 0u;
    if (catalog_index == VEGA_QOL_LEGACY_FIRE_STONE_INDEX)
        return kanto_access();
    return VegaQolProduction_FeatureUnlocked(
        gVegaQolSupplyCatalog[catalog_index].feature);
}

static u8 supply_entry_available(u16 catalog_index)
{
    const VegaQolSupplyEntry *entry;
    if (!supply_entry_unlocked(catalog_index))
        return 0u;
    entry = &gVegaQolSupplyCatalog[catalog_index];
    if (entry->repeatability == VEGA_QOL_SUPPLY_LIMITED)
        return (u8)!reward_claimed(entry->item_id);
    if (entry->repeatability == VEGA_QOL_SUPPLY_LIMITED_REPEATABLE) {
        if (entry->limit_slot >= 8u)
            return 0u;
        return (u8)((G_SUPPLY_SHOP_STATE->limited_session_bits
                     & (u8)(1u << entry->limit_slot)) == 0u);
    }
    return 1u;
}

static void supply_set_result(u16 result)
{
    G_SUPPLY_SHOP_STATE->last_result = result;
    *G_SPECIAL_RESULT = result;
}

static u8 supply_persist_sector(void)
{
    if (G_QOL_STATE->panel_confirm & PERSIST_FAULT_SECTOR31_BIT) {
        G_QOL_STATE->panel_confirm &= (u8)~PERSIST_FAULT_SECTOR31_BIT;
        return 0u;
    }
    clear_bytes(PTR(void *, SAVE_BUFFER), SAVE_SECTOR_SIZE);
    copy_bytes(PTR(void *, SAVE_BUFFER), PTR(const void *, SECTOR31_IMAGE),
               SAVE_SECTOR_DATA_SIZE);
    return (u8)(FN_TRY_WRITE_SECTOR(31u, PTR(const void *, SAVE_BUFFER))
                == 1u);
}

static u8 supply_persist_standard(void)
{
    /* Transaction owners write sector 31 themselves and must not re-enter the
     * global normal-save adapter, otherwise the journal is written twice. */
    if (G_QOL_STATE->panel_confirm & PERSIST_FAULT_STANDARD_BIT) {
        G_QOL_STATE->panel_confirm &= (u8)~PERSIST_FAULT_STANDARD_BIT;
        return 0u;
    }
    return (u8)(VegaQolProduction_OriginalTrySavingData(0u) == 1u);
}

/* Exact-ROM fault probe used only by the T19 mGBA acceptance runner.  There
 * is no field/script dispatcher route to this symbol.  Each fault is one-shot
 * so the compensation write immediately exercises the real save functions. */
PUBLIC_TEXT(VegaQolProduction_TestInjectPersistenceFault)
u8 VegaQolProduction_TestInjectPersistenceFault(u8 mode)
{
    ensure_state();
    G_QOL_STATE->panel_confirm &= 1u;
    if (mode == PERSIST_FAULT_STANDARD)
        G_QOL_STATE->panel_confirm |= PERSIST_FAULT_STANDARD_BIT;
    else if (mode == PERSIST_FAULT_SECTOR31)
        G_QOL_STATE->panel_confirm |= PERSIST_FAULT_SECTOR31_BIT;
    else if (mode != 0u)
        return 0u;
    return 1u;
}

static u8 persist_cross_store(void)
{
    if (!supply_persist_standard())
        return 0u;
    return supply_persist_sector();
}

static void compensate_cross_store(void)
{
    FN_SAVE_FINALIZE(gVegaModernSaveData);
    (void)supply_persist_standard();
    (void)supply_persist_sector();
}

static u16 supply_purchase_raw(u16 catalog_index)
{
    const VegaQolSupplyEntry *entry;
    u8 session_bit = 0u;
    if (!ensure_save())
        return SUPPLY_RESULT_PERSIST_FAILED;
    if (catalog_index >= VEGA_QOL_SUPPLY_CATALOG_COUNT)
        return SUPPLY_RESULT_INVALID;
    entry = &gVegaQolSupplyCatalog[catalog_index];
    if (!supply_entry_unlocked(catalog_index))
        return SUPPLY_RESULT_LOCKED;
    if (!supply_entry_available(catalog_index))
        return SUPPLY_RESULT_LIMIT_REACHED;
    if (gVegaModernSaveData->factory.battle_points < entry->price_bp)
        return SUPPLY_RESULT_INSUFFICIENT_BP;
    copy_bytes(gVegaSaveRollbackData, gVegaModernSaveData,
               VEGA_SAVE_LEDGER_SIZE);
    if (!FN_CHECK_BAG_SPACE(entry->item_id, 1u)
        || !FN_ADD_BAG_ITEM(entry->item_id, 1u))
        return SUPPLY_RESULT_BAG_FULL;
    gVegaModernSaveData->factory.battle_points =
        (u16)(gVegaModernSaveData->factory.battle_points - entry->price_bp);
    if (entry->repeatability == VEGA_QOL_SUPPLY_LIMITED)
        mark_reward_claimed(entry->item_id);
    else if (entry->repeatability == VEGA_QOL_SUPPLY_LIMITED_REPEATABLE) {
        session_bit = (u8)(1u << entry->limit_slot);
        G_SUPPLY_SHOP_STATE->limited_session_bits |= session_bit;
    }
    FN_SAVE_FINALIZE(gVegaModernSaveData);
    if (!supply_persist_standard() || !supply_persist_sector()) {
        /* The normal save can succeed before sector 31 fails.  Compensate
         * both stores before reporting failure so a retry cannot duplicate
         * the item or debit BP twice. */
        (void)FN_REMOVE_BAG_ITEM(entry->item_id, 1u);
        G_SUPPLY_SHOP_STATE->limited_session_bits &= (u8)~session_bit;
        copy_bytes(gVegaModernSaveData, gVegaSaveRollbackData,
                   VEGA_SAVE_LEDGER_SIZE);
        compensate_cross_store();
        return SUPPLY_RESULT_PERSIST_FAILED;
    }
    return SUPPLY_RESULT_SUCCESS;
}

static VegaQolStatus supply_result_to_qol(u16 result)
{
    if (result == SUPPLY_RESULT_SUCCESS)
        return VEGA_QOL_OK;
    if (result == SUPPLY_RESULT_LOCKED)
        return VEGA_QOL_LOCKED;
    if (result == SUPPLY_RESULT_INSUFFICIENT_BP)
        return VEGA_QOL_INSUFFICIENT_CURRENCY;
    if (result == SUPPLY_RESULT_BAG_FULL)
        return VEGA_QOL_CAPACITY;
    if (result == SUPPLY_RESULT_PERSIST_FAILED)
        return VEGA_QOL_PERSIST_FAILED;
    if (result == SUPPLY_RESULT_CANCELLED)
        return VEGA_QOL_CANCELLED;
    if (result == SUPPLY_RESULT_LIMIT_REACHED)
        return VEGA_QOL_ALREADY_CLAIMED;
    return VEGA_QOL_INVALID_ARGUMENT;
}

PUBLIC_TEXT(VegaQolProduction_BpShopPurchaseByIndex)
u16 VegaQolProduction_BpShopPurchaseByIndex(u16 catalog_index)
{
    u16 result = supply_purchase_raw(catalog_index);
    G_SUPPLY_SHOP_STATE->last_catalog_index = catalog_index;
    supply_set_result(result);
    return result;
}

PUBLIC_TEXT(VegaQolProduction_PurchaseSupply)
u8 VegaQolProduction_PurchaseSupply(u8 catalog_index)
{
    return (u8)supply_result_to_qol(supply_purchase_raw(catalog_index));
}

static u8 supply_page_rows(void)
{
    u8 first = (u8)(G_SUPPLY_SHOP_STATE->page * SUPPLY_PAGE_SIZE);
    u8 remaining = first < G_SUPPLY_SHOP_STATE->eligible_count
        ? (u8)(G_SUPPLY_SHOP_STATE->eligible_count - first) : 0u;
    return remaining > SUPPLY_PAGE_SIZE ? SUPPLY_PAGE_SIZE : remaining;
}

static void supply_append_balance(void)
{
    u8 *out = G_SUPPLY_SHOP_STATE->balance_text;
    u8 index = 0u;
    u8 prefix = 0u;
    u16 balance = gVegaModernSaveData->factory.battle_points;
    u16 divisor = 1000u;
    u8 started = 0u;
    while (gVegaQolBpPrefix[prefix] != 0xFFu
           && index + 1u < sizeof(G_SUPPLY_SHOP_STATE->balance_text))
        out[index++] = gVegaQolBpPrefix[prefix++];
    while (divisor != 0u
           && index + 1u < sizeof(G_SUPPLY_SHOP_STATE->balance_text)) {
        u8 digit = (u8)(balance / divisor);
        if (digit != 0u || started || divisor == 1u) {
            out[index++] = gVegaQolDigits[digit];
            started = 1u;
        }
        balance = (u16)(balance % divisor);
        divisor = (u16)(divisor / 10u);
    }
    out[index] = 0xFFu;
}

static u8 supply_render_menu(u8 task_id)
{
    QolWindowTemplate window;
    u8 first = (u8)(G_SUPPLY_SHOP_STATE->page * SUPPLY_PAGE_SIZE);
    u8 rows = supply_page_rows();
    u8 has_next = (u8)(first + rows < G_SUPPLY_SHOP_STATE->eligible_count);
    u8 menu_count = (u8)(rows + 1u);
    u8 index;
    u8 window_id;
    window.bg = 0u;
    window.tilemap_left = 8u;
    window.tilemap_top = 0u;
    window.width = 21u;
    window.height = (u8)(menu_count * 2u + 4u);
    window.palette_num = 15u;
    window.base_block = FN_GET_STD_WINDOW_BASE_TILE();
    window_id = (u8)FN_ADD_WINDOW(&window);
    if (window_id == SUPPLY_WINDOW_INVALID)
        return 0u;
    G_TASKS[task_id].data[0] = window_id;
    G_SUPPLY_SHOP_STATE->window_id = window_id;
    FN_FILL_WINDOW(window_id, 0x11u);
    FN_DRAW_STD_WINDOW_FRAME(window_id, 0u);
    FN_PUT_WINDOW_TILEMAP(window_id);
    supply_append_balance();
    FN_ADD_TEXT_PRINTER(window_id, 2u,
        G_SUPPLY_SHOP_STATE->balance_text, 8u, 1u, 0u, (void *)0);
    for (index = 0u; index < rows; ++index) {
        u16 catalog_index = G_SUPPLY_SHOP_STATE->eligible[first + index];
        FN_ADD_TEXT_PRINTER(window_id, 2u,
            gVegaQolSupplyMessages[catalog_index],
            8u, (u8)(17u + index * 16u), 0u, (void *)0);
    }
    FN_ADD_TEXT_PRINTER(window_id, 2u,
        has_next ? gVegaQolSupplyNext : gVegaQolSupplyCancel,
        8u, (u8)(17u + rows * 16u), 0u, (void *)0);
    (void)FN_MENU_INIT_CURSOR(window_id, 2u, 0u, 17u, 16u,
                              menu_count, 0u);
    FN_COPY_WINDOW_TO_VRAM(window_id, 3u);
    FN_SCHEDULE_BG_COPY(0u);
    return 1u;
}

static void supply_close_window(u8 task_id)
{
    u8 window_id = (u8)G_TASKS[task_id].data[0];
    if (window_id == SUPPLY_WINDOW_INVALID)
        return;
    FN_CLEAR_STD_WINDOW_FRAME(window_id, 0u);
    FN_REMOVE_WINDOW(window_id);
    FN_SCHEDULE_BG_COPY(0u);
    G_TASKS[task_id].data[0] = SUPPLY_WINDOW_INVALID;
    G_SUPPLY_SHOP_STATE->window_id = SUPPLY_WINDOW_INVALID;
}

static void supply_finish_menu(u8 task_id, u16 catalog_index, u16 result)
{
    supply_close_window(task_id);
    FN_DESTROY_TASK(task_id);
    FN_PLAY_SE(5u);
    G_SUPPLY_SHOP_STATE->last_catalog_index = catalog_index;
    supply_set_result(result);
    FN_ENABLE_BOTH_SCRIPT_CONTEXTS();
}

static void task_handle_supply_shop(u8 task_id)
{
    s8 choice = FN_MENU_PROCESS_INPUT();
    u8 first;
    u8 rows;
    u8 has_next;
    u16 selected;
    if (choice == -2)
        return;
    first = (u8)(G_SUPPLY_SHOP_STATE->page * SUPPLY_PAGE_SIZE);
    rows = supply_page_rows();
    has_next = (u8)(first + rows < G_SUPPLY_SHOP_STATE->eligible_count);
    if (choice < 0) {
        supply_finish_menu(task_id, 0xFFFFu, SUPPLY_RESULT_CANCELLED);
        return;
    }
    if ((u8)choice == rows) {
        if (has_next) {
            supply_close_window(task_id);
            ++G_SUPPLY_SHOP_STATE->page;
            if (!supply_render_menu(task_id))
                supply_finish_menu(task_id, 0xFFFFu,
                                   SUPPLY_RESULT_ENGINE_REJECTED);
        } else {
            supply_finish_menu(task_id, 0xFFFFu, SUPPLY_RESULT_CANCELLED);
        }
        return;
    }
    if ((u8)choice >= rows) {
        supply_finish_menu(task_id, 0xFFFFu, SUPPLY_RESULT_INVALID);
        return;
    }
    selected = G_SUPPLY_SHOP_STATE->eligible[first + (u8)choice];
    supply_finish_menu(task_id, selected, supply_purchase_raw(selected));
}

PUBLIC_TEXT(VegaQolProduction_OpenSupplyShop)
u16 VegaQolProduction_OpenSupplyShop(void)
{
    u16 index;
    u8 task_id;
    if (!ensure_save()) {
        supply_set_result(SUPPLY_RESULT_PERSIST_FAILED);
        return SUPPLY_RESULT_PERSIST_FAILED;
    }
    clear_bytes(G_SUPPLY_SHOP_STATE, sizeof(*G_SUPPLY_SHOP_STATE));
    G_SUPPLY_SHOP_STATE->window_id = SUPPLY_WINDOW_INVALID;
    G_SUPPLY_SHOP_STATE->last_result = SUPPLY_RESULT_NOT_SET;
    G_SUPPLY_SHOP_STATE->last_catalog_index = 0xFFFFu;
    for (index = 0u; index < VEGA_QOL_SUPPLY_CATALOG_COUNT; ++index) {
        if (supply_entry_available(index))
            G_SUPPLY_SHOP_STATE->eligible[
                G_SUPPLY_SHOP_STATE->eligible_count++] = index;
    }
    if (G_SUPPLY_SHOP_STATE->eligible_count == 0u) {
        supply_set_result(SUPPLY_RESULT_LOCKED);
        return SUPPLY_RESULT_LOCKED;
    }
    task_id = FN_CREATE_TASK(task_handle_supply_shop, 0x50u);
    if (task_id >= 16u) {
        supply_set_result(SUPPLY_RESULT_ENGINE_REJECTED);
        return SUPPLY_RESULT_ENGINE_REJECTED;
    }
    G_TASKS[task_id].data[0] = SUPPLY_WINDOW_INVALID;
    if (!supply_render_menu(task_id)) {
        FN_DESTROY_TASK(task_id);
        supply_set_result(SUPPLY_RESULT_ENGINE_REJECTED);
        return SUPPLY_RESULT_ENGINE_REJECTED;
    }
    supply_set_result(SUPPLY_RESULT_BUSY);
    FN_SCRIPT_CONTEXT2_ENABLE();
    return SUPPLY_RESULT_BUSY;
}

PUBLIC_TEXT(VegaQolProduction_PostSupplyShop)
void VegaQolProduction_PostSupplyShop(void)
{
    u16 result = G_SUPPLY_SHOP_STATE->last_result;
    if (result == SUPPLY_RESULT_NOT_SET)
        result = SUPPLY_RESULT_CANCELLED;
    *G_SPECIAL_RESULT = result;
}

static void sync_exp_share_flag(void)
{
    if (gVegaModernSaveData->exp_share_enabled
        && VegaQolProduction_FeatureUnlocked(VEGA_QOL_EXP_SHARE))
        (void)VegaQolProduction_OriginalFlagSet(FLAG_EXP_SHARE);
    else
        (void)VegaQolProduction_OriginalFlagClear(FLAG_EXP_SHARE);
}

static void initialize_exp_share_after_badge(void)
{
    if (!FN_FLAG_GET(FLAG_BADGE_1)
        || FN_FLAG_GET(FLAG_QOL_EXP_SHARE_INITIALIZED)
        || !ensure_save())
        return;
    gVegaModernSaveData->exp_share_enabled = 1u;
    FN_SAVE_FINALIZE(gVegaModernSaveData);
    (void)VegaQolProduction_OriginalFlagSet(FLAG_EXP_SHARE);
    (void)VegaQolProduction_OriginalFlagSet(
        FLAG_QOL_EXP_SHARE_INITIALIZED);
}

PUBLIC_TEXT(VegaQolProduction_FlagSetAdapter)
u8 VegaQolProduction_FlagSetAdapter(u16 flag)
{
    u8 result = VegaQolProduction_OriginalFlagSet(flag);
    if (flag == FLAG_EXP_SHARE && ensure_save()) {
        gVegaModernSaveData->exp_share_enabled = 1u;
        FN_SAVE_FINALIZE(gVegaModernSaveData);
        (void)VegaQolProduction_OriginalFlagSet(
            FLAG_QOL_EXP_SHARE_INITIALIZED);
    } else if (flag == FLAG_BADGE_1) {
        initialize_exp_share_after_badge();
    }
    return result;
}

PUBLIC_TEXT(VegaQolProduction_FlagClearAdapter)
u8 VegaQolProduction_FlagClearAdapter(u16 flag)
{
    u8 result = VegaQolProduction_OriginalFlagClear(flag);
    if (flag == FLAG_EXP_SHARE && ensure_save()) {
        gVegaModernSaveData->exp_share_enabled = 0u;
        FN_SAVE_FINALIZE(gVegaModernSaveData);
        (void)VegaQolProduction_OriginalFlagSet(
            FLAG_QOL_EXP_SHARE_INITIALIZED);
    }
    return result;
}

PUBLIC_TEXT(VegaQolProduction_TrySavingDataAdapter)
u8 VegaQolProduction_TrySavingDataAdapter(u8 save_type)
{
    u8 result;
    if (!ensure_save())
        return 0u;
    FN_SAVE_FINALIZE(gVegaModernSaveData);
    result = VegaQolProduction_OriginalTrySavingData(save_type);
    if (result != 1u)
        return result;
    return supply_persist_sector();
}

PUBLIC_TEXT(VegaQolProduction_SaveLoadAdapter)
u8 VegaQolProduction_SaveLoadAdapter(u8 save_type)
{
    u8 result;
    ensure_state();
    clear_owned_high_raid_pending();
    result = FN_STAGE35_SAVE_LOAD(save_type);
    clear_bytes(G_QOL_STATE, sizeof(*G_QOL_STATE));
    ensure_state();
    if (result == 1u && ensure_save()) {
        if (gVegaModernSaveData->text_speed > VEGA_TEXT_NORMAL)
            gVegaModernSaveData->text_speed = VEGA_TEXT_INSTANT;
        if (gVegaModernSaveData->hatch_mode > VEGA_HATCH_SKIP)
            gVegaModernSaveData->hatch_mode = VEGA_HATCH_FAST;
        gVegaModernSaveData->exp_share_enabled =
            (u8)(gVegaModernSaveData->exp_share_enabled != 0u);
        initialize_exp_share_after_badge();
        sync_exp_share_flag();
        FN_SAVE_FINALIZE(gVegaModernSaveData);
    }
    return result;
}

static VegaQolStatus commit_setting(u8 kind, u8 value)
{
    if (!ensure_save())
        return VEGA_QOL_CORRUPT_SAVE;
    switch (kind) {
    case VEGA_QOL_SERVICE_SET_TEXT_SPEED:
        if (value > VEGA_TEXT_NORMAL)
            return VEGA_QOL_INVALID_ARGUMENT;
        gVegaModernSaveData->text_speed = value;
        break;
    case VEGA_QOL_SERVICE_SET_EXP_SHARE:
        if (value > 1u)
            return VEGA_QOL_INVALID_ARGUMENT;
        if (!VegaQolProduction_FeatureUnlocked(VEGA_QOL_EXP_SHARE))
            return VEGA_QOL_LOCKED;
        gVegaModernSaveData->exp_share_enabled = value;
        (void)VegaQolProduction_OriginalFlagSet(
            FLAG_QOL_EXP_SHARE_INITIALIZED);
        break;
    case VEGA_QOL_SERVICE_SET_HATCH_MODE:
        if (value > VEGA_HATCH_SKIP)
            return VEGA_QOL_INVALID_ARGUMENT;
        gVegaModernSaveData->hatch_mode = value;
        break;
    case VEGA_QOL_SERVICE_SET_RESEARCH_PROFILE:
        if (value > VEGA_PROFILE_RESEARCH)
            return VEGA_QOL_INVALID_ARGUMENT;
        if (!VegaQolProduction_FeatureUnlocked(VEGA_QOL_RESEARCH_PROFILE))
            return VEGA_QOL_LOCKED;
        gVegaModernSaveData->encounter_profile[
            gVegaModernSaveData->current_region < VEGA_REGION_COUNT
                ? gVegaModernSaveData->current_region : 0u] = value;
        break;
    default:
        return VEGA_QOL_INVALID_ARGUMENT;
    }
    FN_SAVE_FINALIZE(gVegaModernSaveData);
    sync_exp_share_flag();
    return VEGA_QOL_OK;
}

PUBLIC_TEXT(VegaQolProduction_ApplyExpCandyQuantityAdapter)
u8 VegaQolProduction_ApplyExpCandyQuantityAdapter(
    void *mon, u16 item, u8 choice, u16 available, void *result)
{
    return FN_APPLY_EXP_CANDY(mon, item, choice, available, result);
}

enum {
    CANDY_TASK_MENU = 10,
    CANDY_TASK_AVAILABLE = 11,
    CANDY_TASK_ITEM = 12,
    CANDY_TASK_RETURN_LO = 14,
    CANDY_TASK_RETURN_HI = 15,
    CANDY_SEQUENCE_ACTIVE = 0xC1,
};

typedef void (*ItemUseCallbackFn)(u8, TaskFunc);

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

enum {
    QUANTITY_SCRATCH_REMAINING = 0,
    QUANTITY_SCRATCH_EXIT_CALLBACK = 4,
    QUANTITY_SCRATCH_RETURN_TASK = 8,
};

/* Party item use and the summary/PSS judge renderer cannot be active at the
 * same time.  Reuse the first 12 bytes of that volatile display buffer for
 * the callbacks which must survive the evolution scene; never alias the PC
 * selection bitset. */
static u32 quantity_scratch_read(u8 offset)
{
    u32 value;
    copy_bytes(&value, &G_QOL_STATE->judge_iv[offset], sizeof(value));
    return value;
}

static void quantity_scratch_write(u8 offset, u32 value)
{
    copy_bytes(&G_QOL_STATE->judge_iv[offset], &value, sizeof(value));
}

static void clear_quantity_scratch(void)
{
    clear_bytes(G_QOL_STATE->judge_iv, 12u);
}

static u16 resolve_quantity(u8 choice, u16 available)
{
    u16 requested;
    if (available == 0u)
        return 0u;
    if (choice == 0u)
        requested = 1u;
    else if (choice == 1u)
        requested = 5u;
    else if (choice == 2u)
        requested = 10u;
    else if (choice == 3u)
        requested = available;
    else
        return 0u;
    return requested < available ? requested : available;
}

static u8 is_exp_candy(u16 item)
{
    return (u8)(item >= 988u && item <= 992u);
}

static u8 is_ev_reset_item(u16 item)
{
    return (u8)(item >= 993u && item <= 998u);
}

static u8 is_ev_gain_item(u16 item)
{
    return (u8)((item >= 63u && item <= 67u) || item == 70u
                || (item >= 386u && item <= 391u));
}

static u8 open_common_quantity_menu(u8 task_id)
{
    QolWindowTemplate window;
    QolListMenuTemplate menu;
    u8 window_id;
    u8 list_task_id;
    clear_bytes(&window, sizeof(window));
    clear_bytes(&menu, sizeof(menu));
    window.bg = 0u;
    window.tilemap_left = 18u;
    window.tilemap_top = 1u;
    window.width = 11u;
    window.height = 10u;
    window.palette_num = 15u;
    window.base_block = FN_GET_STD_WINDOW_BASE_TILE();
    window_id = (u8)FN_ADD_WINDOW(&window);
    if (window_id == 0xFFu)
        return 0u;
    FN_FILL_WINDOW(window_id, 0x11u);
    FN_DRAW_STD_WINDOW_FRAME(window_id, 0u);
    FN_PUT_WINDOW_TILEMAP(window_id);
    menu.items = (const VegaQolGeneratedListItem *)gVegaQolQuantityItems;
    menu.total_items = 4u;
    menu.max_showed = 4u;
    menu.window_id = window_id;
    menu.item_x = 9u;
    menu.cursor_x = 1u;
    menu.cursor_pal = 2u;
    menu.fill_value = 1u;
    menu.cursor_shadow_pal = 3u;
    menu.font_id = 2u;
    list_task_id = FN_LIST_MENU_INIT(&menu, 0u, 0u);
    if (list_task_id == 0xFFu) {
        FN_CLEAR_STD_WINDOW_FRAME(window_id, 0u);
        FN_REMOVE_WINDOW(window_id);
        FN_SCHEDULE_BG_COPY(0u);
        return 0u;
    }
    G_TASKS[task_id].data[CANDY_TASK_MENU] =
        (s16)((u16)window_id | ((u16)list_task_id << 8));
    FN_COPY_WINDOW_TO_VRAM(window_id, 3u);
    FN_SCHEDULE_BG_COPY(0u);
    return 1u;
}

static void close_common_quantity_menu(u8 task_id)
{
    u16 packed = (u16)G_TASKS[task_id].data[CANDY_TASK_MENU];
    u8 window_id = (u8)packed;
    u8 list_task_id = (u8)(packed >> 8);
    u16 cursor = 0u;
    u16 above = 0u;
    FN_LIST_MENU_DESTROY(list_task_id, &cursor, &above);
    FN_CLEAR_STD_WINDOW_FRAME(window_id, 0u);
    FN_REMOVE_WINDOW(window_id);
    FN_SCHEDULE_BG_COPY(0u);
    G_TASKS[task_id].data[CANDY_TASK_MENU] = (s16)0xFFFFu;
}

PUBLIC_TEXT(VegaQolProduction_MonTryLearningNewMoveAdapter)
u16 VegaQolProduction_MonTryLearningNewMoveAdapter(void *mon, u8 first_move)
{
    return FN_ORIGINAL_MON_TRY_LEARNING(mon, first_move);
}

static void candy_continue_task(u8 task_id);
static void candy_after_evolution(void);

static void candy_try_moves_task(u8 task_id)
{
    void *mon;
    u16 result;
    if (FN_PARTY_TEXT_ACTIVE()
        || (G_MAIN_NEW_KEYS & (KEY_A | KEY_B)) == 0u)
        return;
    mon = PTR(u8 *, PLAYER_PARTY)
        + (u32)(u8)G_PARTY_SLOT * VEGA_PARTY_MON_SIZE;
    result = FN_ORIGINAL_MON_TRY_LEARNING(mon, 1u);
    G_PARTY_LEARN_METHOD = 1u;
    if (result == MOVE_NONE) {
        VegaQolProduction_PartyMenuTryEvolutionAdapter(task_id);
    } else if (result == MON_HAS_MAX_MOVES) {
        FN_PARTY_MOVE_NEEDS_REPLACE(task_id);
    } else if (result == MON_ALREADY_KNOWS_MOVE) {
        G_TASKS[task_id].func = PTR(TaskFunc, 0x08126FE5u);
    } else {
        FN_PARTY_MOVE_LEARNED(task_id, result);
    }
}

static void finish_quantity_sequence(u8 task_id, u8 had_effect)
{
    TaskFunc return_task = (TaskFunc)(uintptr_t)
        quantity_scratch_read(QUANTITY_SCRATCH_RETURN_TASK);
    clear_quantity_scratch();
    G_QOL_STATE->relearn_active = 0u;
    G_QOL_STATE->last_result = 0u;
    G_PARTY_USE_EXIT = had_effect;
    (void)FN_DISPLAY_PARTY_MESSAGE(
        had_effect ? gVegaQolQuantityAppliedMessage
                   : gVegaQolCandyNoEffectMessage,
        1u);
    FN_SCHEDULE_BG_COPY(2u);
    G_TASKS[task_id].func = return_task;
}

static void candy_continue_task(u8 task_id)
{
    QolState *state = G_QOL_STATE;
    u8 *mon = PTR(u8 *, PLAYER_PARTY)
        + (u32)state->relearn_position * VEGA_PARTY_MON_SIZE;
    if (state->relearn_position >= *(volatile u8 *)(uintptr_t)PLAYER_PARTY_COUNT
        || FN_GET_MON_DATA(mon, MON_DATA_IS_EGG, (u8 *)0)) {
        finish_quantity_sequence(task_id, state->relearn_index != 0u);
        return;
    }
    for (;;) {
        u16 species = (u16)FN_GET_MON_DATA(
            mon, MON_DATA_SPECIES, (u8 *)0);
        u8 level = (u8)FN_GET_MON_DATA(
            mon, MON_DATA_LEVEL, (u8 *)0);
        u8 cap = FN_EFFECTIVE_LEVEL_CAP();
        u32 current_exp = FN_GET_MON_DATA(mon, MON_DATA_EXP, (u8 *)0);
        u32 cap_exp;
        u32 next_exp;
        u32 target_exp;
        u32 applied;
        u8 crossed_level = 0u;
        if (species == 0u || cap == 0u || level >= cap) {
            state->last_result = 0u;
            finish_quantity_sequence(task_id, state->relearn_index != 0u);
            return;
        }
        cap_exp = FN_GET_SPECIES_EXP(species, cap);
        if (current_exp >= cap_exp) {
            state->last_result = 0u;
            finish_quantity_sequence(task_id, state->relearn_index != 0u);
            return;
        }
        next_exp = FN_GET_SPECIES_EXP(species, (u8)(level + 1u));
        if (quantity_scratch_read(QUANTITY_SCRATCH_REMAINING) == 0u) {
            u32 value;
            if (state->last_result == 0u) {
                finish_quantity_sequence(task_id,
                                         state->relearn_index != 0u);
                return;
            }
            value = state->relearn_move == 68u
                ? next_exp - current_exp : FN_CANDY_VALUE(state->relearn_move);
            if (value == 0u
                || !FN_REMOVE_BAG_ITEM(state->relearn_move, 1u)) {
                finish_quantity_sequence(task_id,
                                         state->relearn_index != 0u);
                return;
            }
            --state->last_result;
            quantity_scratch_write(QUANTITY_SCRATCH_REMAINING, value);
        }
        target_exp = current_exp
            + quantity_scratch_read(QUANTITY_SCRATCH_REMAINING);
        if (target_exp < current_exp || target_exp > cap_exp)
            target_exp = cap_exp;
        if (next_exp > current_exp && target_exp >= next_exp) {
            target_exp = next_exp;
            crossed_level = 1u;
        }
        applied = target_exp - current_exp;
        if (applied == 0u) {
            quantity_scratch_write(QUANTITY_SCRATCH_REMAINING, 0u);
            continue;
        }
        FN_SET_BOX_MON_DATA(mon, MON_DATA_EXP, &target_exp);
        FN_CALCULATE_MON_STATS(mon);
        quantity_scratch_write(
            QUANTITY_SCRATCH_REMAINING,
            quantity_scratch_read(QUANTITY_SCRATCH_REMAINING) - applied);
        state->relearn_index = 1u;
        if (!crossed_level)
            continue;
        (void)FN_UPDATE_PARTY_MON(state->relearn_position, mon);
        (void)FN_DISPLAY_PARTY_MESSAGE(gVegaQolCandyAppliedMessage, 1u);
        FN_SCHEDULE_BG_COPY(2u);
        G_TASKS[task_id].func = candy_try_moves_task;
        return;
    }
}

PUBLIC_TEXT(VegaQolProduction_PartyMenuTryEvolutionAdapter)
void VegaQolProduction_PartyMenuTryEvolutionAdapter(u8 task_id)
{
    QolState *state = G_QOL_STATE;
    u8 *mon;
    u16 target;
    if (state->relearn_active != CANDY_SEQUENCE_ACTIVE) {
        VegaQolProduction_OriginalPartyMenuTryEvolution(task_id);
        return;
    }
    mon = PTR(u8 *, PLAYER_PARTY)
        + (u32)state->relearn_position * VEGA_PARTY_MON_SIZE;
    target = FN_GET_EVOLUTION_TARGET(mon, 0u, 0u);
    if (target == 0u) {
        candy_continue_task(task_id);
        return;
    }
    FN_FREE_PARTY_POINTERS();
    G_AFTER_EVOLUTION = (u32)(uintptr_t)candy_after_evolution;
    FN_BEGIN_EVOLUTION(mon, target, 1u, state->relearn_position);
    FN_DESTROY_TASK(task_id);
}

static void candy_after_evolution(void)
{
    FN_INIT_PARTY_MENU(0u, 0u, 3u, 1u, 127u, candy_continue_task,
        (VoidFn)(uintptr_t)quantity_scratch_read(
            QUANTITY_SCRATCH_EXIT_CALLBACK));
}

static u8 apply_non_level_quantity(u16 item, u16 count)
{
    u8 backup[VEGA_PARTY_MON_SIZE];
    u8 result[32];
    u8 *mon;
    u16 applied = 0u;
    if (G_PARTY_SLOT < 0 || G_PARTY_SLOT >= 6)
        return 0u;
    mon = PTR(u8 *, PLAYER_PARTY)
        + (u32)(u8)G_PARTY_SLOT * VEGA_PARTY_MON_SIZE;
    copy_bytes(backup, mon, sizeof(backup));
    while (applied < count) {
        u8 changed;
        if (is_ev_gain_item(item))
            changed = (u8)!FN_EXECUTE_ITEM_EFFECT((u8)G_PARTY_SLOT,
                                                   item, 0u);
        else if (is_ev_reset_item(item))
            changed = FN_APPLY_EV_RESET_ITEM(mon, item, result);
        else
            break;
        if (!changed)
            break;
        ++applied;
    }
    if (applied == 0u)
        return 0u;
    if (!FN_REMOVE_BAG_ITEM(item, applied)) {
        copy_bytes(mon, backup, sizeof(backup));
        return 0u;
    }
    (void)FN_UPDATE_PARTY_MON((u8)G_PARTY_SLOT, mon);
    return 1u;
}

static void common_quantity_task(u8 task_id)
{
    u16 packed = (u16)G_TASKS[task_id].data[CANDY_TASK_MENU];
    s32 choice = FN_LIST_MENU_INPUT((u8)(packed >> 8));
    if (choice == -1)
        return;
    close_common_quantity_menu(task_id);
    if (choice == -2) {
        G_QOL_STATE->relearn_active = 0u;
        clear_quantity_scratch();
        G_PARTY_USE_EXIT = 0u;
        G_TASKS[task_id].func = task_load_pointer(
            task_id, CANDY_TASK_RETURN_LO);
        return;
    }
    if (choice >= 0 && choice < 4) {
        u16 item = (u16)G_TASKS[task_id].data[CANDY_TASK_ITEM];
        u16 available = (u16)G_TASKS[task_id].data[CANDY_TASK_AVAILABLE];
        u16 count = resolve_quantity((u8)choice, available);
        TaskFunc return_task = task_load_pointer(
            task_id, CANDY_TASK_RETURN_LO);
        if (G_PARTY_SLOT < 0 || G_PARTY_SLOT >= 6)
            goto no_effect;
        if (count == 0u)
            goto no_effect;
        if (item == 68u || is_exp_candy(item)) {
            QolState *state = G_QOL_STATE;
            clear_quantity_scratch();
            quantity_scratch_write(QUANTITY_SCRATCH_EXIT_CALLBACK,
                                   G_PARTY_EXIT_CALLBACK);
            quantity_scratch_write(QUANTITY_SCRATCH_RETURN_TASK,
                                   (u32)(uintptr_t)return_task);
            state->last_result = count;
            state->relearn_move = item;
            state->relearn_position = (u8)G_PARTY_SLOT;
            state->relearn_index = 0u;
            state->relearn_active = CANDY_SEQUENCE_ACTIVE;
            candy_continue_task(task_id);
            return;
        }
        if (!apply_non_level_quantity(item, count))
            goto no_effect;
        G_PARTY_USE_EXIT = 1u;
        (void)FN_DISPLAY_PARTY_MESSAGE(gVegaQolQuantityAppliedMessage, 1u);
        FN_SCHEDULE_BG_COPY(2u);
        G_TASKS[task_id].func = return_task;
        return;
    }
    goto no_effect;

no_effect:
    G_QOL_STATE->relearn_active = 0u;
    clear_quantity_scratch();
    G_PARTY_USE_EXIT = 0u;
    (void)FN_DISPLAY_PARTY_MESSAGE(gVegaQolCandyNoEffectMessage, 1u);
    FN_SCHEDULE_BG_COPY(2u);
    G_TASKS[task_id].func = task_load_pointer(
        task_id, CANDY_TASK_RETURN_LO);
}

static void common_quantity_item_use_callback(u8 task_id,
                                               TaskFunc return_task)
{
    u16 item = G_SPECIAL_ITEM;
    u16 available = 0u;
    ensure_state();
    G_QOL_STATE->relearn_active = 0u;
    clear_quantity_scratch();
    while (available < 999u
           && FN_CHECK_BAG_HAS_ITEM(item, (u16)(available + 1u)))
        ++available;
    G_TASKS[task_id].data[CANDY_TASK_MENU] = (s16)0xFFFFu;
    G_TASKS[task_id].data[CANDY_TASK_AVAILABLE] = (s16)available;
    G_TASKS[task_id].data[CANDY_TASK_ITEM] = (s16)item;
    task_store_pointer(task_id, CANDY_TASK_RETURN_LO, return_task);
    if (open_common_quantity_menu(task_id)) {
        G_TASKS[task_id].func = common_quantity_task;
        return;
    }
    G_PARTY_USE_EXIT = 0u;
    (void)FN_DISPLAY_PARTY_MESSAGE(gVegaQolCandyNoEffectMessage, 1u);
    FN_SCHEDULE_BG_COPY(2u);
    G_TASKS[task_id].func = return_task;
}

PUBLIC_TEXT(VegaQolProduction_FieldUseCommonQuantityAdapter)
void VegaQolProduction_FieldUseCommonQuantityAdapter(u8 task_id)
{
    *(ItemUseCallbackFn *)(uintptr_t)ITEM_USE_CALLBACK =
        common_quantity_item_use_callback;
    FN_SET_UP_ITEM_USE_CALLBACK(task_id);
}

PUBLIC_TEXT(VegaQolProduction_FieldUseExpCandyAdapter)
void VegaQolProduction_FieldUseExpCandyAdapter(u8 task_id)
{
    VegaQolProduction_FieldUseCommonQuantityAdapter(task_id);
}

PUBLIC_TEXT(VegaQolProduction_IsReusableTm)
u8 VegaQolProduction_IsReusableTm(u16 item)
{
    return (u8)(VegaQolProduction_FeatureUnlocked(VEGA_QOL_TM_REUSE_LICENSE)
                && FN_REUSABLE_TM(item));
}

PUBLIC_TEXT(VegaQolProduction_TmHmSymbolAdapter)
u8 VegaQolProduction_TmHmSymbolAdapter(u16 item)
{
    u8 mystery = FN_ITEM_MYSTERY2(item);
    u8 tm_id;
    /* Keep quantities visible for the consumable pre-Hall-of-Fame phase.
     * Quantities remain truthful after the license because old copies are
     * retained and no longer consumed. */
    if (item == 0u)
        return 0u;
    tm_id = mystery == 0u ? (u8)(item - 8u) : (u8)(mystery - 1u);
    return tm_id < 120u ? 1u : 0u;
}

PUBLIC_TEXT(VegaQolProduction_TmSellableAdapter)
u8 VegaQolProduction_TmSellableAdapter(u16 item)
{
    return (u8)(FN_ITEM_PRICE(item) != 0u);
}

PUBLIC_TEXT(VegaQolProduction_TmBagQuantityAdapter)
u8 VegaQolProduction_TmBagQuantityAdapter(u16 item)
{
    (void)item;
    return 0xFFu;
}

static VegaQolStatus hyper_train_party(u8 party_slot, u8 stat,
                                       u8 cancelled)
{
    u8 backup[VEGA_PARTY_MON_SIZE];
    u8 *mon;
    u16 item;
    u16 old_8004;
    u16 old_8005;
    if (cancelled)
        return VEGA_QOL_CANCELLED;
    if (party_slot >= *(volatile u8 *)(uintptr_t)PLAYER_PARTY_COUNT
        || stat > 6u)
        return VEGA_QOL_INVALID_ARGUMENT;
    if (stat == 6u) {
        if (!VegaQolProduction_FeatureUnlocked(VEGA_QOL_EXP_CANDY_XL_GOLD_CAP))
            return VEGA_QOL_LOCKED;
        item = 854u;
    } else {
        if (!VegaQolProduction_FeatureUnlocked(VEGA_QOL_EXP_CANDY_L_SILVER_CAP))
            return VEGA_QOL_LOCKED;
        item = 853u;
    }
    if (!FN_CHECK_BAG_HAS_ITEM(item, 1u))
        return VEGA_QOL_CAPACITY;
    mon = PTR(u8 *, PLAYER_PARTY) + (u32)party_slot * VEGA_PARTY_MON_SIZE;
    if (FN_GET_BOX_MON_DATA(mon, MON_DATA_IS_EGG, (u8 *)0))
        return VEGA_QOL_FORBIDDEN_MON;
    copy_bytes(backup, mon, sizeof(backup));
    old_8004 = *(volatile u16 *)(uintptr_t)SPECIAL_VAR_8004;
    old_8005 = *(volatile u16 *)(uintptr_t)SPECIAL_VAR_8005;
    *(volatile u16 *)(uintptr_t)SPECIAL_VAR_8004 = party_slot;
    *(volatile u16 *)(uintptr_t)SPECIAL_VAR_8005 = stat;
    if (!FN_HYPER_TRAINING()) {
        *(volatile u16 *)(uintptr_t)SPECIAL_VAR_8004 = old_8004;
        *(volatile u16 *)(uintptr_t)SPECIAL_VAR_8005 = old_8005;
        return VEGA_QOL_EFFECTLESS;
    }
    *(volatile u16 *)(uintptr_t)SPECIAL_VAR_8004 = old_8004;
    *(volatile u16 *)(uintptr_t)SPECIAL_VAR_8005 = old_8005;
    if (!FN_REMOVE_BAG_ITEM(item, 1u)) {
        copy_bytes(mon, backup, sizeof(backup));
        return VEGA_QOL_CAPACITY;
    }
    return VEGA_QOL_OK;
}

static VegaQolStatus ev_reset_all_party(u8 party_slot, u8 cancelled)
{
    u8 backup[VEGA_PARTY_MON_SIZE];
    u8 result[32];
    u8 *mon;
    if (cancelled)
        return VEGA_QOL_CANCELLED;
    if (!VegaQolProduction_FeatureUnlocked(VEGA_QOL_EV_RESET_ALL))
        return VEGA_QOL_LOCKED;
    if (party_slot >= *(volatile u8 *)(uintptr_t)PLAYER_PARTY_COUNT)
        return VEGA_QOL_INVALID_ARGUMENT;
    mon = PTR(u8 *, PLAYER_PARTY) + (u32)party_slot * VEGA_PARTY_MON_SIZE;
    if (FN_GET_BOX_MON_DATA(mon, MON_DATA_IS_EGG, (u8 *)0))
        return VEGA_QOL_FORBIDDEN_MON;
    copy_bytes(backup, mon, sizeof(backup));
    if (!FN_APPLY_EV_RESET_ALL(mon, result))
        return VEGA_QOL_EFFECTLESS;
    return VEGA_QOL_OK;
}

static VegaQolStatus set_daycare_quest(u8 value)
{
    VegaQolStatus reward_status;
    if (value > 1u)
        return VEGA_QOL_INVALID_ARGUMENT;
    if (!ensure_save())
        return VEGA_QOL_CORRUPT_SAVE;
    if (value && (!kanto_access() || !gVegaModernSaveData->kanto_visited))
        return VEGA_QOL_LOCKED;
    if (value) {
        reward_status = claim_daycare_set_raw();
        if (reward_status != VEGA_QOL_OK
            && reward_status != VEGA_QOL_ALREADY_CLAIMED)
            return reward_status;
        FN_FLAG_SET(FLAG_QOL_DAYCARE_QUEST);
    } else {
        FN_FLAG_CLEAR(FLAG_QOL_DAYCARE_QUEST);
        FN_FLAG_CLEAR(FLAG_QOL_EGG_BASKET);
        *(volatile u16 *)(uintptr_t)QOL_BASKET_COUNTER = 0u;
    }
    return VEGA_QOL_OK;
}

static VegaQolStatus set_egg_basket(u8 value)
{
    u8 old;
    u16 old_counter;
    if (value > 1u)
        return VEGA_QOL_INVALID_ARGUMENT;
    if (!ensure_save())
        return VEGA_QOL_CORRUPT_SAVE;
    if (value && !kanto_daycare_quest())
        return VEGA_QOL_LOCKED;
    old = FN_FLAG_GET(FLAG_QOL_EGG_BASKET);
    old_counter = *(volatile u16 *)(uintptr_t)QOL_BASKET_COUNTER;
    if (value)
        FN_FLAG_SET(FLAG_QOL_EGG_BASKET);
    else
        FN_FLAG_CLEAR(FLAG_QOL_EGG_BASKET);
    *(volatile u16 *)(uintptr_t)QOL_BASKET_COUNTER = 0u;
    (void)old;
    (void)old_counter;
    return VEGA_QOL_OK;
}

static u32 selection_count(void)
{
    QolState *state = G_QOL_STATE;
    u32 count = 0u;
    u8 box;
    for (box = 0u; box < VEGA_QOL_BOX_COUNT; ++box) {
        u32 mask = state->selection[box] & 0x3FFFFFFFu;
        while (mask != 0u) {
            count += mask & 1u;
            mask >>= 1;
        }
    }
    return count;
}

static void clear_selection(void)
{
    u8 box;
    for (box = 0u; box < VEGA_QOL_BOX_COUNT; ++box)
        G_QOL_STATE->selection[box] = 0u;
}

static u8 selection_valid(u8 box, u8 slot)
{
    return (u8)(box < VEGA_QOL_BOX_COUNT && slot < VEGA_QOL_BOX_CAPACITY);
}

static VegaQolStatus toggle_selection(u8 box, u8 slot)
{
    if (!selection_valid(box, slot))
        return VEGA_QOL_INVALID_ARGUMENT;
    if (FN_GET_BOX_MON_DATA_AT(box, slot, MON_DATA_SPECIES) == 0u)
        return VEGA_QOL_EFFECTLESS;
    G_QOL_STATE->selection[box] ^= (u32)1u << slot;
    return VEGA_QOL_OK;
}

static const BaseStatsView *base_stats(u16 species)
{
    if (species == 0u || species >= 1621u)
        return (const BaseStatsView *)0;
    return &PTR(const BaseStatsView *, 0x09600000u)[species];
}

static u16 mon_ability(void *mon, u16 species)
{
    return base_stats(species) == (const BaseStatsView *)0
        ? 0u : FN_GET_MON_ABILITY(mon);
}

static u8 game_string_equal(const u8 *left, const u8 *right, u8 limit)
{
    u8 index;
    for (index = 0u; index < limit; ++index) {
        if (left[index] != right[index])
            return 0u;
        if (left[index] == 0xFFu)
            return 1u;
    }
    return 1u;
}

static u8 filter_matches(void *mon, const VegaQolSearchFilter *filter)
{
    u16 species = (u16)FN_GET_BOX_MON_DATA(mon, MON_DATA_SPECIES, (u8 *)0);
    const BaseStatsView *stats;
    u8 nickname[11];
    if (species == 0u)
        return 0u;
    stats = base_stats(species);
    if (filter->modes & VEGA_QOL_SEARCH_NAME) {
        clear_bytes(nickname, sizeof(nickname));
        FN_GET_BOX_MON_DATA(mon, MON_DATA_NICKNAME, nickname);
        if (!game_string_equal(nickname, filter->nickname, 10u))
            return 0u;
    }
    if (filter->modes & VEGA_QOL_SEARCH_TYPE) {
        if (stats == (const BaseStatsView *)0
            || (stats->type1 != filter->type_id
                && stats->type2 != filter->type_id))
            return 0u;
    }
    if ((filter->modes & VEGA_QOL_SEARCH_ABILITY)
        && mon_ability(mon, species) != filter->ability_id)
        return 0u;
    return 1u;
}

static VegaQolStatus search_and_select(const VegaQolSearchFilter *filter)
{
    u8 mon[VEGA_PARTY_MON_SIZE];
    u8 box;
    u8 slot;
    u32 found = 0u;
    if (filter == (const VegaQolSearchFilter *)0
        || filter->modes == 0u
        || (filter->modes & ~(VEGA_QOL_SEARCH_NAME
                              | VEGA_QOL_SEARCH_TYPE
                              | VEGA_QOL_SEARCH_ABILITY)) != 0u)
        return VEGA_QOL_INVALID_ARGUMENT;
    clear_selection();
    for (box = 0u; box < VEGA_QOL_BOX_COUNT; ++box) {
        for (slot = 0u; slot < VEGA_QOL_BOX_CAPACITY; ++slot) {
            if (FN_GET_BOX_MON_DATA_AT(box, slot, MON_DATA_SPECIES) == 0u)
                continue;
            FN_BOX_MON_AT_TO_MON(box, slot, mon);
            if (filter_matches(mon, filter)) {
                G_QOL_STATE->selection[box] |= (u32)1u << slot;
                ++found;
            }
        }
    }
    return found != 0u ? VEGA_QOL_OK : VEGA_QOL_EFFECTLESS;
}

static VegaQolStatus move_selection(u8 destination_box, u8 cancelled)
{
    u8 box;
    u8 slot;
    u8 free_slots[VEGA_QOL_BOX_CAPACITY];
    u8 free_count = 0u;
    u16 needed = 0u;
    u8 destination_index = 0u;
    if (cancelled)
        return VEGA_QOL_CANCELLED;
    if (destination_box >= VEGA_QOL_BOX_COUNT)
        return VEGA_QOL_INVALID_ARGUMENT;
    for (slot = 0u; slot < VEGA_QOL_BOX_CAPACITY; ++slot) {
        if (FN_GET_BOX_MON_DATA_AT(destination_box, slot,
                                   MON_DATA_SPECIES) == 0u)
            free_slots[free_count++] = slot;
    }
    for (box = 0u; box < VEGA_QOL_BOX_COUNT; ++box) {
        if (box == destination_box)
            continue;
        for (slot = 0u; slot < VEGA_QOL_BOX_CAPACITY; ++slot) {
            if ((G_QOL_STATE->selection[box] & ((u32)1u << slot))
                && FN_GET_BOX_MON_DATA_AT(box, slot, MON_DATA_SPECIES) != 0u)
                ++needed;
        }
    }
    if (needed == 0u)
        return VEGA_QOL_EMPTY_SELECTION;
    if (free_count < needed)
        return VEGA_QOL_CAPACITY;
    for (box = 0u; box < VEGA_QOL_BOX_COUNT; ++box) {
        if (box == destination_box)
            continue;
        for (slot = 0u; slot < VEGA_QOL_BOX_CAPACITY; ++slot) {
            void *mon;
            if ((G_QOL_STATE->selection[box] & ((u32)1u << slot)) == 0u)
                continue;
            mon = FN_GET_BOXED_MON(box, slot);
            if (mon == (void *)0
                || FN_GET_BOX_MON_DATA(mon, MON_DATA_SPECIES, (u8 *)0) == 0u)
                continue;
            FN_SET_BOX_MON_AT(destination_box,
                              free_slots[destination_index++], mon);
            FN_ZERO_BOX_MON_AT(box, slot);
        }
    }
    clear_selection();
    return VEGA_QOL_OK;
}

static u8 item_forbidden(u16 item)
{
    if (item == 0u)
        return 0u;
    return (u8)(FN_IS_MAIL(item) || FN_GET_POCKET(item) == 2u);
}

static u8 mon_release_forbidden(void *mon)
{
    u16 species = (u16)FN_GET_BOX_MON_DATA(mon, MON_DATA_SPECIES, (u8 *)0);
    u16 index;
    if (FN_GET_BOX_MON_DATA(mon, MON_DATA_IS_EGG, (u8 *)0)
        || FN_GET_BOX_MON_DATA(mon, MON_DATA_SANITY_IS_BAD_EGG, (u8 *)0)
        || FN_GET_BOX_MON_DATA(mon, MON_DATA_FATEFUL_ENCOUNTER, (u8 *)0))
        return 1u;
    for (index = 0u; index < VEGA_QOL_PROTECTED_SPECIES_COUNT; ++index) {
        if (gVegaQolProtectedSpecies[index] == species)
            return 1u;
    }
    return 0u;
}

static u8 mon_knows_move(void *mon, u16 move)
{
    u8 slot;
    if (mon == (void *)0)
        return 0u;
    for (slot = 0u; slot < 4u; ++slot) {
        if (FN_GET_BOX_MON_DATA(mon, MON_DATA_MOVE1 + slot, (u8 *)0) == move)
            return 1u;
    }
    return 0u;
}

static u8 selected_has_move(u16 move)
{
    u8 box;
    u8 slot;
    for (box = 0u; box < VEGA_QOL_BOX_COUNT; ++box) {
        for (slot = 0u; slot < VEGA_QOL_BOX_CAPACITY; ++slot) {
            if ((G_QOL_STATE->selection[box] & ((u32)1u << slot))
                && mon_knows_move(FN_GET_BOXED_MON(box, slot), move))
                return 1u;
        }
    }
    return 0u;
}

static u8 unselected_has_move(u16 move)
{
    u8 box;
    u8 slot;
    u8 party_count = *(volatile u8 *)(uintptr_t)PLAYER_PARTY_COUNT;
    for (slot = 0u; slot < party_count && slot < VEGA_PARTY_CAPACITY; ++slot) {
        if (mon_knows_move(PTR(u8 *, PLAYER_PARTY)
                           + (u32)slot * VEGA_PARTY_MON_SIZE, move))
            return 1u;
    }
    for (box = 0u; box < VEGA_QOL_BOX_COUNT; ++box) {
        for (slot = 0u; slot < VEGA_QOL_BOX_CAPACITY; ++slot) {
            if ((G_QOL_STATE->selection[box] & ((u32)1u << slot)) == 0u
                && FN_GET_BOX_MON_DATA_AT(box, slot, MON_DATA_SPECIES) != 0u
                && mon_knows_move(FN_GET_BOXED_MON(box, slot), move))
                return 1u;
        }
    }
    return 0u;
}

static u8 item_seen_before(u8 limit_box, u8 limit_slot, u16 item)
{
    u8 box;
    u8 slot;
    for (box = 0u; box <= limit_box; ++box) {
        u8 end = box == limit_box ? limit_slot : VEGA_QOL_BOX_CAPACITY;
        for (slot = 0u; slot < end; ++slot) {
            void *mon;
            if ((G_QOL_STATE->selection[box] & ((u32)1u << slot)) == 0u)
                continue;
            mon = FN_GET_BOXED_MON(box, slot);
            if (mon != (void *)0
                && FN_GET_BOX_MON_DATA(mon, MON_DATA_HELD_ITEM, (u8 *)0)
                   == item)
                return 1u;
        }
    }
    return 0u;
}

static u16 selected_item_count(u16 item)
{
    u16 count = 0u;
    u8 box;
    u8 slot;
    for (box = 0u; box < VEGA_QOL_BOX_COUNT; ++box) {
        for (slot = 0u; slot < VEGA_QOL_BOX_CAPACITY; ++slot) {
            void *mon;
            if ((G_QOL_STATE->selection[box] & ((u32)1u << slot)) == 0u)
                continue;
            mon = FN_GET_BOXED_MON(box, slot);
            if (mon != (void *)0
                && FN_GET_BOX_MON_DATA(mon, MON_DATA_HELD_ITEM, (u8 *)0)
                   == item)
                ++count;
        }
    }
    return count;
}

static VegaQolStatus items_then_mutate(u8 release, u8 cancelled)
{
    u16 selected_count = 0u;
    u16 item_count = 0u;
    u16 added = 0u;
    u8 box;
    u8 slot;
    if (cancelled)
        return VEGA_QOL_CANCELLED;
    for (box = 0u; box < VEGA_QOL_BOX_COUNT; ++box) {
        for (slot = 0u; slot < VEGA_QOL_BOX_CAPACITY; ++slot) {
            void *mon;
            u16 item;
            if ((G_QOL_STATE->selection[box] & ((u32)1u << slot)) == 0u)
                continue;
            mon = FN_GET_BOXED_MON(box, slot);
            if (mon == (void *)0
                || FN_GET_BOX_MON_DATA(mon, MON_DATA_SPECIES, (u8 *)0) == 0u)
                continue;
            if (release && mon_release_forbidden(mon))
                return VEGA_QOL_FORBIDDEN_MON;
            item = (u16)FN_GET_BOX_MON_DATA(mon, MON_DATA_HELD_ITEM, (u8 *)0);
            if (item_forbidden(item))
                return VEGA_QOL_FORBIDDEN_ITEM;
            ++selected_count;
            if (item != 0u)
                ++item_count;
        }
    }
    if (selected_count == 0u)
        return VEGA_QOL_EMPTY_SELECTION;
    if (!release && item_count == 0u)
        return VEGA_QOL_EFFECTLESS;
    if (!release && item_count != 0u
        && !VegaQolProduction_FeatureUnlocked(VEGA_QOL_PC_HELD_ITEM_BULK))
        return VEGA_QOL_LOCKED;
    if (release) {
        if ((selected_has_move(57u) && !unselected_has_move(57u))
            || (selected_has_move(291u) && !unselected_has_move(291u)))
            return VEGA_QOL_FORBIDDEN_MON;
    }
    for (box = 0u; box < VEGA_QOL_BOX_COUNT; ++box) {
        for (slot = 0u; slot < VEGA_QOL_BOX_CAPACITY; ++slot) {
            void *mon;
            u16 item;
            if ((G_QOL_STATE->selection[box] & ((u32)1u << slot)) == 0u)
                continue;
            mon = FN_GET_BOXED_MON(box, slot);
            if (mon == (void *)0)
                continue;
            item = (u16)FN_GET_BOX_MON_DATA(mon, MON_DATA_HELD_ITEM, (u8 *)0);
            if (item != 0u && !item_seen_before(box, slot, item)
                && !FN_CHECK_BAG_SPACE(item, selected_item_count(item)))
                return VEGA_QOL_CAPACITY;
        }
    }
    for (box = 0u; box < VEGA_QOL_BOX_COUNT; ++box) {
        for (slot = 0u; slot < VEGA_QOL_BOX_CAPACITY; ++slot) {
            void *mon;
            u16 item;
            if ((G_QOL_STATE->selection[box] & ((u32)1u << slot)) == 0u)
                continue;
            mon = FN_GET_BOXED_MON(box, slot);
            if (mon == (void *)0
                || FN_GET_BOX_MON_DATA(mon, MON_DATA_SPECIES, (u8 *)0) == 0u)
                continue;
            item = (u16)FN_GET_BOX_MON_DATA(mon, MON_DATA_HELD_ITEM, (u8 *)0);
            if (item != 0u) {
                if (!FN_ADD_BAG_ITEM(item, 1u))
                    goto rollback_bag;
                ++added;
            }
        }
    }
    for (box = 0u; box < VEGA_QOL_BOX_COUNT; ++box) {
        for (slot = 0u; slot < VEGA_QOL_BOX_CAPACITY; ++slot) {
            void *mon;
            if ((G_QOL_STATE->selection[box] & ((u32)1u << slot)) == 0u)
                continue;
            mon = FN_GET_BOXED_MON(box, slot);
            if (mon == (void *)0
                || FN_GET_BOX_MON_DATA(mon, MON_DATA_SPECIES, (u8 *)0) == 0u)
                continue;
            if (release)
                FN_ZERO_BOX_MON_AT(box, slot);
            else {
                u16 none = 0u;
                FN_SET_BOX_MON_DATA(mon, MON_DATA_HELD_ITEM, &none);
                /* GetBoxedMonPtr expands into gDisposableBoxMon.  Persist the
                 * edited image explicitly or the bag addition would duplicate
                 * the held item on the next decompression. */
                FN_SET_BOX_MON_AT(box, slot, mon);
            }
        }
    }
    clear_selection();
    return VEGA_QOL_OK;

rollback_bag:
    for (box = 0u; box < VEGA_QOL_BOX_COUNT && added != 0u; ++box) {
        for (slot = 0u; slot < VEGA_QOL_BOX_CAPACITY && added != 0u; ++slot) {
            void *mon;
            u16 item;
            if ((G_QOL_STATE->selection[box] & ((u32)1u << slot)) == 0u)
                continue;
            mon = FN_GET_BOXED_MON(box, slot);
            if (mon == (void *)0)
                continue;
            item = (u16)FN_GET_BOX_MON_DATA(mon, MON_DATA_HELD_ITEM, (u8 *)0);
            if (item != 0u) {
                (void)FN_REMOVE_BAG_ITEM(item, 1u);
                --added;
            }
        }
    }
    return VEGA_QOL_CAPACITY;
}

static VegaQolStatus relearn_move(u8 box, u8 slot, u8 move_slot,
                                  u16 move, u8 cancelled)
{
    u8 mon[VEGA_PARTY_MON_SIZE];
    u16 pool[64];
    u8 count;
    u8 index;
    if (cancelled)
        return VEGA_QOL_CANCELLED;
    if (!VegaQolProduction_FeatureUnlocked(VEGA_QOL_PC_MOVE_EDIT))
        return VEGA_QOL_LOCKED;
    if (!selection_valid(box, slot) || move_slot >= 4u || move == 0u)
        return VEGA_QOL_INVALID_ARGUMENT;
    if (FN_GET_BOX_MON_DATA_AT(box, slot, MON_DATA_SPECIES) == 0u)
        return VEGA_QOL_INVALID_ARGUMENT;
    FN_BOX_MON_AT_TO_MON(box, slot, mon);
    if (FN_GET_BOX_MON_DATA(mon, MON_DATA_IS_EGG, (u8 *)0))
        return VEGA_QOL_FORBIDDEN_MON;
    if (FN_GET_BOX_MON_DATA(mon, MON_DATA_MOVE1 + move_slot, (u8 *)0) == move)
        return VEGA_QOL_EFFECTLESS;
    *(volatile u8 *)(uintptr_t)MOVE_MANAGER_MODE = 0u;
    count = FN_MOVE_RELEARN_POOL(mon, pool);
    for (index = 0u; index < count && index < 64u; ++index) {
        if (pool[index] == move)
            break;
    }
    if (index >= count || index >= 64u)
        return VEGA_QOL_MOVE_NOT_IN_POOL;
    if (FN_CALCULATE_PP(move, 0u, move_slot) == 0u)
        return VEGA_QOL_INVALID_ARGUMENT;
    FN_REMOVE_MON_PP_BONUS(mon, move_slot);
    FN_SET_MON_MOVE_SLOT(mon, move, move_slot);
    FN_SET_BOX_MON_AT(box, slot, mon);
    return VEGA_QOL_OK;
}

static u8 map_allowed(u8 group, u8 number)
{
    u16 index;
    for (index = 0u; index < VEGA_QOL_FIELD_PC_MAP_COUNT; ++index) {
        if (gVegaQolFieldPcMaps[index].group == group
            && gVegaQolFieldPcMaps[index].number == number)
            return 1u;
    }
    return 0u;
}

static VegaQolStatus field_map_context_allowed(u8 group, u8 number,
                                                u8 panel_owned)
{
    if (G_MAIN_CALLBACK2 != OVERWORLD_CALLBACK || G_BATTLE_FLAGS != 0u
        || FN_IN_UNION_ROOM() || FN_LINK_STATE_ACTIVE()
        || FN_GET_SAFARI_ZONE_FLAG())
        return VEGA_QOL_CONTEXT_FORBIDDEN;
    if (FN_SCRIPT_CONTEXT_ENABLED() && !panel_owned)
        return VEGA_QOL_CONTEXT_FORBIDDEN;
    return map_allowed(group, number)
        ? VEGA_QOL_OK : VEGA_QOL_CONTEXT_FORBIDDEN;
}

static VegaQolStatus field_pc_allowed(u8 group, u8 number)
{
    u8 panel_owned;
    if (!VegaQolProduction_FeatureUnlocked(VEGA_QOL_FIELD_PC))
        return VEGA_QOL_LOCKED;
    panel_owned = (u8)(G_QOL_STATE->panel_active
        && G_START_MENU_CALLBACK
           == ((u32)(uintptr_t)VegaQolProduction_StartMenuPanel | 1u));
    return field_map_context_allowed(group, number, panel_owned);
}

static VegaQolStatus claim_egg_queue(u8 cancelled)
{
    u8 boxes[VEGA_EGG_QUEUE_CAPACITY];
    u8 slots[VEGA_EGG_QUEUE_CAPACITY];
    u8 needed;
    u8 found = 0u;
    u8 box;
    u8 slot;
    u8 index;
    if (cancelled)
        return VEGA_QOL_CANCELLED;
    if (!VegaQolProduction_FeatureUnlocked(VEGA_QOL_EGG_PC_TRANSFER))
        return VEGA_QOL_LOCKED;
    if (!ensure_save())
        return VEGA_QOL_CORRUPT_SAVE;
    if (gVegaModernSaveData->egg_queue_count == 0u)
        return VEGA_QOL_EFFECTLESS;
    needed = gVegaModernSaveData->egg_queue_count;
    for (box = 0u; box < VEGA_QOL_BOX_COUNT && found < needed; ++box) {
        for (slot = 0u; slot < VEGA_QOL_BOX_CAPACITY && found < needed;
             ++slot) {
            if (FN_GET_BOX_MON_DATA_AT(box, slot, MON_DATA_SPECIES) == 0u) {
                boxes[found] = box;
                slots[found] = slot;
                ++found;
            }
        }
    }
    if (found != needed)
        return VEGA_QOL_CAPACITY;
    copy_bytes(gVegaSaveRollbackData, gVegaModernSaveData,
               VEGA_SAVE_LEDGER_SIZE);
    for (index = 0u; index < needed; ++index) {
        u8 head = gVegaModernSaveData->egg_queue_head;
        FN_SET_BOX_MON_AT(boxes[index], slots[index],
                          gVegaModernSaveData->egg_queue[head]);
        clear_bytes(gVegaModernSaveData->egg_queue[head], VEGA_BOX_MON_SIZE);
        gVegaModernSaveData->egg_queue_head =
            (u8)((head + 1u) % VEGA_EGG_QUEUE_CAPACITY);
        --gVegaModernSaveData->egg_queue_count;
    }
    gVegaModernSaveData->egg_queue_head = 0u;
    FN_SAVE_FINALIZE(gVegaModernSaveData);
    if (!persist_cross_store()) {
        for (index = 0u; index < needed; ++index)
            FN_ZERO_BOX_MON_AT(boxes[index], slots[index]);
        copy_bytes(gVegaModernSaveData, gVegaSaveRollbackData,
                   VEGA_SAVE_LEDGER_SIZE);
        compensate_cross_store();
        return VEGA_QOL_PERSIST_FAILED;
    }
    return VEGA_QOL_OK;
}

static u8 research_profile_enabled(void)
{
    u8 region;
    if (!ensure_save()
        || !VegaQolProduction_FeatureUnlocked(VEGA_QOL_RESEARCH_PROFILE))
        return 0u;
    region = gVegaModernSaveData->current_region < VEGA_REGION_COUNT
        ? gVegaModernSaveData->current_region : 0u;
    return (u8)(gVegaModernSaveData->encounter_profile[region]
                == VEGA_PROFILE_RESEARCH);
}

static u8 research_rule_unlocked(u8 unlock)
{
    switch (unlock) {
    case VEGA_RESEARCH_UNLOCK_GAME_START:
        return 1u;
    case VEGA_RESEARCH_UNLOCK_BADGE_1:
        return FN_FLAG_GET(FLAG_BADGE_1);
    case VEGA_RESEARCH_UNLOCK_BADGE_2:
        return FN_FLAG_GET(FLAG_BADGE_2);
    case VEGA_RESEARCH_UNLOCK_BADGE_3:
        return FN_FLAG_GET(FLAG_BADGE_3);
    case VEGA_RESEARCH_UNLOCK_BADGE_5:
        return FN_FLAG_GET(FLAG_BADGE_5);
    case VEGA_RESEARCH_UNLOCK_BADGE_6:
        return FN_FLAG_GET(FLAG_BADGE_6);
    case VEGA_RESEARCH_UNLOCK_BADGE_7:
        return FN_FLAG_GET(FLAG_BADGE_7);
    case VEGA_RESEARCH_UNLOCK_BADGE_8:
        return FN_FLAG_GET(FLAG_BADGE_8);
    case VEGA_RESEARCH_UNLOCK_HALL_OF_FAME:
        return hall_of_fame();
    case VEGA_RESEARCH_UNLOCK_KANTO:
        return kanto_access();
    case VEGA_RESEARCH_UNLOCK_CERT_1:
    case VEGA_RESEARCH_UNLOCK_CERT_2:
    case VEGA_RESEARCH_UNLOCK_CERT_3:
    case VEGA_RESEARCH_UNLOCK_CERT_4:
    case VEGA_RESEARCH_UNLOCK_CERT_5:
    case VEGA_RESEARCH_UNLOCK_CERT_6:
        return (u8)(popcount8(gVegaModernSaveData->kanto_certifications)
            >= unlock - VEGA_RESEARCH_UNLOCK_CERT_1 + 1u);
    case VEGA_RESEARCH_UNLOCK_KANTO_LEAGUE:
        return gVegaModernSaveData->league_ii_cleared;
    default:
        return 0u;
    }
}

static u8 shiny_pid_matches(u32 ot_id, u32 personality)
{
    return (u8)(((ot_id & 0xFFFFu) ^ (ot_id >> 16)
        ^ (personality & 0xFFFFu) ^ (personality >> 16)) < 8u);
}

static void apply_research_profile(u8 force_research)
{
    u8 *save;
    const VegaQolResearchRule *rule = (const VegaQolResearchRule *)0;
    u16 eligible = 0u;
    u16 pick;
    u16 index;
    u16 held;
    u16 egg_moves[50];
    u8 egg_move_count;
    u8 stat;
    u8 level;
    u32 ot_id;
    u32 pid;
    void *mon = PTR(void *, ENEMY_PARTY);
    if (!research_profile_enabled())
        return;
    save = (u8 *)save_block1();
    if (save == (u8 *)0)
        return;
    pid = FN_GET_BOX_MON_DATA(mon, MON_DATA_PERSONALITY, (u8 *)0);
    ot_id = FN_GET_BOX_MON_DATA(mon, MON_DATA_OT_ID, (u8 *)0);
    for (index = 0u; index < VEGA_QOL_RESEARCH_RULE_COUNT; ++index) {
        const VegaQolResearchRule *candidate = &gVegaQolResearchRules[index];
        if (candidate->group == save[SAVE_LOCATION_OFFSET]
            && candidate->map == save[SAVE_LOCATION_OFFSET + 1u]
            && research_rule_unlocked(candidate->unlock))
            ++eligible;
    }
    if (eligible == 0u)
        return;
    pick = (u16)(pid % eligible);
    for (index = 0u; index < VEGA_QOL_RESEARCH_RULE_COUNT; ++index) {
        const VegaQolResearchRule *candidate = &gVegaQolResearchRules[index];
        if (candidate->group != save[SAVE_LOCATION_OFFSET]
            || candidate->map != save[SAVE_LOCATION_OFFSET + 1u]
            || !research_rule_unlocked(candidate->unlock))
            continue;
        if (pick-- == 0u) {
            rule = candidate;
            break;
        }
    }
    if (rule == (const VegaQolResearchRule *)0)
        return;
    /* Authored rows explicitly preserve the original table.  Ordinary
     * RESEARCH encounters therefore use a deterministic 25% extra slot;
     * the radar's explicit hidden scan requests the authored slot directly. */
    if (!force_research && rule->normal_preserved && (pid & 3u) != 0u)
        return;
    /* MINOR_BONUS_NO_CHAIN_LEAK: keep the original personality (and thus the
     * original wild shiny result), then test exactly one additional random
     * personality.  No chain state is read or written and NORMAL never
     * enters this path. */
    if (rule->shiny_rolls > 1u && !shiny_pid_matches(ot_id, pid)) {
        u32 candidate = ((u32)FN_RANDOM() << 16) | FN_RANDOM();
        if (shiny_pid_matches(ot_id, candidate))
            pid = candidate;
    }
    level = (u8)(rule->level_min
        + ((pid >> 16) % (u32)(rule->level_max - rule->level_min + 1u)));
    FN_CREATE_MON(mon, rule->species, level, 0x20u, 1u, pid, 0u, 0u);
    for (stat = 0u; stat < 6u; ++stat) {
        u8 value = (u8)FN_GET_BOX_MON_DATA(mon, MON_DATA_HP_IV + stat,
                                           (u8 *)0);
        if (value < rule->iv_floor)
            FN_SET_BOX_MON_DATA(mon, MON_DATA_HP_IV + stat, &rule->iv_floor);
    }
    if ((pid >> 8) % 100u < rule->hidden_ability_rate)
        PTR(u8 *, mon)[71u] |= 0x10u;
    held = 0u;
    if ((pid >> 24) % 100u < rule->held_item_rate) {
        const BaseStatsView *stats = base_stats(rule->species);
        if (stats != (const BaseStatsView *)0)
            held = stats->item2 != 0u ? stats->item2 : stats->item1;
        if (held != 0u)
            FN_SET_BOX_MON_DATA(mon, MON_DATA_HELD_ITEM, &held);
    }
    egg_move_count = FN_GET_ALL_EGG_MOVES(mon, egg_moves, 1u);
    if (egg_move_count != 0u) {
        FN_REMOVE_MON_PP_BONUS(mon, 3u);
        FN_SET_MON_MOVE_SLOT(mon, egg_moves[pid % egg_move_count], 3u);
    }
    FN_CALCULATE_MON_STATS(mon);
}

static void arm_random_wild_token(void)
{
    ensure_state();
    G_QOL_STATE->wild_token_pid = FN_GET_BOX_MON_DATA(
        PTR(void *, ENEMY_PARTY), MON_DATA_PERSONALITY, (u8 *)0);
    G_QOL_STATE->wild_token_armed = 1u;
}

PUBLIC_TEXT(VegaQolProduction_TryGenerateWildMonAdapter)
u8 VegaQolProduction_TryGenerateWildMonAdapter(const void *info, u8 area,
                                                u8 flags)
{
    u8 result;
    ensure_state();
    G_QOL_STATE->wild_token_armed = 0u;
    result = FN_WILD_GENERATE(info, area, flags);
    if (result) {
        apply_research_profile(0u);
        arm_random_wild_token();
    }
    return result;
}

PUBLIC_TEXT(VegaQolProduction_GenerateFishingEncounterAdapter)
u16 VegaQolProduction_GenerateFishingEncounterAdapter(const void *info, u8 rod)
{
    u16 species;
    ensure_state();
    G_QOL_STATE->wild_token_armed = 0u;
    species = FN_FISHING_GENERATE(info, rod);
    if (species != 0u) {
        apply_research_profile(0u);
        arm_random_wild_token();
    }
    return species;
}

PUBLIC_TEXT(VegaQolProduction_TryHiddenEncounterAdapter)
u8 VegaQolProduction_TryHiddenEncounterAdapter(void)
{
    u32 selected = FN_ECOLOGY_SELECT(0u, 1u, 4u, 2u, 1u);
    u16 species = (u16)selected;
    u8 level = (u8)(selected >> 16);
    u8 hit = (u8)(selected >> 24);
    if (!hit || species == 0u)
        return 0u;
    FN_GENERATE_WILD_DIRECT(species, level, 0u);
    /* This is an explicit scanner encounter, never random-wild AUTO
     * provenance.  RESEARCH replaces it with the unlocked authored row and
     * applies IV/ability/move/item policy before the normal battle starts. */
    apply_research_profile(1u);
    FN_START_WILD_DIRECT();
    return 1u;
}

PUBLIC_TEXT(VegaQolProduction_DoStandardWildBattleAdapter)
void VegaQolProduction_DoStandardWildBattleAdapter(void)
{
    u32 pid;
    ensure_state();
    pid = FN_GET_BOX_MON_DATA(PTR(void *, ENEMY_PARTY),
                              MON_DATA_PERSONALITY, (u8 *)0);
    G_QOL_STATE->battle_auto_eligible = (u8)(
        G_QOL_STATE->wild_token_armed
        && pid == G_QOL_STATE->wild_token_pid);
    G_QOL_STATE->battle_token_pid = pid;
    G_QOL_STATE->wild_token_armed = 0u;
    G_QOL_STATE->auto_active = 0u;
    FN_STANDARD_WILD_BATTLE();
}

static u8 late_gimmick_trainer(u16 trainer_id)
{
    u16 low = 0u;
    u16 high = VEGA_QOL_LATE_GIMMICK_TRAINER_COUNT;
    while (low < high) {
        u16 middle = (u16)(low + ((high - low) >> 1));
        if (gVegaQolLateGimmickTrainers[middle] < trainer_id)
            low = (u16)(middle + 1u);
        else
            high = middle;
    }
    return (u8)(low < VEGA_QOL_LATE_GIMMICK_TRAINER_COUNT
        && gVegaQolLateGimmickTrainers[low] == trainer_id);
}

/* The Stage35 owner still parses every real trainerbattle command and builds
 * the exact party.  This adapter only gates the 4 Dynamax and 67 Terastal
 * consumers; before Kanto League clear it clears their pending mechanic so
 * the authored normal-form fallback runs through the same physical command. */
PUBLIC_TEXT(VegaQolProduction_ConfigureTrainerBattleAdapter)
const u8 *VegaQolProduction_ConfigureTrainerBattleAdapter(const u8 *data)
{
    const u8 *next;
    ensure_state();
    G_QOL_STATE->auto_move_slot &= (u8)~QOL_STATE_LATE_GIMMICK_PENDING;
    next = FN_STAGE35_CONFIGURE_TRAINER(data);
    if (next != (const u8 *)0 && late_gimmick_trainer(G_TRAINER_OPPONENT_A)) {
        if (!VegaQolProduction_FeatureUnlocked(
                VEGA_QOL_TERA_DYNAMAX_STORY)) {
            FN_STAGE35_TRAINER_BATTLE_END(3u);
        } else {
            G_QOL_STATE->auto_move_slot |= QOL_STATE_LATE_GIMMICK_PENDING;
        }
    }
    return next;
}

/* SIMPLE_EVENT Raid wrappers call this stable service immediately before the
 * existing wild-battle command.  The linked CFRU function owns real pending
 * Raid state, shields, partner route, capture and battle-end cleanup. */
PUBLIC_TEXT(VegaQolProduction_ConfigureHighRaid)
u8 VegaQolProduction_ConfigureHighRaid(void)
{
    ensure_state();
    if (!VegaQolProduction_FeatureUnlocked(VEGA_QOL_HIGH_DIFFICULTY_RAID))
        return VEGA_QOL_LOCKED;
    clear_owned_high_raid_pending();
    if (VEGA_QOL_HIGH_RAID_COUNT == 0u
        || !FN_CONFIGURE_HIGH_RAID(0u, 6u, 5u, 10u, 1u))
        return VEGA_QOL_CONTEXT_FORBIDDEN;
    G_QOL_STATE->auto_move_slot |= QOL_STATE_HIGH_RAID_PENDING;
    return VEGA_QOL_OK;
}

/* Low-tier Raid hosts are available from the normal story routes.  They use
 * the same one-shot CFRU pending-state owner as high Raids, but deliberately
 * have no partner and no shield so an early-game party cannot be trapped in
 * a high-difficulty controller contract. */
PUBLIC_TEXT(VegaQolProduction_ConfigureLowRaid)
u8 VegaQolProduction_ConfigureLowRaid(void)
{
    ensure_state();
    clear_owned_high_raid_pending();
    if (VEGA_QOL_LOW_RAID_COUNT == 0u
        || !FN_CONFIGURE_HIGH_RAID(0u, 0u, 0u, 10u, 1u))
        return VEGA_QOL_CONTEXT_FORBIDDEN;
    G_QOL_STATE->auto_move_slot |= QOL_STATE_HIGH_RAID_PENDING;
    return VEGA_QOL_OK;
}

PUBLIC_TEXT(VegaQolProduction_ClearBattleAutoState)
void VegaQolProduction_ClearBattleAutoState(void)
{
    ensure_state();
    G_QOL_STATE->wild_token_armed = 0u;
    G_QOL_STATE->battle_auto_eligible = 0u;
    G_QOL_STATE->auto_active = 0u;
    G_QOL_STATE->wild_token_pid = 0u;
    G_QOL_STATE->battle_token_pid = 0u;
    G_QOL_STATE->auto_move_slot &= (u8)~(
        QOL_STATE_HIGH_RAID_PENDING | QOL_STATE_LATE_GIMMICK_PENDING);
}

static u8 auto_battle_allowed_values(u32 flags, u8 shiny, u8 lead_can_battle)
{
    const u32 forbidden = BATTLE_TYPE_TRAINER
        | BATTLE_TYPE_LINK | BATTLE_TYPE_MULTI | BATTLE_TYPE_SAFARI
        | BATTLE_TYPE_SCRIPTED_WILD_1 | BATTLE_TYPE_SCRIPTED_WILD_2
        | BATTLE_TYPE_LEGENDARY | BATTLE_TYPE_FRONTIER_MASK
        | BATTLE_TYPE_DYNAMAX;
    return (u8)(VegaQolProduction_FeatureUnlocked(VEGA_QOL_AUTO_BATTLE)
                && lead_can_battle && !shiny
                && (flags & forbidden) == 0u
                && (flags & ~BATTLE_TYPE_IS_MASTER) == 0u);
}

static u8 auto_battle_allowed_live(void)
{
    u8 *battle_mon = PTR(u8 *, BATTLE_MONS)
        + (u32)G_ACTIVE_BATTLER * BATTLE_MON_STRIDE;
    u32 enemy_pid = FN_GET_BOX_MON_DATA(PTR(void *, ENEMY_PARTY),
                                         MON_DATA_PERSONALITY, (u8 *)0);
    if ((G_ACTIVE_BATTLER & 1u) != 0u)
        return 0u;
    return (u8)(G_QOL_STATE->battle_auto_eligible
        && enemy_pid == G_QOL_STATE->battle_token_pid
        && auto_battle_allowed_values(
        G_BATTLE_FLAGS, FN_IS_MON_SHINY(PTR(void *, ENEMY_PARTY)),
        (u8)(*(volatile u16 *)(void *)(battle_mon + BATTLE_MON_HP) != 0u)));
}

PUBLIC_TEXT(VegaQolProduction_HandleInputChooseActionAdapter)
void VegaQolProduction_HandleInputChooseActionAdapter(void)
{
    ensure_state();
    if (G_MAIN_NEW_KEYS & KEY_B) {
        G_QOL_STATE->auto_active = 0u;
        FN_ORIGINAL_BATTLE_ACTION();
        return;
    }
    if (!auto_battle_allowed_live()) {
        G_QOL_STATE->auto_active = 0u;
        FN_ORIGINAL_BATTLE_ACTION();
        return;
    }
    if (G_MAIN_NEW_KEYS & KEY_SELECT) {
        G_QOL_STATE->auto_active = 1u;
        G_MAIN_NEW_KEYS &= (u16)~KEY_SELECT;
    }
    if (G_QOL_STATE->auto_active) {
        PTR(volatile u8 *, ACTION_CURSOR)[G_ACTIVE_BATTLER] = 0u;
        G_MAIN_NEW_KEYS |= KEY_A;
    }
    FN_ORIGINAL_BATTLE_ACTION();
}

PUBLIC_TEXT(VegaQolProduction_HandleInputChooseMoveAdapter)
void VegaQolProduction_HandleInputChooseMoveAdapter(void)
{
    u8 unusable;
    u8 slot;
    ensure_state();
    if ((G_MAIN_NEW_KEYS & KEY_B) || !G_QOL_STATE->auto_active
        || !auto_battle_allowed_live()) {
        if (G_MAIN_NEW_KEYS & KEY_B)
            G_QOL_STATE->auto_active = 0u;
        FN_ORIGINAL_BATTLE_MOVE();
        return;
    }
    unusable = FN_CHECK_MOVE_LIMITATIONS(G_ACTIVE_BATTLER, 0u, 0xFFu);
    for (slot = 0u; slot < 4u; ++slot) {
        if ((unusable & (1u << slot)) == 0u)
            break;
    }
    if (slot >= 4u) {
        G_QOL_STATE->auto_active = 0u;
        FN_ORIGINAL_BATTLE_MOVE();
        return;
    }
    G_QOL_STATE->auto_move_slot = slot;
    PTR(volatile u8 *, MOVE_CURSOR)[G_ACTIVE_BATTLER] = slot;
    G_MAIN_NEW_KEYS |= KEY_A;
    FN_ORIGINAL_BATTLE_MOVE();
}

static u8 first_empty_pc_slot(u8 *out_box, u8 *out_slot)
{
    u8 box;
    u8 slot;
    for (box = 0u; box < VEGA_QOL_BOX_COUNT; ++box) {
        for (slot = 0u; slot < VEGA_QOL_BOX_CAPACITY; ++slot) {
            if (FN_GET_BOX_MON_DATA_AT(box, slot, MON_DATA_SPECIES) == 0u) {
                *out_box = box;
                *out_slot = slot;
                return 1u;
            }
        }
    }
    return 0u;
}

static u8 build_daycare_egg_box(void *daycare_data, u8 out[VEGA_BOX_MON_SIZE])
{
    u8 *party = PTR(u8 *, PLAYER_PARTY);
    u8 backup[VEGA_PARTY_CAPACITY * VEGA_PARTY_MON_SIZE];
    u8 old_count = *(volatile u8 *)(uintptr_t)PLAYER_PARTY_COUNT;
    u8 slot;
    u8 found = 0xFFu;
    if (old_count > VEGA_PARTY_CAPACITY)
        return 0u;
    copy_bytes(backup, party, VEGA_PARTY_CAPACITY * VEGA_PARTY_MON_SIZE);
    for (slot = old_count; slot < VEGA_PARTY_CAPACITY; ++slot)
        clear_bytes(party + (u32)slot * VEGA_PARTY_MON_SIZE,
                    VEGA_PARTY_MON_SIZE);
    /* Linked GiveEgg uses party slot 5 or PC.  Count 5 forces the party path;
     * the complete six-slot image is restored after the generated BoxPokemon
     * has been copied into the shared FIFO. */
    *(volatile u8 *)(uintptr_t)PLAYER_PARTY_COUNT = 5u;
    FN_DAYCARE_GIVE_EGG(daycare_data);
    for (slot = 0u; slot < VEGA_PARTY_CAPACITY; ++slot) {
        u8 *candidate = party + (u32)slot * VEGA_PARTY_MON_SIZE;
        u8 *before = backup + (u32)slot * VEGA_PARTY_MON_SIZE;
        if (bytes_differ(candidate, before, VEGA_PARTY_MON_SIZE)
            && FN_GET_BOX_MON_DATA(candidate, MON_DATA_IS_EGG, (u8 *)0)) {
            found = slot;
            break;
        }
    }
    if (found != 0xFFu) {
        copy_bytes(out, party + (u32)found * VEGA_PARTY_MON_SIZE,
                   VEGA_BOX_MON_SIZE);
    }
    copy_bytes(party, backup, VEGA_PARTY_CAPACITY * VEGA_PARTY_MON_SIZE);
    *(volatile u8 *)(uintptr_t)PLAYER_PARTY_COUNT = old_count;
    return (u8)(found != 0xFFu);
}

static u8 queue_generated_egg(void *daycare_data)
{
    u8 egg[VEGA_BOX_MON_SIZE];
    u8 tail;
    if (!ensure_save()
        || gVegaModernSaveData->egg_queue_count >= VEGA_EGG_QUEUE_CAPACITY)
        return 0u;
    if (!build_daycare_egg_box(daycare_data, egg))
        return 0u;
    tail = (u8)((gVegaModernSaveData->egg_queue_head
                 + gVegaModernSaveData->egg_queue_count)
                % VEGA_EGG_QUEUE_CAPACITY);
    copy_bytes(gVegaModernSaveData->egg_queue[tail], egg,
               VEGA_BOX_MON_SIZE);
    ++gVegaModernSaveData->egg_queue_count;
    FN_SAVE_FINALIZE(gVegaModernSaveData);
    return 1u;
}

static void pop_delivered_egg(void)
{
    u8 head = gVegaModernSaveData->egg_queue_head;
    clear_bytes(gVegaModernSaveData->egg_queue[head], VEGA_BOX_MON_SIZE);
    --gVegaModernSaveData->egg_queue_count;
    if (gVegaModernSaveData->egg_queue_count == 0u)
        gVegaModernSaveData->egg_queue_head = 0u;
    else
        gVegaModernSaveData->egg_queue_head =
            (u8)((head + 1u) % VEGA_EGG_QUEUE_CAPACITY);
    FN_SAVE_FINALIZE(gVegaModernSaveData);
}

static VegaQolStatus give_egg_from_daycare_transaction(void *daycare_data)
{
    u8 count = *(volatile u8 *)(uintptr_t)PLAYER_PARTY_COUNT;
    u8 party_backup[VEGA_PARTY_MON_SIZE];
    u8 daycare_backup[DAYCARE_OFFSPRING_OFFSET + sizeof(u32)];
    u8 pending_before;
    u8 box;
    u8 slot;
    if (daycare_data == (void *)0 || count > VEGA_PARTY_CAPACITY)
        return VEGA_QOL_INVALID_ARGUMENT;
    if (!ensure_save())
        return VEGA_QOL_CORRUPT_SAVE;
    pending_before = FN_FLAG_GET(FLAG_PENDING_DAYCARE_EGG);
    if (gVegaModernSaveData->egg_queue_count != 0u) {
        u8 head = gVegaModernSaveData->egg_queue_head;
        copy_bytes(gVegaSaveRollbackData, gVegaModernSaveData,
                   VEGA_SAVE_LEDGER_SIZE);
        if (count < VEGA_PARTY_CAPACITY) {
            void *destination = PTR(u8 *, PLAYER_PARTY)
                + (u32)count * VEGA_PARTY_MON_SIZE;
            copy_bytes(party_backup, destination, VEGA_PARTY_MON_SIZE);
            FN_BOX_MON_TO_MON(gVegaModernSaveData->egg_queue[head],
                              destination);
            (void)FN_CALCULATE_PARTY_COUNT();
            pop_delivered_egg();
            FN_FLAG_CLEAR(FLAG_PENDING_DAYCARE_EGG);
            if (!persist_cross_store()) {
                copy_bytes(destination, party_backup, VEGA_PARTY_MON_SIZE);
                *(volatile u8 *)(uintptr_t)PLAYER_PARTY_COUNT = count;
                copy_bytes(gVegaModernSaveData, gVegaSaveRollbackData,
                           VEGA_SAVE_LEDGER_SIZE);
                if (pending_before)
                    FN_FLAG_SET(FLAG_PENDING_DAYCARE_EGG);
                compensate_cross_store();
                return VEGA_QOL_PERSIST_FAILED;
            }
        } else if (first_empty_pc_slot(&box, &slot)) {
            FN_SET_BOX_MON_AT(box, slot,
                gVegaModernSaveData->egg_queue[head]);
            pop_delivered_egg();
            FN_FLAG_CLEAR(FLAG_PENDING_DAYCARE_EGG);
            if (!persist_cross_store()) {
                FN_ZERO_BOX_MON_AT(box, slot);
                copy_bytes(gVegaModernSaveData, gVegaSaveRollbackData,
                           VEGA_SAVE_LEDGER_SIZE);
                if (pending_before)
                    FN_FLAG_SET(FLAG_PENDING_DAYCARE_EGG);
                compensate_cross_store();
                return VEGA_QOL_PERSIST_FAILED;
            }
        } else {
            return VEGA_QOL_CAPACITY;
        }
        return VEGA_QOL_OK;
    }
    if (count == VEGA_PARTY_CAPACITY && !first_empty_pc_slot(&box, &slot))
        return VEGA_QOL_CAPACITY;
    copy_bytes(daycare_backup, daycare_data, sizeof(daycare_backup));
    copy_bytes(gVegaSaveRollbackData, gVegaModernSaveData,
               VEGA_SAVE_LEDGER_SIZE);
    if (count < VEGA_PARTY_CAPACITY) {
        void *destination = PTR(u8 *, PLAYER_PARTY)
            + (u32)count * VEGA_PARTY_MON_SIZE;
        copy_bytes(party_backup, destination, VEGA_PARTY_MON_SIZE);
        FN_DAYCARE_GIVE_EGG(daycare_data);
        if (*(volatile u8 *)(uintptr_t)PLAYER_PARTY_COUNT == count) {
            copy_bytes(destination, party_backup, VEGA_PARTY_MON_SIZE);
            copy_bytes(daycare_data, daycare_backup, sizeof(daycare_backup));
            return VEGA_QOL_EFFECTLESS;
        }
    } else {
        /* Legacy pending flags can exist without a queue entry.  A full-party
         * acceptance sends the inherited egg directly to the first PC slot. */
        u8 egg[VEGA_BOX_MON_SIZE];
        if (!build_daycare_egg_box(daycare_data, egg)) {
            copy_bytes(daycare_data, daycare_backup, sizeof(daycare_backup));
            return VEGA_QOL_EFFECTLESS;
        }
        FN_SET_BOX_MON_AT(box, slot, egg);
    }
    FN_FLAG_CLEAR(FLAG_PENDING_DAYCARE_EGG);
    FN_SAVE_FINALIZE(gVegaModernSaveData);
    if (!persist_cross_store()) {
        if (count < VEGA_PARTY_CAPACITY) {
            void *destination = PTR(u8 *, PLAYER_PARTY)
                + (u32)count * VEGA_PARTY_MON_SIZE;
            copy_bytes(destination, party_backup, VEGA_PARTY_MON_SIZE);
            *(volatile u8 *)(uintptr_t)PLAYER_PARTY_COUNT = count;
        } else {
            FN_ZERO_BOX_MON_AT(box, slot);
        }
        copy_bytes(daycare_data, daycare_backup, sizeof(daycare_backup));
        copy_bytes(gVegaModernSaveData, gVegaSaveRollbackData,
                   VEGA_SAVE_LEDGER_SIZE);
        if (pending_before)
            FN_FLAG_SET(FLAG_PENDING_DAYCARE_EGG);
        compensate_cross_store();
        return VEGA_QOL_PERSIST_FAILED;
    }
    return VEGA_QOL_OK;
}

PUBLIC_TEXT(VegaQolProduction_GiveEggFromDaycareAdapter)
void VegaQolProduction_GiveEggFromDaycareAdapter(void *daycare_data)
{
    (void)give_egg_from_daycare_transaction(daycare_data);
}

/* The stock Special wrapper restores LR through r0 and therefore discards the
 * internal GiveEgg return value.  The event table points at this status-returning
 * owner so specialvar can branch before any success text or flag clear. */
PUBLIC_TEXT(VegaQolProduction_GiveEggFromDaycareSpecial)
u8 VegaQolProduction_GiveEggFromDaycareSpecial(void)
{
    return (u8)give_egg_from_daycare_transaction(daycare());
}

PUBLIC_TEXT(VegaQolProduction_CalculatePartyCountForDaycare)
u8 VegaQolProduction_CalculatePartyCountForDaycare(void)
{
    u8 count = FN_CALCULATE_PARTY_COUNT();
    /* Daycare scripts reject a full party before reaching GiveEgg.  Returning
     * five only for their pending-egg transaction lets the existing Yes/No
     * flow reach our queue adapter while preserving the true global count. */
    if (count == VEGA_PARTY_CAPACITY && daycare_first_use()
        && (FN_FLAG_GET(FLAG_PENDING_DAYCARE_EGG)
            || (ensure_save()
                && gVegaModernSaveData->egg_queue_count != 0u))) {
        u8 box;
        u8 slot;
        if (first_empty_pc_slot(&box, &slot))
            return VEGA_PARTY_CAPACITY - 1u;
    }
    return count;
}

PUBLIC_TEXT(VegaQolProduction_IsEggPendingAdapter)
u8 VegaQolProduction_IsEggPendingAdapter(void *daycare_data)
{
    (void)daycare_data;
    return (u8)(FN_FLAG_GET(FLAG_PENDING_DAYCARE_EGG)
        || (ensure_save() && gVegaModernSaveData->egg_queue_count != 0u));
}

PUBLIC_TEXT(VegaQolProduction_TriggerPendingDaycareEggAdapter)
void VegaQolProduction_TriggerPendingDaycareEggAdapter(void *daycare_data)
{
    if (daycare_data != (void *)0)
        (void)queue_generated_egg(daycare_data);
}

static void basket_step(void)
{
    volatile u16 *counter = PTR(volatile u16 *, QOL_BASKET_COUNTER);
    void *data;
    u8 compatibility;
    if (!FN_FLAG_GET(FLAG_QOL_EGG_BASKET)
        || !VegaQolProduction_FeatureUnlocked(VEGA_QOL_EGG_BASKET))
        return;
    *counter = (u16)(*counter + 1u);
    if (*counter < 256u)
        return;
    *counter = 0u;
    if (!ensure_save()
        || gVegaModernSaveData->egg_queue_count >= VEGA_EGG_QUEUE_CAPACITY)
        return;
    data = daycare();
    if (data == (void *)0)
        return;
    compatibility = FN_DAYCARE_COMPATIBILITY(data);
    if (compatibility == 0u)
        return;
    compatibility = VegaQolProduction_ModifyBreedingScore(compatibility);
    if (compatibility <= (((u32)FN_RANDOM() * 100u) >> 16))
        return;
    (void)queue_generated_egg(data);
}

PUBLIC_TEXT(VegaQolProduction_ShouldEggHatchAdapter)
u8 VegaQolProduction_ShouldEggHatchAdapter(void)
{
    void *data = daycare();
    u8 basket_active = (u8)(FN_FLAG_GET(FLAG_QOL_EGG_BASKET)
        && VegaQolProduction_FeatureUnlocked(VEGA_QOL_EGG_BASKET));
    u16 offspring = 0u;
    u8 suppressed = 0u;
    u8 result;
    /* Stock ShouldEggHatch already performs the ordinary 256-step breeding
     * roll.  While the basket owns that clock, temporarily mark the stock
     * pending field so only its hatch/step side effects run; basket_step then
     * performs exactly one compatibility/RNG roll and restores the field. */
    if (basket_active && data != (void *)0) {
        volatile u16 *field = PTR(volatile u16 *,
            (u32)(uintptr_t)data + DAYCARE_OFFSPRING_OFFSET);
        offspring = *field;
        if (offspring == 0u) {
            *field = 1u;
            suppressed = 1u;
        }
    }
    result = FN_SHOULD_EGG_HATCH();
    if (suppressed) {
        *PTR(volatile u16 *, (u32)(uintptr_t)data
            + DAYCARE_OFFSPRING_OFFSET) = offspring;
    }
    if (basket_active)
        basket_step();
    return result;
}

PUBLIC_TEXT(VegaQolProduction_SubtractEggSteps)
u32 VegaQolProduction_SubtractEggSteps(u32 steps, void *mon)
{
    /* HATCH_MODE controls presentation only; it must never change egg steps. */
    return FN_SUBTRACT_EGG_STEPS(steps, mon);
}

PUBLIC_TEXT(VegaQolProduction_TryDecrementEggSteps)
void VegaQolProduction_TryDecrementEggSteps(void *daycare_data, u8 ignore_id)
{
    FN_TRY_DECREMENT_EGG_STEPS(daycare_data, ignore_id);
}

PUBLIC_TEXT(VegaQolProduction_ShouldSkipHatchNickname)
u8 VegaQolProduction_ShouldSkipHatchNickname(void)
{
    /* Even SKIP preserves the nickname prompt and Pokédex registration. */
    return 0u;
}

PUBLIC_TEXT(VegaQolProduction_EggHatchPresentationAdapter)
void VegaQolProduction_EggHatchPresentationAdapter(void)
{
    u8 repeats = 0u;
    u8 state;
    /* gMain keeps the original low-ROM callback value; the entry hook does
     * not rewrite the stored pointer. */
    const u32 hatch_callback = 0x080468C1u;
    if (ensure_save()) {
        if (gVegaModernSaveData->hatch_mode == VEGA_HATCH_FAST)
            repeats = 1u;
        else if (gVegaModernSaveData->hatch_mode == VEGA_HATCH_SKIP)
            repeats = 7u;
    }
    VegaQolProduction_OriginalEggHatchCallback();
    while (repeats-- != 0u && G_MAIN_CALLBACK2 == hatch_callback) {
        u32 data = *(volatile u32 *)(uintptr_t)EGG_HATCH_DATA_SLOT;
        if (!pointer_is_ewram(data, 3u))
            break;
        state = *(volatile u8 *)(uintptr_t)(data + 2u);
        /* Never cross the message/nickname states within one input frame.
         * Otherwise the A/B that ended the fanfare can also answer a prompt
         * which was not visible when the key was pressed. */
        if (state >= 8u && state <= 10u)
            break;
        VegaQolProduction_OriginalEggHatchCallback();
    }
}

PUBLIC_TEXT(VegaQolProduction_ModifyBreedingScore)
u8 VegaQolProduction_ModifyBreedingScore(u8 score)
{
    VegaQolStatus claim_status;
    if (!VegaQolProduction_FeatureUnlocked(VEGA_QOL_OVAL_CHARM))
        return score;
    /* The quest service normally awards the charm.  The alternate 100-catch
     * boundary has no narrative owner, so claim it on the first breeding
     * check while keeping a full key-item pocket failure non-destructive. */
    if (!FN_CHECK_BAG_HAS_ITEM(684u, 1u)) {
        if (!ensure_save())
            return score;
        claim_status = claim_single_item_raw(684u, 684u, 1u);
        if (claim_status != VEGA_QOL_OK
            && claim_status != VEGA_QOL_ALREADY_CLAIMED)
            return score;
        if (!FN_CHECK_BAG_HAS_ITEM(684u, 1u))
            return score;
    }
    return score >= 50u ? 100u : (u8)(score * 2u);
}

static u8 append_encoded(u8 *out, u8 at, const u8 *text, u8 limit)
{
    while (at + 1u < limit && *text != 0xFFu)
        out[at++] = *text++;
    out[at] = 0xFFu;
    return at;
}

static u8 append_number(u8 *out, u8 at, u16 value, u8 width, u8 limit)
{
    u16 divisor = width == 3u ? 100u : (width == 2u ? 10u : 1u);
    while (width-- != 0u && at + 1u < limit) {
        out[at++] = gVegaQolDigits[(value / divisor) % 10u];
        if (divisor > 1u)
            divisor = (u16)(divisor / 10u);
    }
    out[at] = 0xFFu;
    return at;
}

static u8 iv_judge_word(u8 value)
{
    if (value == 31u)
        return 0u;
    if (value == 30u)
        return 1u;
    if (value >= 26u)
        return 2u;
    if (value >= 16u)
        return 3u;
    return value != 0u ? 4u : 5u;
}

static u8 append_stat_judge(u8 *line, u8 at, u8 limit, void *mon,
                            u8 stat, u8 mode, u8 short_label)
{
    u16 value;
    const u8 *label = short_label ? gVegaQolShortStatLabels[stat]
                                  : gVegaQolStatLabels[stat];
    at = append_encoded(line, at, label, limit);
    at = append_encoded(line, at, gVegaQolSpace, limit);
    if (mode == 1u) {
        u8 trained = PTR(const u8 *, mon)[0x10u];
        value = (u16)FN_GET_BOX_MON_DATA(mon, MON_DATA_HP_IV + stat,
                                         (u8 *)0);
        at = append_number(line, at, value, 2u, limit);
        at = append_encoded(line, at, gVegaQolSpace, limit);
        if (trained & (1u << stat))
            at = append_encoded(line, at, gVegaQolTrainedText, limit);
        else
            at = append_encoded(line, at,
                                gVegaQolIvJudgeWords[iv_judge_word((u8)value)],
                                limit);
    } else {
        value = (u16)FN_GET_BOX_MON_DATA(mon, MON_DATA_HP_EV + stat,
                                         (u8 *)0);
        at = append_number(line, at, value, 3u, limit);
        if (value >= 252u)
            at = append_encoded(line, at, gVegaQolMaxText, limit);
    }
    return at;
}

static u16 mon_ev_total(void *mon)
{
    u16 total = 0u;
    u8 stat;
    for (stat = 0u; stat < 6u; ++stat)
        total = (u16)(total + FN_GET_BOX_MON_DATA(
            mon, MON_DATA_HP_EV + stat, (u8 *)0));
    return total;
}

static void build_pc_judge_lines(void *mon, u8 mode, u8 selected)
{
    u8 line_index;
    u8 *lines[3] = {G_QOL_STATE->judge_iv, G_QOL_STATE->judge_ev,
                    G_QOL_STATE->relearn_text};
    for (line_index = 0u; line_index < 3u; ++line_index) {
        u8 at = 0u;
        u8 first = (u8)(line_index * 2u);
        clear_bytes(lines[line_index], 36u);
        lines[line_index][0] = 0xFFu;
        if (selected && line_index == 0u)
            at = append_encoded(lines[line_index], at,
                                gVegaQolSelectedPrefix, 36u);
        at = append_stat_judge(lines[line_index], at, 36u, mon, first,
                               mode, 1u);
        at = append_encoded(lines[line_index], at, gVegaQolSeparator, 36u);
        at = append_stat_judge(lines[line_index], at, 36u, mon,
                               (u8)(first + 1u), mode, 1u);
        if (mode == 2u && line_index == 2u) {
            at = append_encoded(lines[line_index], at,
                                gVegaQolSeparator, 36u);
            at = append_number(lines[line_index], at, mon_ev_total(mon),
                               3u, 36u);
            at = append_encoded(lines[line_index], at,
                                gVegaQolSeparator, 36u);
            (void)append_number(lines[line_index], at, 510u, 3u, 36u);
        }
    }
}

static void update_box_markers(void)
{
    u32 pss = G_PSS_DATA;
    u8 box;
    u8 slot;
    if (!pointer_is_ewram(pss, PSS_BOX_SPRITES_OFFSET + 120u))
        return;
    box = FN_STORAGE_CURRENT_BOX();
    if (box >= VEGA_QOL_BOX_COUNT)
        return;
    if (!G_QOL_STATE->marker_initialized || G_QOL_STATE->marker_box != box) {
        G_QOL_STATE->marker_box = box;
        G_QOL_STATE->marker_initialized = 1u;
        for (slot = 0u; slot < VEGA_QOL_BOX_CAPACITY; ++slot) {
            u32 sprite = *(volatile u32 *)(uintptr_t)(
                pss + PSS_BOX_SPRITES_OFFSET + (u32)slot * 4u);
            G_QOL_STATE->marker_modes[slot] = pointer_is_ewram(sprite, 2u)
                ? (u8)((*(volatile u16 *)(uintptr_t)sprite >> 10) & 3u)
                : 0u;
        }
    }
    for (slot = 0u; slot < VEGA_QOL_BOX_CAPACITY; ++slot) {
        u32 sprite = *(volatile u32 *)(uintptr_t)(
            pss + PSS_BOX_SPRITES_OFFSET + (u32)slot * 4u);
        if (pointer_is_ewram(sprite, 2u)) {
            volatile u16 *attr0 = (volatile u16 *)(uintptr_t)sprite;
            if (G_QOL_STATE->selection[box] & ((u32)1u << slot))
                *attr0 = (u16)((*attr0 & (u16)~0x0C00u) | 0x0400u);
            else
                *attr0 = (u16)((*attr0 & (u16)~0x0C00u)
                    | ((u16)G_QOL_STATE->marker_modes[slot] << 10));
        }
    }
}

static void update_pc_judge(void)
{
    u32 pss = G_PSS_DATA;
    u8 area;
    u8 slot;
    u8 box;
    u8 mode;
    void *mon;
    if (!pointer_is_ewram(pss, PSS_CURSOR_TEXT_OFFSET
                              + PSS_CURSOR_TEXT_STRIDE * 4u))
        return;
    area = *(volatile u8 *)(uintptr_t)PSS_CURSOR_AREA;
    slot = *(volatile u8 *)(uintptr_t)PSS_CURSOR_POSITION;
    box = FN_STORAGE_CURRENT_BOX();
    if (area != 0u || !selection_valid(box, slot))
        return;
    mode = pss_judge_mode();
    if (mode == 0u) {
        update_box_markers();
        return;
    }
    mon = FN_GET_BOXED_MON(box, slot);
    if (mon == (void *)0
        || FN_GET_BOX_MON_DATA(mon, MON_DATA_SPECIES, (u8 *)0) == 0u)
        return;
    build_pc_judge_lines(mon, mode,
        (u8)((G_QOL_STATE->selection[box] & ((u32)1u << slot)) != 0u));
    copy_bytes(PTR(void *, pss + PSS_CURSOR_TEXT_OFFSET
                         + PSS_CURSOR_TEXT_STRIDE),
               G_QOL_STATE->judge_iv, sizeof(G_QOL_STATE->judge_iv));
    copy_bytes(PTR(void *, pss + PSS_CURSOR_TEXT_OFFSET
                         + PSS_CURSOR_TEXT_STRIDE * 2u),
               G_QOL_STATE->judge_ev, sizeof(G_QOL_STATE->judge_ev));
    copy_bytes(PTR(void *, pss + PSS_CURSOR_TEXT_OFFSET
                         + PSS_CURSOR_TEXT_STRIDE * 3u),
               G_QOL_STATE->relearn_text,
               sizeof(G_QOL_STATE->relearn_text));
    FN_PRINT_PSS_MON_INFO();
    update_box_markers();
}

enum {
    QOL_SEARCH_MENU_NONE = 0u,
    QOL_SEARCH_MENU_CATEGORY = 1u,
    QOL_SEARCH_MENU_TYPE = 2u,
    QOL_SEARCH_MENU_ABILITY = 3u,
    QOL_PSS_MENU_MOVE = 0x40u,
    QOL_PSS_MENU_MOVE_SLOT = 0x41u,
    QOL_PSS_MENU_MOVE_CONFIRM = 0x42u,
    QOL_PSS_MENU_RELEASE_CONFIRM = 0x43u,
    QOL_PSS_MENU_BOX_MOVE_CONFIRM = 0x44u,
    QOL_PSS_MENU_TAKE_ITEMS_CONFIRM = 0x45u,
    QOL_SEARCH_NAMING_PENDING = 0x80u,
};

static u8 search_menu_mode(void)
{
    return (u8)(G_QOL_STATE->filter_mode >> 4);
}

static void set_search_menu_mode(u8 mode)
{
    G_QOL_STATE->filter_mode = (u8)((G_QOL_STATE->filter_mode & 0x0Fu)
                                     | ((mode & 3u) << 4));
}

static VegaQolStatus open_pss_list_menu(
    const VegaQolGeneratedListItem *items, u16 total_items,
    u16 initial_cursor, u8 operation)
{
    QolListMenuTemplate menu;
    u16 scroll_offset;
    u16 selected_row;
    u8 task_id;
    if (items == (const VegaQolGeneratedListItem *)0 || total_items == 0u)
        return VEGA_QOL_INVALID_ARGUMENT;
    clear_bytes(&menu, sizeof(menu));
    menu.items = items;
    menu.total_items = total_items;
    /* PSS window 2 is the stock 25x8-tile right pane.  Font 2 consumes two
     * tile rows, so four visible entries are the exact safe maximum. */
    menu.max_showed = total_items < 4u ? total_items : 4u;
    menu.window_id = 2u;
    menu.item_x = 9u;
    menu.cursor_x = 1u;
    menu.cursor_pal = 2u;
    menu.fill_value = 1u;
    menu.cursor_shadow_pal = 3u;
    menu.font_id = 2u;
    if (initial_cursor >= total_items)
        initial_cursor = (u16)(total_items - 1u);
    if (initial_cursor >= menu.max_showed)
        scroll_offset = (u16)(initial_cursor - menu.max_showed + 1u);
    else
        scroll_offset = 0u;
    selected_row = (u16)(initial_cursor - scroll_offset);
    FN_FILL_WINDOW(2u, 0x11u);
    task_id = FN_LIST_MENU_INIT(&menu, scroll_offset, selected_row);
    if (task_id == 0xFFu)
        return VEGA_QOL_CAPACITY;
    G_QOL_STATE->last_result = task_id;
    G_QOL_STATE->pss_confirm_op = operation;
    return VEGA_QOL_OK;
}

static void close_pss_list_menu(void)
{
    u16 cursor = 0u;
    u16 above = 0u;
    FN_LIST_MENU_DESTROY((u8)G_QOL_STATE->last_result, &cursor, &above);
    G_QOL_STATE->pss_confirm_op = 0u;
}

static VegaQolStatus open_search_menu(u8 mode)
{
    const VegaQolGeneratedListItem *items;
    u16 total_items;
    VegaQolStatus status;
    if (mode == QOL_SEARCH_MENU_CATEGORY) {
        items = (const VegaQolGeneratedListItem *)gVegaQolSearchMenuItems;
        total_items = 5u;
    } else if (mode == QOL_SEARCH_MENU_TYPE) {
        items = (const VegaQolGeneratedListItem *)gVegaQolSearchTypeItems;
        total_items = VEGA_QOL_SEARCH_TYPE_COUNT;
    } else if (mode == QOL_SEARCH_MENU_ABILITY) {
        items = (const VegaQolGeneratedListItem *)gVegaQolSearchAbilityItems;
        total_items = VEGA_QOL_SEARCH_ABILITY_COUNT;
    } else {
        return VEGA_QOL_INVALID_ARGUMENT;
    }
    status = open_pss_list_menu(items, total_items, 0u, 0u);
    if (status != VEGA_QOL_OK) {
        FN_REFRESH_PSS_MON_DATA();
        FN_PRINT_PSS_MON_INFO();
        return status;
    }
    set_search_menu_mode(mode);
    return VEGA_QOL_OK;
}

static void close_search_menu(void)
{
    close_pss_list_menu();
    set_search_menu_mode(QOL_SEARCH_MENU_NONE);
}

static void restore_pc_right_pane(void)
{
    FN_REFRESH_PSS_MON_DATA();
    FN_PRINT_PSS_MON_INFO();
    if (pss_judge_mode() != 0u)
        update_pc_judge();
}

static void show_pc_status(VegaQolStatus status)
{
    u32 pss = G_PSS_DATA;
    if (!pointer_is_ewram(pss + PSS_CURSOR_TEXT_OFFSET,
                          PSS_CURSOR_TEXT_STRIDE * 4u))
        return;
    if ((u16)status > VEGA_QOL_ALREADY_CLAIMED)
        status = VEGA_QOL_INVALID_ARGUMENT;
    FN_REFRESH_PSS_MON_DATA();
    copy_bytes(PTR(void *, pss + PSS_CURSOR_TEXT_OFFSET
                         + PSS_CURSOR_TEXT_STRIDE),
               gVegaQolPssStatusMessages[status], PSS_CURSOR_TEXT_STRIDE);
    clear_bytes(PTR(void *, pss + PSS_CURSOR_TEXT_OFFSET
                          + PSS_CURSOR_TEXT_STRIDE * 2u),
                PSS_CURSOR_TEXT_STRIDE * 2u);
    FN_PRINT_PSS_MON_INFO();
    update_box_markers();
}

static void begin_search_name_input(void)
{
    clear_bytes(G_QOL_STATE->judge_iv, sizeof(G_QOL_STATE->judge_iv));
    G_QOL_STATE->judge_iv[0] = 0xFFu;
    G_QOL_STATE->pss_confirm_op = QOL_SEARCH_NAMING_PENDING;
    if (!pointer_is_ewram(G_PSS_DATA, 5u)) {
        G_QOL_STATE->pss_confirm_op = 0u;
        restore_pc_right_pane();
        return;
    }
    /* Reuse stock Task_NameBox so SaveMovingMon, fade, sWhichToReshow and
     * screenChangeType are all established before our naming hook swaps only
     * the template/destination/callback. */
    FN_SET_PSS_TASK(PTR(TaskFunc, 0x0808E4CDu));
}

static u8 process_search_menu(void)
{
    s32 choice = FN_LIST_MENU_INPUT((u8)G_QOL_STATE->last_result);
    u8 mode = search_menu_mode();
    VegaQolStatus status = VEGA_QOL_OK;
    if (choice == -1)
        return 0u;
    close_search_menu();
    if (choice == -2 || (mode == QOL_SEARCH_MENU_CATEGORY && choice == 4)) {
        restore_pc_right_pane();
        return 0u;
    }
    if (mode == QOL_SEARCH_MENU_CATEGORY) {
        if (choice == 0) {
            begin_search_name_input();
            return 0u;
        }
        if (choice == 1)
            status = open_search_menu(QOL_SEARCH_MENU_TYPE);
        else if (choice == 2)
            status = open_search_menu(QOL_SEARCH_MENU_ABILITY);
        else if (choice == 3) {
            clear_bytes(&G_QOL_STATE->filter,
                        sizeof(G_QOL_STATE->filter));
            clear_selection();
            restore_pc_right_pane();
        } else
            status = VEGA_QOL_INVALID_ARGUMENT;
    } else if (mode == QOL_SEARCH_MENU_TYPE && choice >= 0
               && choice <= 255) {
        G_QOL_STATE->filter.type_id = (u8)choice;
        G_QOL_STATE->filter.modes |= VEGA_QOL_SEARCH_TYPE;
        status = search_and_select(&G_QOL_STATE->filter);
        restore_pc_right_pane();
    } else if (mode == QOL_SEARCH_MENU_ABILITY && choice > 0
               && choice <= 0xFFFF) {
        G_QOL_STATE->filter.ability_id = (u16)choice;
        G_QOL_STATE->filter.modes |= VEGA_QOL_SEARCH_ABILITY;
        status = search_and_select(&G_QOL_STATE->filter);
        restore_pc_right_pane();
    } else {
        status = VEGA_QOL_INVALID_ARGUMENT;
        restore_pc_right_pane();
    }
    if (search_menu_mode() == QOL_SEARCH_MENU_NONE)
        G_QOL_STATE->last_result = status;
    return 0u;
}

static void return_from_search_naming(void)
{
    u8 index;
    clear_bytes(G_QOL_STATE->filter.nickname,
                sizeof(G_QOL_STATE->filter.nickname));
    for (index = 0u; index < 10u
         && G_QOL_STATE->judge_iv[index] != 0xFFu; ++index)
        G_QOL_STATE->filter.nickname[index] =
            G_QOL_STATE->judge_iv[index];
    G_QOL_STATE->filter.nickname[index] = 0xFFu;
    if (index == 0u)
        G_QOL_STATE->filter.modes &= (u8)~VEGA_QOL_SEARCH_NAME;
    else
        G_QOL_STATE->filter.modes |= VEGA_QOL_SEARCH_NAME;
    G_QOL_STATE->last_result = G_QOL_STATE->filter.modes != 0u
        ? search_and_select(&G_QOL_STATE->filter) : VEGA_QOL_OK;
    G_QOL_STATE->pss_confirm_op = 0u;
    FN_STANDARD_PSS_RETURN();
}

PUBLIC_TEXT(VegaQolProduction_DoNamingScreenAdapter)
void VegaQolProduction_DoNamingScreenAdapter(
    u8 template_num, u8 *destination, u16 species, u16 gender,
    u32 personality, VoidFn return_callback)
{
    ensure_state();
    if (G_QOL_STATE->pss_confirm_op == QOL_SEARCH_NAMING_PENDING) {
        VegaQolProduction_OriginalDoNamingScreen(
            6u, G_QOL_STATE->judge_iv, 0u, 0u, 0u,
            return_from_search_naming);
        return;
    }
    VegaQolProduction_OriginalDoNamingScreen(
        template_num, destination, species, gender, personality,
        return_callback);
}

static void free_relearn_menu_items(void)
{
    u32 pointer = G_QOL_STATE->wild_token_pid;
    u32 count = G_QOL_STATE->wild_token_armed;
    if (pointer_is_ewram(pointer,
                         count * sizeof(VegaQolGeneratedListItem)))
        FN_FREE(PTR(void *, pointer));
    G_QOL_STATE->wild_token_pid = 0u;
    G_QOL_STATE->wild_token_armed = 0u;
}

static VegaQolStatus open_relearn_move_menu(u8 box, u8 slot)
{
    u8 mon[VEGA_PARTY_MON_SIZE];
    u16 pool[64];
    VegaQolGeneratedListItem *items;
    VegaQolStatus status;
    u8 count;
    u8 out = 0u;
    u8 index;
    if (!selection_valid(box, slot)
        || FN_GET_BOX_MON_DATA_AT(box, slot, MON_DATA_SPECIES) == 0u)
        return VEGA_QOL_INVALID_ARGUMENT;
    if (!VegaQolProduction_FeatureUnlocked(VEGA_QOL_PC_MOVE_EDIT))
        return VEGA_QOL_LOCKED;
    FN_BOX_MON_AT_TO_MON(box, slot, mon);
    if (FN_GET_BOX_MON_DATA(mon, MON_DATA_IS_EGG, (u8 *)0))
        return VEGA_QOL_FORBIDDEN_MON;
    *(volatile u8 *)(uintptr_t)MOVE_MANAGER_MODE = 0u;
    count = FN_MOVE_RELEARN_POOL(mon, pool);
    if (count > 64u)
        count = 64u;
    if (count == 0u)
        return VEGA_QOL_EFFECTLESS;
    free_relearn_menu_items();
    items = (VegaQolGeneratedListItem *)FN_ALLOC_ZEROED(
        (u32)count * sizeof(*items));
    if (items == (VegaQolGeneratedListItem *)0)
        return VEGA_QOL_CAPACITY;
    for (index = 0u; index < count; ++index) {
        u8 known;
        if (pool[index] == 0u || pool[index] >= VEGA_QOL_MOVE_COUNT)
            continue;
        for (known = 0u; known < 4u; ++known) {
            if (FN_GET_BOX_MON_DATA(mon, MON_DATA_MOVE1 + known,
                                    (u8 *)0) == pool[index])
                break;
        }
        if (known != 4u)
            continue;
        items[out].name = gVegaQolMoveTexts[pool[index]];
        items[out].id = pool[index];
        ++out;
    }
    if (out == 0u) {
        FN_FREE(items);
        return VEGA_QOL_EFFECTLESS;
    }
    G_QOL_STATE->wild_token_pid = (u32)(uintptr_t)items;
    G_QOL_STATE->wild_token_armed = out;
    G_QOL_STATE->relearn_box = box;
    G_QOL_STATE->relearn_position = slot;
    G_QOL_STATE->relearn_slot = 0u;
    while (G_QOL_STATE->relearn_slot < 4u
           && FN_GET_BOX_MON_DATA(mon,
                MON_DATA_MOVE1 + G_QOL_STATE->relearn_slot,
                (u8 *)0) != 0u)
        ++G_QOL_STATE->relearn_slot;
    if (G_QOL_STATE->relearn_slot >= 4u)
        G_QOL_STATE->relearn_slot = 0u;
    G_QOL_STATE->relearn_active = 1u;
    status = open_pss_list_menu(items, out, 0u, QOL_PSS_MENU_MOVE);
    if (status != VEGA_QOL_OK) {
        free_relearn_menu_items();
        G_QOL_STATE->relearn_active = 0u;
    }
    return status;
}

static u8 process_relearn_menu(void)
{
    s32 choice = FN_LIST_MENU_INPUT((u8)G_QOL_STATE->last_result);
    u8 operation = G_QOL_STATE->pss_confirm_op;
    VegaQolStatus status = VEGA_QOL_OK;
    if (choice == -1)
        return 0u;
    close_pss_list_menu();
    if (choice == -2) {
        status = VEGA_QOL_CANCELLED;
        goto finish;
    }
    if (operation == QOL_PSS_MENU_MOVE) {
        if (choice <= 0 || choice >= (s32)VEGA_QOL_MOVE_COUNT) {
            status = VEGA_QOL_INVALID_ARGUMENT;
            goto finish;
        }
        G_QOL_STATE->relearn_move = (u16)choice;
        free_relearn_menu_items();
        status = open_pss_list_menu(
            (const VegaQolGeneratedListItem *)gVegaQolMoveSlotItems,
            4u, G_QOL_STATE->relearn_slot, QOL_PSS_MENU_MOVE_SLOT);
        if (status == VEGA_QOL_OK)
            return 0u;
        goto finish;
    }
    if (operation == QOL_PSS_MENU_MOVE_SLOT) {
        if (choice < 0 || choice >= 4) {
            status = VEGA_QOL_INVALID_ARGUMENT;
            goto finish;
        }
        G_QOL_STATE->relearn_slot = (u8)choice;
        status = open_pss_list_menu(
            (const VegaQolGeneratedListItem *)gVegaQolYesNoItems,
            2u, 0u, QOL_PSS_MENU_MOVE_CONFIRM);
        if (status == VEGA_QOL_OK)
            return 0u;
        goto finish;
    }
    if (operation == QOL_PSS_MENU_MOVE_CONFIRM) {
        status = choice == 1
            ? relearn_move(G_QOL_STATE->relearn_box,
                           G_QOL_STATE->relearn_position,
                           G_QOL_STATE->relearn_slot,
                           G_QOL_STATE->relearn_move, 0u)
            : VEGA_QOL_CANCELLED;
    } else {
        status = VEGA_QOL_INVALID_ARGUMENT;
    }

finish:
    free_relearn_menu_items();
    G_QOL_STATE->relearn_active = 0u;
    G_QOL_STATE->pss_confirm_op = 0u;
    G_QOL_STATE->last_result = status;
    show_pc_status(status);
    return 0u;
}

static VegaQolStatus confirm_pc_operation(u8 operation, u8 destination_box)
{
    u8 menu_operation;
    if (selection_count() == 0u)
        return VEGA_QOL_EMPTY_SELECTION;
    if (operation == 1u)
        menu_operation = QOL_PSS_MENU_RELEASE_CONFIRM;
    else if (operation == 2u)
        menu_operation = QOL_PSS_MENU_BOX_MOVE_CONFIRM;
    else if (operation == 3u)
        menu_operation = QOL_PSS_MENU_TAKE_ITEMS_CONFIRM;
    else
        return VEGA_QOL_INVALID_ARGUMENT;
    G_QOL_STATE->last_box = destination_box;
    if (open_pss_list_menu(
            (const VegaQolGeneratedListItem *)gVegaQolYesNoItems,
            2u, 1u, menu_operation) != VEGA_QOL_OK)
        return VEGA_QOL_CAPACITY;
    return VEGA_QOL_CONFIRM_REQUIRED;
}

static u8 process_pc_confirmation_menu(void)
{
    s32 choice = FN_LIST_MENU_INPUT((u8)G_QOL_STATE->last_result);
    u8 operation = G_QOL_STATE->pss_confirm_op;
    VegaQolStatus status;
    if (choice == -1)
        return 0u;
    close_pss_list_menu();
    if (choice != 1) {
        status = VEGA_QOL_CANCELLED;
    } else if (operation == QOL_PSS_MENU_RELEASE_CONFIRM) {
        status = items_then_mutate(1u, 0u);
    } else if (operation == QOL_PSS_MENU_BOX_MOVE_CONFIRM) {
        status = move_selection(G_QOL_STATE->last_box, 0u);
    } else if (operation == QOL_PSS_MENU_TAKE_ITEMS_CONFIRM) {
        status = items_then_mutate(0u, 0u);
    } else {
        status = VEGA_QOL_INVALID_ARGUMENT;
    }
    G_QOL_STATE->pss_confirm_op = 0u;
    G_QOL_STATE->last_result = status;
    show_pc_status(status);
    return 0u;
}

PUBLIC_TEXT(VegaQolProduction_PssHandleInputAdapter)
u8 VegaQolProduction_PssHandleInputAdapter(void)
{
    VegaQolStatus status;
    u16 held;
    u8 box;
    u8 slot;
    ensure_state();
    /* FireRed runs the HELP-button callback before the PSS input task.  With
     * the default HELP option it consumes L/R before SELECT+L/R can reach the
     * production shortcuts.  Suppress HELP for the lifetime of the stock PSS
     * and restore the exact user option on its normal B exit. */
    suppress_help_button_mode();
    if (search_menu_mode() != QOL_SEARCH_MENU_NONE)
        return process_search_menu();
    if (G_QOL_STATE->pss_confirm_op >= QOL_PSS_MENU_MOVE
        && G_QOL_STATE->pss_confirm_op <= QOL_PSS_MENU_MOVE_CONFIRM)
        return process_relearn_menu();
    if (G_QOL_STATE->pss_confirm_op >= QOL_PSS_MENU_RELEASE_CONFIRM
        && G_QOL_STATE->pss_confirm_op
           <= QOL_PSS_MENU_TAKE_ITEMS_CONFIRM)
        return process_pc_confirmation_menu();
    if ((G_MAIN_NEW_KEYS & KEY_SELECT) == 0u) {
        if (pss_judge_mode() != 0u
            && ((G_MAIN_NEW_KEYS_RAW | G_MAIN_HELD_KEYS_RAW
                 | G_MAIN_NEW_KEYS | G_MAIN_REPEAT_KEYS | G_MAIN_HELD_KEYS)
                & (KEY_L | KEY_R))) {
            set_pss_judge_mode(
                ((G_MAIN_NEW_KEYS_RAW | G_MAIN_HELD_KEYS_RAW
                  | G_MAIN_NEW_KEYS | G_MAIN_REPEAT_KEYS | G_MAIN_HELD_KEYS)
                 & KEY_L) ? 1u : 2u);
            G_MAIN_NEW_KEYS_RAW &= (u16)~(KEY_L | KEY_R);
            G_MAIN_NEW_KEYS &= (u16)~(KEY_L | KEY_R);
            G_MAIN_REPEAT_KEYS &= (u16)~(KEY_L | KEY_R);
            update_pc_judge();
            return 0u;
        }
        if (G_MAIN_NEW_KEYS & KEY_B) {
            restore_help_button_mode();
            set_pss_judge_mode(0u);
            G_QOL_STATE->pss_confirm_op = 0u;
            G_QOL_STATE->relearn_active = 0u;
            free_relearn_menu_items();
        }
        u8 result = FN_ORIGINAL_PSS_INPUT();
        update_pc_judge();
        return result;
    }
    box = FN_STORAGE_CURRENT_BOX();
    slot = *(volatile u8 *)(uintptr_t)PSS_CURSOR_POSITION;
    held = G_MAIN_HELD_KEYS;
    if (*(volatile u8 *)(uintptr_t)PSS_CURSOR_AREA != 0u)
        return FN_ORIGINAL_PSS_INPUT();
    G_MAIN_NEW_KEYS &= (u16)~KEY_SELECT;
    if (held & KEY_START)
        status = confirm_pc_operation(1u, box);
    else if (held & KEY_R)
        status = confirm_pc_operation(2u, box);
    else if (held & KEY_L)
        status = open_search_menu(QOL_SEARCH_MENU_CATEGORY);
    else if (held & KEY_A)
        status = confirm_pc_operation(3u, box);
    else if (held & KEY_UP)
        status = open_relearn_move_menu(box, slot);
    else if (held & KEY_DOWN) {
        clear_selection();
        status = VEGA_QOL_OK;
    } else {
        status = toggle_selection(box, slot);
        set_pss_judge_mode(pss_judge_mode() == 0u ? 1u : 0u);
        if (pss_judge_mode() == 0u) {
            FN_REFRESH_PSS_MON_DATA();
            FN_PRINT_PSS_MON_INFO();
        }
    }
    /* A successful modal menu stores its ListMenu task id in last_result.
     * Do not replace that id with VEGA_QOL_OK before the next PSS frame. */
    if (G_QOL_STATE->pss_confirm_op != 0u
        || search_menu_mode() != QOL_SEARCH_MENU_NONE)
        return 0u;
    G_QOL_STATE->last_result = status;
    if (status != VEGA_QOL_OK) {
        show_pc_status(status);
        return 0u;
    }
    update_pc_judge();
    return 0u;
}

static void render_summary_judge(void)
{
    static const TextColor colors = {0u, 1u, 2u};
    u32 summary;
    void *mon;
    u8 window;
    u8 mode;
    u8 stat;
    ensure_state();
    summary = *(volatile u32 *)(uintptr_t)SUMMARY_DATA_SLOT;
    if (!pointer_is_ewram(summary, SUMMARY_CURRENT_MON_OFFSET + 100u))
        return;
    mon = PTR(void *, summary + SUMMARY_CURRENT_MON_OFFSET);
    mode = summary_judge_mode();
    /* During summary setup the right-pane window slot is not initialized yet.
     * Calling FillWindowPixelBuffer with that transient id corrupts the
     * freshly allocated summary tail.  The stock path also owns every page
     * render until Skills has reached its normal input state. */
    if (mode == 0u
        || *(volatile u8 *)(uintptr_t)(summary + SUMMARY_PAGE_OFFSET) != 1u
        || *(volatile u8 *)(uintptr_t)(summary + SUMMARY_INPUT_STATE_OFFSET)
               != 2u) {
        VegaQolProduction_OriginalPrintSkillsPage();
        return;
    }
    window = *(volatile u8 *)(uintptr_t)(summary
             + SUMMARY_WINDOW_IDS_OFFSET + 3u);
    FN_FILL_WINDOW(window, 0u);
    for (stat = 0u; stat < 6u; ++stat) {
        u8 at;
        clear_bytes(G_QOL_STATE->judge_iv,
                    sizeof(G_QOL_STATE->judge_iv));
        G_QOL_STATE->judge_iv[0] = 0xFFu;
        at = append_stat_judge(G_QOL_STATE->judge_iv, 0u,
                               sizeof(G_QOL_STATE->judge_iv), mon,
                               stat, mode, 0u);
        if (mode == 2u && stat == 5u) {
            at = append_encoded(G_QOL_STATE->judge_iv, at,
                                gVegaQolSeparator,
                                sizeof(G_QOL_STATE->judge_iv));
            at = append_encoded(G_QOL_STATE->judge_iv, at,
                                gVegaQolTotalText,
                                sizeof(G_QOL_STATE->judge_iv));
            at = append_number(G_QOL_STATE->judge_iv, at,
                               mon_ev_total(mon), 3u,
                               sizeof(G_QOL_STATE->judge_iv));
            at = append_encoded(G_QOL_STATE->judge_iv, at,
                                gVegaQolSeparator,
                                sizeof(G_QOL_STATE->judge_iv));
            (void)append_number(G_QOL_STATE->judge_iv, at, 510u, 3u,
                                sizeof(G_QOL_STATE->judge_iv));
        }
        FN_WINDOW_PRINT(window, 2u, 2u, (u8)(3u + stat * 16u),
                        &colors, 0xFFu, G_QOL_STATE->judge_iv);
    }
    FN_COPY_WINDOW_TO_VRAM(window, 2u);
}

PUBLIC_TEXT(VegaQolProduction_PrintSkillsPageAdapter)
void VegaQolProduction_PrintSkillsPageAdapter(void)
{
    render_summary_judge();
}

PUBLIC_TEXT(VegaQolProduction_SummaryInputAdapter)
void VegaQolProduction_SummaryInputAdapter(u8 task_id)
{
    u32 summary;
    u8 mode;
    ensure_state();
    summary = *(volatile u32 *)(uintptr_t)SUMMARY_DATA_SLOT;
    if (!pointer_is_ewram(summary, SUMMARY_CURRENT_MON_OFFSET + 100u)) {
        FN_ORIGINAL_SUMMARY_INPUT(task_id);
        return;
    }
    if (*(volatile u8 *)(uintptr_t)(summary + SUMMARY_PAGE_OFFSET) != 1u) {
        restore_help_button_mode();
        set_summary_judge_mode(0u);
        FN_ORIGINAL_SUMMARY_INPUT(task_id);
        return;
    }
    if (*(volatile u8 *)(uintptr_t)(summary + SUMMARY_INPUT_STATE_OFFSET)
        != 2u) {
        FN_ORIGINAL_SUMMARY_INPUT(task_id);
        return;
    }
    mode = summary_judge_mode();
    if (G_MAIN_NEW_KEYS & KEY_SELECT) {
        set_summary_judge_mode(mode == 0u ? 1u : 0u);
        if (summary_judge_mode() != 0u)
            suppress_help_button_mode();
        else
            restore_help_button_mode();
        G_MAIN_NEW_KEYS &= (u16)~KEY_SELECT;
        render_summary_judge();
        return;
    }
    if (mode != 0u && (G_MAIN_NEW_KEYS & (KEY_L | KEY_R))) {
        set_summary_judge_mode((G_MAIN_NEW_KEYS & KEY_L) ? 1u : 2u);
        G_MAIN_NEW_KEYS &= (u16)~(KEY_L | KEY_R);
        render_summary_judge();
        return;
    }
    if (G_MAIN_NEW_KEYS & KEY_B) {
        restore_help_button_mode();
        set_summary_judge_mode(0u);
    }
    FN_ORIGINAL_SUMMARY_INPUT(task_id);
}

PUBLIC_TEXT(VegaQolProduction_GetTextSpeedDelay)
u8 VegaQolProduction_GetTextSpeedDelay(void)
{
    if (!ensure_save())
        return 1u;
    if (gVegaModernSaveData->text_speed == VEGA_TEXT_INSTANT)
        return 0x7Fu;
    return gVegaModernSaveData->text_speed == VEGA_TEXT_FAST ? 1u : 2u;
}

PUBLIC_TEXT(VegaQolProduction_RunTextPrintersForInstantText)
u8 VegaQolProduction_RunTextPrintersForInstantText(void)
{
    u8 i;
    u8 instant = (u8)(gVegaModernSaveData->magic == VEGA_SAVE_MAGIC
        && gVegaModernSaveData->text_speed == VEGA_TEXT_INSTANT);

    for (i = 0u; i < 32u; ++i) {
        QolTextPrinter *printer = &G_TEXT_PRINTERS[i];
        u16 j;
        if (printer->active == 0u)
            continue;
        if (!instant || printer->state != 0u) {
            u16 result = (u16)FN_RENDER_FONT(printer);
            if (result == 1u) {
                printer->active = 0u;
            } else if (result == 0u) {
                FN_COPY_WINDOW_TO_VRAM(
                    printer->printer_template.attributes[0], 2u);
            }
            if ((result == 0u || result == 3u)
                && printer->callback != (QolTextPrinterCallback)0) {
                printer->callback(&printer->printer_template, result);
            }
            continue;
        }
        for (j = 0u; j < 0x400u; ++j) {
            u8 old_state = printer->state;
            u16 result = (u16)FN_RENDER_FONT(printer);
            u8 new_state = printer->state;
            if (result == 0u) {
                if (printer->callback != (QolTextPrinterCallback)0)
                    printer->callback(&printer->printer_template, result);
            } else if (result == 3u) {
                if (printer->callback != (QolTextPrinterCallback)0)
                    printer->callback(&printer->printer_template, result);
                /* Handle characters immediately, but leave the newly entered
                 * control state for the stock loop on the next frame. */
                if (old_state == 0u && new_state != 0u)
                    FN_COPY_WINDOW_TO_VRAM(
                        printer->printer_template.attributes[0], 2u);
                break;
            } else if (result == 1u) {
                FN_COPY_WINDOW_TO_VRAM(
                    printer->printer_template.attributes[0], 2u);
                printer->active = 0u;
                break;
            }
            if (new_state != 0u)
                break;
        }
    }
    return 1u;
}

static u8 panel_state_index(u8 panel)
{
    if (!ensure_save())
        return 0u;
    if (panel == 0u)
        return gVegaModernSaveData->text_speed;
    if (panel == 1u)
        return (u8)(gVegaModernSaveData->exp_share_enabled != 0u);
    if (panel == 2u)
        return gVegaModernSaveData->hatch_mode;
    if (panel == 3u) {
        u8 region = gVegaModernSaveData->current_region < VEGA_REGION_COUNT
            ? gVegaModernSaveData->current_region : 0u;
        return gVegaModernSaveData->encounter_profile[region];
    }
    if (panel == 6u)
        return G_QOL_STATE->hyper_stat <= 6u
            ? G_QOL_STATE->hyper_stat : 0u;
    if (panel == 8u)
        return (u8)(FN_FLAG_GET(FLAG_QOL_EGG_BASKET) != 0u);
    if (panel == 9u) {
        if (VegaQolProduction_FeatureUnlocked(VEGA_QOL_EVERSTONE_SUPPLY)
            && !reward_claimed(195u))
            return 1u;
        if (VegaQolProduction_FeatureUnlocked(VEGA_QOL_EXP_CANDY_M_ONCE)
            && !reward_claimed(990u))
            return 2u;
        if (VegaQolProduction_FeatureUnlocked(VEGA_QOL_POWER_ITEMS)
            && !reward_claimed(856u))
            return 3u;
        if (VegaQolProduction_FeatureUnlocked(VEGA_QOL_EXP_CANDY_XL_ONCE)
            && !reward_claimed(992u))
            return 4u;
        if (kanto_daycare_quest()
            && (!reward_claimed(902u) || !reward_claimed(684u)))
            return 5u;
        return 0u;
    }
    return 0u;
}

static u8 selected_supply_index(void)
{
    u8 start = (u8)(G_QOL_STATE->pss_confirm_op
                    % VEGA_QOL_SUPPLY_CATALOG_COUNT);
    u8 offset;
    for (offset = 0u; offset < VEGA_QOL_SUPPLY_CATALOG_COUNT; ++offset) {
        u8 index = (u8)((start + offset)
                        % VEGA_QOL_SUPPLY_CATALOG_COUNT);
        if (supply_entry_unlocked(index)) {
            G_QOL_STATE->pss_confirm_op = index;
            return index;
        }
    }
    return 0xFFu;
}

static void cycle_supply(s8 direction)
{
    u8 current = selected_supply_index();
    u8 offset;
    if (current == 0xFFu)
        return;
    for (offset = 1u; offset <= VEGA_QOL_SUPPLY_CATALOG_COUNT; ++offset) {
        s16 candidate = (s16)current + (s16)direction * offset;
        while (candidate < 0)
            candidate += VEGA_QOL_SUPPLY_CATALOG_COUNT;
        candidate %= VEGA_QOL_SUPPLY_CATALOG_COUNT;
        if (supply_entry_unlocked((u8)candidate)) {
            G_QOL_STATE->pss_confirm_op = (u8)candidate;
            return;
        }
    }
}

static void print_panel(void)
{
    u8 panel = G_QOL_STATE->panel_index % VEGA_QOL_PANEL_COUNT;
    u8 state = panel_state_index(panel);
    if (G_QOL_STATE->panel_status_active != 0u) {
        u16 status = G_QOL_STATE->last_result;
        if (status > VEGA_QOL_ALREADY_CLAIMED)
            status = VEGA_QOL_INVALID_ARGUMENT;
        FN_PRINT_HELP(gVegaQolStatusMessages[status], 2u);
        return;
    }
    if (G_QOL_STATE->panel_confirm != 0u) {
        FN_PRINT_HELP(gVegaQolConfirmMessage, 2u);
        return;
    }
    if (panel == 9u) {
        FN_PRINT_HELP(gVegaQolOneTimeRewardMessages[state], 2u);
        return;
    }
    if (panel == 10u) {
        u8 supply = selected_supply_index();
        if (supply != 0xFFu) {
            FN_PRINT_HELP(gVegaQolSupplyMessages[supply], 2u);
            return;
        }
    }
    if (state >= VEGA_QOL_PANEL_STATE_COUNT)
        state = 0u;
    FN_PRINT_HELP(gVegaQolPanelMessages[panel][state], 2u);
}

static VegaQolStatus open_field_pc(void)
{
    u8 *save = (u8 *)save_block1();
    VegaQolStatus status;
    if (save == (void *)0)
        return VEGA_QOL_CONTEXT_FORBIDDEN;
    status = field_pc_allowed(save[SAVE_LOCATION_OFFSET],
                              save[SAVE_LOCATION_OFFSET + 1u]);
    if (status != VEGA_QOL_OK)
        return status;
    FN_DESTROY_HELP();
    FN_CLOSE_START_MENU();
    G_QOL_STATE->panel_active = 0u;
    (void)FN_SHOW_PSS();
    return VEGA_QOL_OK;
}

PUBLIC_TEXT(VegaQolProduction_StartMenuPanel)
u8 VegaQolProduction_StartMenuPanel(void)
{
    VegaQolStatus status = VEGA_QOL_OK;
    u16 keys = G_MAIN_NEW_KEYS;
    ensure_state();
    if (G_QOL_STATE->panel_status_active != 0u) {
        if (keys & (KEY_A | KEY_B)) {
            G_QOL_STATE->panel_status_active = 0u;
            print_panel();
        }
        return 0u;
    }
    if ((G_QOL_STATE->panel_index == 6u
         || G_QOL_STATE->panel_index == 7u)
        && (keys & (KEY_L | KEY_R))) {
        u8 count = *(volatile u8 *)(uintptr_t)PLAYER_PARTY_COUNT;
        if (count != 0u) {
            if (keys & KEY_R)
                G_QOL_STATE->last_box =
                    (u8)((G_QOL_STATE->last_box + 1u) % count);
            else
                G_QOL_STATE->last_box =
                    (u8)((G_QOL_STATE->last_box + count - 1u) % count);
        }
        print_panel();
        return 0u;
    }
    if (keys & KEY_LEFT) {
        G_QOL_STATE->panel_confirm = 0u;
        G_QOL_STATE->panel_status_active = 0u;
        G_QOL_STATE->panel_index = (u8)((G_QOL_STATE->panel_index
            + VEGA_QOL_PANEL_COUNT - 1u) % VEGA_QOL_PANEL_COUNT);
        print_panel();
        return 0u;
    }
    if (keys & KEY_RIGHT) {
        G_QOL_STATE->panel_confirm = 0u;
        G_QOL_STATE->panel_status_active = 0u;
        G_QOL_STATE->panel_index = (u8)((G_QOL_STATE->panel_index + 1u)
                                        % VEGA_QOL_PANEL_COUNT);
        print_panel();
        return 0u;
    }
    if (G_QOL_STATE->panel_index == 6u && (keys & (KEY_UP | KEY_DOWN))) {
        if (keys & KEY_UP)
            G_QOL_STATE->hyper_stat =
                (u8)((G_QOL_STATE->hyper_stat + 1u) % 7u);
        else
            G_QOL_STATE->hyper_stat =
                (u8)((G_QOL_STATE->hyper_stat + 6u) % 7u);
        print_panel();
        return 0u;
    }
    if (G_QOL_STATE->panel_index == 10u && (keys & (KEY_UP | KEY_DOWN))) {
        G_QOL_STATE->panel_confirm = 0u;
        G_QOL_STATE->panel_status_active = 0u;
        cycle_supply((keys & KEY_DOWN) ? 1 : -1);
        print_panel();
        return 0u;
    }
    if ((keys & KEY_B) && G_QOL_STATE->panel_confirm != 0u) {
        G_QOL_STATE->panel_confirm = 0u;
        G_QOL_STATE->last_result = VEGA_QOL_CANCELLED;
        print_panel();
        return 0u;
    }
    if ((keys & KEY_A)
        && (G_QOL_STATE->panel_index == 5u
            || G_QOL_STATE->panel_index == 6u
            || G_QOL_STATE->panel_index == 7u
            || G_QOL_STATE->panel_index == 9u
            || G_QOL_STATE->panel_index == 10u)) {
        u8 token = (u8)(G_QOL_STATE->panel_index + 1u);
        if (G_QOL_STATE->panel_confirm != token) {
            G_QOL_STATE->panel_confirm = token;
            G_QOL_STATE->last_result = VEGA_QOL_CONFIRM_REQUIRED;
            print_panel();
            return 0u;
        }
        G_QOL_STATE->panel_confirm = 0u;
    }
    if (keys & KEY_B)
        G_QOL_STATE->panel_index = VEGA_QOL_PANEL_COUNT - 1u;
    if ((keys & KEY_A) || (keys & KEY_B)) {
        switch (G_QOL_STATE->panel_index) {
        case 0u:
            status = commit_setting(VEGA_QOL_SERVICE_SET_TEXT_SPEED,
                (u8)((panel_state_index(0u) + 1u) % 3u));
            break;
        case 1u:
            status = commit_setting(VEGA_QOL_SERVICE_SET_EXP_SHARE,
                (u8)(panel_state_index(1u) == 0u));
            break;
        case 2u:
            status = commit_setting(VEGA_QOL_SERVICE_SET_HATCH_MODE,
                (u8)((panel_state_index(2u) + 1u) % 3u));
            break;
        case 3u:
            status = commit_setting(VEGA_QOL_SERVICE_SET_RESEARCH_PROFILE,
                (u8)(panel_state_index(3u) == 0u));
            break;
        case 4u:
            status = open_field_pc();
            break;
        case 5u:
            {
                u8 *save = (u8 *)save_block1();
                status = save == (void *)0 ? VEGA_QOL_CONTEXT_FORBIDDEN
                    : field_map_context_allowed(save[SAVE_LOCATION_OFFSET],
                        save[SAVE_LOCATION_OFFSET + 1u], 1u);
                if (status == VEGA_QOL_OK)
                    status = claim_egg_queue(0u);
            }
            break;
        case 6u:
            status = hyper_train_party(G_QOL_STATE->last_box,
                                       G_QOL_STATE->hyper_stat, 0u);
            break;
        case 7u:
            status = ev_reset_all_party(G_QOL_STATE->last_box, 0u);
            break;
        case 8u:
            if (!FN_FLAG_GET(FLAG_QOL_DAYCARE_QUEST)) {
                status = VEGA_QOL_LOCKED;
                break;
            }
            {
                u8 *save = (u8 *)save_block1();
                status = save == (void *)0 ? VEGA_QOL_CONTEXT_FORBIDDEN
                    : field_map_context_allowed(save[SAVE_LOCATION_OFFSET],
                        save[SAVE_LOCATION_OFFSET + 1u], 1u);
                if (status == VEGA_QOL_OK)
                    status = set_egg_basket(
                        (u8)(FN_FLAG_GET(FLAG_QOL_EGG_BASKET) == 0u));
            }
            break;
        case 9u:
            {
                u8 reward_state = panel_state_index(9u);
                status = reward_state == 0u ? VEGA_QOL_LOCKED
                    : (VegaQolStatus)VegaQolProduction_ClaimOneTimeReward(
                        (u8)(reward_state - 1u));
            }
            break;
        case 10u:
            {
                u8 supply = selected_supply_index();
                status = supply == 0xFFu ? VEGA_QOL_LOCKED
                    : (VegaQolStatus)VegaQolProduction_PurchaseSupply(supply);
            }
            break;
        default:
            G_QOL_STATE->panel_active = 0u;
            G_START_MENU_CALLBACK = START_MENU_INPUT_CALLBACK;
            return 0u;
        }
        G_QOL_STATE->last_result = status;
        if (G_QOL_STATE->panel_active) {
            G_QOL_STATE->panel_status_active = 1u;
            print_panel();
        }
    }
    return 0u;
}

PUBLIC_TEXT(VegaQolProduction_ReadKeysAdapter)
void VegaQolProduction_ReadKeysAdapter(void)
{
    VegaQolProduction_OriginalReadKeys();
    ensure_state();
    if (G_MAIN_CALLBACK2 == OVERWORLD_CALLBACK
        && G_START_MENU_CALLBACK == START_MENU_INPUT_CALLBACK
        && (G_MAIN_NEW_KEYS & KEY_SELECT)) {
        G_MAIN_NEW_KEYS &= (u16)~KEY_SELECT;
        G_MAIN_REPEAT_KEYS &= (u16)~KEY_SELECT;
        G_QOL_STATE->panel_active = 1u;
        G_QOL_STATE->panel_index = 0u;
        G_START_MENU_CALLBACK = (u32)(uintptr_t)VegaQolProduction_StartMenuPanel | 1u;
        print_panel();
    }
    /* Movement remains owned by the linked CFRU ShouldPlayerRun/MoveOnBike
     * paths.  They already interpret B relative to FLAG_AUTO_RUN (0x914) and
     * FLAG_BIKE_TURBO_BOOST (0x91F), including the existing L-button toggle.
     * Rewriting B here would invert those modes twice and break tile-input
    * semantics after a toggle. */
}

PUBLIC_TEXT(VegaQolProduction_Probe)
u32 VegaQolProduction_Probe(u32 selector)
{
    ensure_state();
    switch (selector) {
    case 0u: return VEGA_QOL_PRODUCTION_MAGIC;
    case 1u: return 1u;
    case 2u: return VEGA_QOL_FEATURE_COUNT;
    case 3u: return VEGA_QOL_BOX_COUNT;
    case 4u: return selection_count();
    case 5u: return G_QOL_STATE->last_result;
    case 6u: return G_QOL_STATE->auto_active;
    case 7u: return ensure_save() ? gVegaModernSaveData->egg_queue_count : 0u;
    case 8u: return ensure_save() ? gVegaModernSaveData->text_speed : 0u;
    case 9u: return *(volatile u16 *)(uintptr_t)QOL_BASKET_COUNTER;
    case 10u:
        return (u32)((G_QOL_STATE->auto_move_slot
                      & QOL_STATE_HIGH_RAID_PENDING) != 0u
                     && FN_CFRU_IS_RAID());
    case 11u:
        return (u32)((G_QOL_STATE->auto_move_slot
                      & QOL_STATE_LATE_GIMMICK_PENDING) != 0u);
    default: return 0u;
    }
}

PUBLIC_TEXT(VegaQolProduction_Dispatch)
u32 VegaQolProduction_Dispatch(u16 service, u32 a, u32 b, u32 c)
{
    VegaQolStatus status;
    ensure_state();
    switch ((VegaQolService)service) {
    case VEGA_QOL_SERVICE_PROBE:
        return VegaQolProduction_Probe(a);
    case VEGA_QOL_SERVICE_FEATURE_UNLOCKED:
        return VegaQolProduction_FeatureUnlocked((u16)a);
    case VEGA_QOL_SERVICE_PC_CLEAR_SELECTION:
        clear_selection();
        status = VEGA_QOL_OK;
        break;
    case VEGA_QOL_SERVICE_PC_TOGGLE_SELECTION:
        status = toggle_selection((u8)a, (u8)b);
        break;
    case VEGA_QOL_SERVICE_PC_SEARCH:
        status = pointer_is_ewram(a, sizeof(VegaQolSearchFilter))
            ? search_and_select(PTR(const VegaQolSearchFilter *, a))
            : VEGA_QOL_INVALID_ARGUMENT;
        break;
    case VEGA_QOL_SERVICE_PC_MOVE:
        status = move_selection((u8)a, (u8)b);
        break;
    case VEGA_QOL_SERVICE_PC_RELEASE:
        status = items_then_mutate(1u, (u8)a);
        break;
    case VEGA_QOL_SERVICE_PC_TAKE_ITEMS:
        status = items_then_mutate(0u, (u8)a);
        break;
    case VEGA_QOL_SERVICE_PC_RELEARN:
        status = relearn_move((u8)a, (u8)b, (u8)(b >> 8),
                              (u16)c, (u8)(b >> 16));
        break;
    case VEGA_QOL_SERVICE_FIELD_PC_ALLOWED:
        status = field_pc_allowed((u8)a, (u8)b);
        break;
    case VEGA_QOL_SERVICE_EGG_QUEUE_CLAIM:
        status = claim_egg_queue((u8)a);
        break;
    case VEGA_QOL_SERVICE_AUTO_BATTLE_ALLOWED:
        status = auto_battle_allowed_values(a, (u8)b, (u8)c)
            ? VEGA_QOL_OK : VEGA_QOL_CONTEXT_FORBIDDEN;
        break;
    case VEGA_QOL_SERVICE_SET_TEXT_SPEED:
    case VEGA_QOL_SERVICE_SET_EXP_SHARE:
    case VEGA_QOL_SERVICE_SET_HATCH_MODE:
    case VEGA_QOL_SERVICE_SET_RESEARCH_PROFILE:
        status = commit_setting((u8)service, (u8)a);
        break;
    case VEGA_QOL_SERVICE_SELECTION_COUNT:
        return selection_count();
    case VEGA_QOL_SERVICE_HYPER_TRAIN_PARTY:
        status = hyper_train_party((u8)a, (u8)b, (u8)c);
        break;
    case VEGA_QOL_SERVICE_EV_RESET_ALL_PARTY:
        status = ev_reset_all_party((u8)a, (u8)b);
        break;
    case VEGA_QOL_SERVICE_SET_DAYCARE_QUEST:
        status = set_daycare_quest((u8)a);
        break;
    case VEGA_QOL_SERVICE_SET_EGG_BASKET:
        status = set_egg_basket((u8)a);
        break;
    case VEGA_QOL_SERVICE_CLAIM_ONE_TIME_REWARD:
        status = (VegaQolStatus)VegaQolProduction_ClaimOneTimeReward((u8)a);
        break;
    case VEGA_QOL_SERVICE_PURCHASE_SUPPLY:
        status = (VegaQolStatus)VegaQolProduction_PurchaseSupply((u8)a);
        break;
    case VEGA_QOL_SERVICE_SUPPLY_AVAILABLE:
        if (a >= VEGA_QOL_SUPPLY_CATALOG_COUNT)
            status = VEGA_QOL_INVALID_ARGUMENT;
        else
            status = supply_entry_available((u16)a)
                ? VEGA_QOL_OK : VEGA_QOL_LOCKED;
        break;
    case VEGA_QOL_SERVICE_CONFIGURE_HIGH_RAID:
        status = (VegaQolStatus)VegaQolProduction_ConfigureHighRaid();
        break;
    case VEGA_QOL_SERVICE_CONFIGURE_LOW_RAID:
        status = (VegaQolStatus)VegaQolProduction_ConfigureLowRaid();
        break;
    default:
        status = VEGA_QOL_INVALID_ARGUMENT;
        break;
    }
    G_QOL_STATE->last_result = status;
    return status;
}
