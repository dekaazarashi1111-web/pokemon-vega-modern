/* T27 Stage 44: Codex-controlled 6->3 battle runtime. */

#include "codex_battle_runtime.h"

#include <stddef.h>
#include <stdint.h>

#define CBR_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))
#define PTR(type, address) ((type)(uintptr_t)(address))

typedef uint8_t u8;
typedef int8_t s8;
typedef uint16_t u16;
typedef uint32_t u32;

typedef struct Pokemon100 { u8 bytes[100]; } Pokemon100;

typedef void (*VoidFn)(void);
typedef u8 (*U8Fn)(u8);
typedef u16 (*U16FromU8Fn)(u8);
typedef u8 (*PolicyCanFn)(u8, u8);
typedef u8 (*PolicyMarkFn)(u8);
typedef u8 (*VarSetFn)(u16, u16);
typedef u16 (*VarGetFn)(u16);
typedef u8 (*FlagFn)(u16);
typedef u32 (*GetMonDataFn)(const void *, int, u8 *);
typedef void (*SetMonDataFn)(void *, int, const void *);
typedef void (*CreateMonFn)(void *, u16, u8, u8, u8, u32, u8, u32);
typedef void (*CalculateStatsFn)(void *);
typedef u8 (*CalculatePpFn)(u16, u8, u8);
typedef u8 (*GetGenderFn)(u16, u32);
typedef u8 (*IsShinyFn)(u32, u32);
typedef u8 (*CalculatePartyCountFn)(void);
typedef void (*PrepareBufferFn)(u8, u8 *, u16);
typedef void (*EmitTwoFn)(u8, u8, u16);
typedef void (*EmitMonFn)(u8, u8, u8 *);
typedef const void *(*CanMegaFn)(u8, u8);
typedef u16 (*CanZFn)(u8, u8, u16);
typedef u8 (*CanGimmickFn)(u8);

void CodexBattleRuntime_OpponentController(void);

enum {
    CBR_STATE_MAGIC = 0x32524243u, /* CBR2 */
    CBR_STATUS_READY = 1u,
    CBR_STATUS_ACCEPTED = 2u,
    CBR_STATUS_ERROR = 3u,
    CBR_STATUS_WAITING = 4u,
    CBR_STATUS_ACTIVE = 5u,
    CBR_STATUS_RESULT = 6u,
    CBR_ACTION_MOVE = 1u,
    CBR_ACTION_SWITCH = 2u,
    CBR_ACTION_FORFEIT = 3u,
    CBR_ACTION_CPU = 4u,
    CBR_DISCONNECT_WAIT = 0u,
    CBR_DISCONNECT_CPU = 1u,
    CBR_DISCONNECT_FORFEIT = 2u,
    CBR_GIMMICK_NONE = 0u,
    CBR_GIMMICK_MEGA = 1u,
    CBR_GIMMICK_Z = 2u,
    CBR_GIMMICK_DYNAMAX = 3u,
    CBR_GIMMICK_TERA = 4u,
    CBR_TEAM_SIZE = 6u,
    CBR_SELECTION_SIZE = 3u,
    CBR_MON_SIZE = 100u,
    CBR_REQUEST_CRC_SIZE = 84u,
    CBR_REQUEST_COPY_SIZE = 92u,
    CBR_BATTLE_TYPE_TRAINER = 0x0008u,
    CBR_BATTLE_TYPE_DYNAMAX = 0x40000000u,
    CBR_CONTROLLER_CHOOSEACTION = 18u,
    CBR_CONTROLLER_CHOOSEMOVE = 20u,
    CBR_CONTROLLER_CHOOSEPOKEMON = 22u,
    CBR_CONTROLLER_PRINTSTRING = 16u,
    CBR_CONTROLLER_BATTLEANIMATION = 52u,
    CBR_STRING_CUSTOM = 388u,
    CBR_EVENT_ABILITY_POPUP = 389u,
    CBR_ANIM_LOAD_ABILITY_POPUP = 0x42u,
    CBR_ACTION_USE_MOVE = 0u,
    CBR_ENGINE_ACTION_SWITCH = 2u,
    CBR_ENGINE_ACTION_RUN = 3u,
    CBR_CONTROLLER_TWO_RETURN_VALUES = 33u,
    CBR_ACTION_RUN_BATTLESCRIPT = 10u,
    CBR_MON_DATA_PERSONALITY = 0u,
    CBR_MON_DATA_OT_ID = 1u,
    CBR_MON_DATA_SPECIES = 11u,
    CBR_MON_DATA_HELD_ITEM = 12u,
    CBR_MON_DATA_MOVE1 = 13u,
    CBR_MON_DATA_PP1 = 17u,
    CBR_MON_DATA_PP_BONUSES = 21u,
    CBR_MON_DATA_EXP = 25u,
    CBR_MON_DATA_EV_HP = 26u,
    CBR_MON_DATA_IV_HP = 39u,
    CBR_MON_DATA_IS_EGG = 45u,
    CBR_MON_DATA_LEVEL = 56u,
    CBR_MON_DATA_STATUS = 55u,
    CBR_MON_DATA_HP = 57u,
    CBR_MON_DATA_MAX_HP = 58u,
    CBR_NATURE_MINT_OFFSET = 0x0Fu,
    CBR_TERA_TYPE_OFFSET = 0x11u,
    CBR_MET_BITS_OFFSET = 0x46u,
    CBR_IV_BITS_OFFSET = 0x48u,
    CBR_HP_OFFSET = 0x56u,
    CBR_MAX_HP_OFFSET = 0x58u,
    CBR_HIDDEN_ABILITY_MASK = 0x1000u,
    CBR_ABILITY_NUM_MASK = 0x80000000u,
    CBR_FLAG_BATTLE_FACILITY = 0x0930u,
    CBR_FLAG_DISABLE_BAG = 0x0915u,
    CBR_FLAG_CODEX_TRAINER = 0x07E9u,
    CBR_VAR_FACILITY_NUMBER = 0x403Au,
    CBR_VAR_PARTY_SIZE = 0x5015u,
    CBR_VAR_LEVEL = 0x5016u,
    CBR_VAR_BATTLE_TYPE = 0x5017u,
    CBR_VAR_TIER = 0x5018u,
    CBR_TIER_NO_RESTRICTIONS = 1u,
    CBR_RESULT_OK = 1u,
    CBR_RESULT_NOT_READY = 2u,
    CBR_RESULT_INVALID = 3u,
    CBR_RESULT_CANCELLED = 4u,
    CBR_RESULT_BUSY = 5u,
    CBR_CLEANUP_WIN = 1u,
    CBR_CLEANUP_LOSS = 2u,
    CBR_CLEANUP_FORFEIT = 3u,
    CBR_CLEANUP_ABORT = 4u,
    CBR_CLEANUP_RESET = 5u,
    CBR_PRIVATE_COMMAND_SIZE = 16u,
    CBR_PRESENCE_ITEM = 1u,
    CBR_PRESENCE_MOVES = 2u,
    CBR_PRESENCE_ABILITY = 4u,
    CBR_PRESENCE_NATURE = 8u,
    CBR_PRESENCE_IVS = 16u,
    CBR_PRESENCE_EVS = 32u,
    CBR_PRESENCE_SHINY = 64u,
    CBR_PRESENCE_TERA = 128u,
    CBR_SWITCH_NONE = 0u,
    CBR_SWITCH_VOLUNTARY = 1u,
    CBR_SWITCH_FORCED = 2u,
    CBR_PUBLIC_EVENT_CAPACITY = 4u,
    CBR_PUBLIC_STATE_VERSION = 2u,
    CBR_BATTLE_MON_SIZE = 0x58u,
    CBR_BATTLE_MON_ATTACK_OFFSET = 0x02u,
    CBR_BATTLE_MON_MOVES_OFFSET = 0x0Cu,
    CBR_BATTLE_MON_STAT_STAGES_OFFSET = 0x19u,
    CBR_BATTLE_MON_TYPE3_OFFSET = 0x18u,
    CBR_BATTLE_MON_TYPE1_OFFSET = 0x21u,
    CBR_BATTLE_MON_TYPE2_OFFSET = 0x22u,
    CBR_BATTLE_MON_PP_OFFSET = 0x24u,
    CBR_BATTLE_MON_HP_OFFSET = 0x28u,
    CBR_BATTLE_MON_LEVEL_OFFSET = 0x2Au,
    CBR_BATTLE_MON_MAX_HP_OFFSET = 0x2Cu,
    CBR_BATTLE_MON_ITEM_OFFSET = 0x2Eu,
    CBR_BATTLE_MON_ABILITY_OFFSET = 0x38u,
    CBR_BATTLE_MON_STATUS1_OFFSET = 0x4Cu,
    CBR_BATTLE_MON_STATUS2_OFFSET = 0x50u,
    CBR_NEWBS_Z_USED_OFFSET = 0x240u,
    CBR_NEWBS_DMAX_USED_OFFSET = 0x24Eu,
    CBR_NEWBS_DMAX_TIMER_OFFSET = 0x252u,
    CBR_NEWBS_TERA_DONE_OFFSET = 0x26Cu,
    CBR_NEWBS_AI_ABILITIES_OFFSET = 0x29Eu,
    CBR_NEWBS_DISGUISED_AS_OFFSET = 0x0B0u,
    CBR_NEWBS_TELEKINESIS_OFFSET = 0x20u,
    CBR_NEWBS_MAGNET_RISE_OFFSET = 0x24u,
    CBR_NEWBS_HEAL_BLOCK_OFFSET = 0x28u,
    CBR_NEWBS_LASER_FOCUS_OFFSET = 0x2Cu,
    CBR_NEWBS_THROAT_CHOP_OFFSET = 0x30u,
    CBR_NEWBS_EMBARGO_OFFSET = 0x34u,
    CBR_NEWBS_ELECTRIFY_OFFSET = 0x38u,
    CBR_NEWBS_SLOW_START_OFFSET = 0x3Cu,
    CBR_NEWBS_GLAIVE_RUSH_OFFSET = 0xBCu,
    CBR_NEWBS_SYRUP_BOMB_OFFSET = 0xCCu,
    CBR_NEWBS_DRAGON_CHEER_OFFSET = 0xD0u,
    CBR_NEWBS_CUD_CHEW_OFFSET = 0xE0u,
    CBR_NEWBS_PARADOX_STAT_OFFSET = 0xE4u,
    CBR_NEWBS_ROOST_BITS_OFFSET = 0x121u,
    CBR_NEWBS_HEALING_WISH_BITS_OFFSET = 0x125u,
    CBR_NEWBS_POWDER_BITS_OFFSET = 0x126u,
    CBR_NEWBS_TAR_SHOT_BITS_OFFSET = 0x128u,
    CBR_NEWBS_OCTOLOCK_BITS_OFFSET = 0x129u,
    CBR_NEWBS_NO_RETREAT_BITS_OFFSET = 0x12Au,
    CBR_NEWBS_SALT_CURE_BITS_OFFSET = 0x134u,
    CBR_DISABLE_STRUCT_SIZE = 0x1Cu,
    CBR_PROTECT_USES_OFFSET = 0x08u,
    CBR_STOCKPILE_OFFSET = 0x09u,
    CBR_DISABLE_MOVE_OFFSET = 0x04u,
    CBR_ENCORE_MOVE_OFFSET = 0x06u,
    CBR_DISABLE_TIMER_OFFSET = 0x0Bu,
    CBR_ENCORE_TIMER_OFFSET = 0x0Eu,
    CBR_PERISH_TIMER_OFFSET = 0x0Fu,
    CBR_FURY_CUTTER_OFFSET = 0x10u,
    CBR_ROLLOUT_TIMER_OFFSET = 0x11u,
    CBR_CHARGE_TIMER_OFFSET = 0x12u,
    CBR_TAUNT_TIMER_OFFSET = 0x13u,
    CBR_BOOSTER_ENERGY_OFFSET = 0x1Bu,
    CBR_STATUS3_SWITCH_IN_ABILITY_DONE = 0x00080000u,
    CBR_STATUS3_ILLUSION = 0x80000000u,
    CBR_PUBLIC_DISABLED = 0x00000002u,
    CBR_PUBLIC_ENCORED = 0x00000004u,
    CBR_PUBLIC_TAUNT = 0x00000020u,
    CBR_PUBLIC_MAGNET_RISE = 0x00000040u,
    CBR_PUBLIC_HEAL_BLOCK = 0x00000200u,
    CBR_PUBLIC_LASER_FOCUS = 0x00000800u,
    CBR_PUBLIC_THROAT_CHOP = 0x00004000u,
    CBR_PUBLIC_EMBARGO = 0x00008000u,
    CBR_PUBLIC_ELECTRIFY = 0x00020000u,
    CBR_PUBLIC_SLOW_START = 0x00040000u,
    CBR_PUBLIC_SYRUP_BOMB = 0x00080000u,
    CBR_PUBLIC_DRAGON_CHEER = 0x00000001u,
    CBR_PUBLIC_PARADOX_BOOST = 0x00000002u,
    CBR_PUBLIC_POWDER = 0x00000010u,
    CBR_PUBLIC_TAR_SHOT = 0x00001000u,
    CBR_PUBLIC_OCTOLOCK = 0x00080000u,
    CBR_PUBLIC_NO_RETREAT = 0x00100000u,
    CBR_PUBLIC_SALT_CURE = 0x80000000u,
    CBR_PUBLIC_MESSAGE_LOADER_OFFSET = 76u,
    CBR_PUBLIC_MESSAGE_LOADER_SIZE = 150u,
    CBR_PUBLIC_TEXT_BUFFERS_OFFSET = 28u,
    CBR_PUBLIC_TEXT_BUFFER_SIZE = 16u,
    CBR_PUBLIC_ABILITIES_OFFSET = 20u,
    CBR_BATTLE_STRING_ID_ADDER = 12u,
    CBR_BATTLE_STRING_COUNT = 386u,
    CBR_TEXT_PLACEHOLDER = 0xFDu,
    CBR_TEXT_BUFF1 = 0x00u,
    CBR_TEXT_BUFF2 = 0x01u,
    CBR_TEXT_BUFF3 = 0x34u,
    CBR_TEXT_CURRENT_MOVE = 0x14u,
    CBR_TEXT_LAST_MOVE = 0x15u,
    CBR_TEXT_LAST_ITEM = 0x16u,
    CBR_TEXT_LAST_ABILITY = 0x17u,
    CBR_TEXT_ATTACKER_ABILITY = 0x18u,
    CBR_TEXT_TARGET_ABILITY = 0x19u,
    CBR_TEXT_SCRIPTING_ABILITY = 0x1Au,
    CBR_TEXT_EFFECT_ABILITY = 0x1Bu,
    CBR_BUFFER_ABILITY = 9u,
    CBR_BUFFER_ITEM = 10u,
    CBR_ITEM_KNOWLEDGE_UNKNOWN = 0u,
    CBR_ITEM_KNOWLEDGE_HELD = 1u,
    CBR_ITEM_KNOWLEDGE_GONE = 2u,
    CBR_ITEM_KNOWLEDGE_CHANGED = 3u,
    CBR_WISH_FUTURE_MOVE_OFFSET = 0x18u,
    CBR_WISH_COUNTER_OFFSET = 0x20u,
};

enum {
    G_PLAYER_PARTY_ADDRESS = 0x020241E4u,
    G_ENEMY_PARTY_ADDRESS = 0x02023F8Cu,
    G_PLAYER_COUNT_ADDRESS = 0x02023F89u,
    G_ENEMY_COUNT_ADDRESS = 0x02023F8Au,
    G_TRAINER_OPPONENT_A_ADDRESS = 0x020385E2u,
    G_TRAINER_TABLE_ADDRESS = 0x09329070u,
    CBR_TRAINER_RECORD_SIZE = 0x20u,
    CBR_TRAINER_PARTY_SIZE_OFFSET = 0x18u,
    G_SELECTED_ORDER_ADDRESS = 0x0203C6C8u,
    G_SPECIAL_RESULT_ADDRESS = 0x02037004u,
    G_BATTLE_OUTCOME_ADDRESS = 0x02023DEAu,
    G_BATTLE_TYPE_FLAGS_ADDRESS = 0x02022AACu,
    G_BATTLE_BUFFER_A_ADDRESS = 0x02022B24u,
    G_BATTLE_BUFFER_B_ADDRESS = 0x02023324u,
    G_BATTLE_CONTROLLER_EXEC_FLAGS_ADDRESS = 0x02023B28u,
    G_BATTLERS_COUNT_ADDRESS = 0x02023B2Cu,
    G_BATTLE_STRUCT_PTR_ADDRESS = 0x02023F48u,
    G_ACTIVE_BATTLER_ADDRESS = 0x02023B24u,
    G_BATTLE_MONS_ADDRESS = 0x02023B44u,
    G_BATTLER_PARTY_INDEXES_ADDRESS = 0x02023B2Eu,
    G_BANK_ATTACKER_ADDRESS = 0x02023CCBu,
    G_BANK_TARGET_ADDRESS = 0x02023CCCu,
    G_EFFECT_BANK_ADDRESS = 0x02023CCEu,
    G_SIDE_STATUSES_ADDRESS = 0x02023D3Eu,
    G_SIDE_TIMERS_ADDRESS = 0x02023D44u,
    G_STATUSES3_ADDRESS = 0x02023D5Cu,
    G_BATTLE_WEATHER_ADDRESS = 0x02023E7Cu,
    G_WISH_FUTURE_KNOCK_ADDRESS = 0x02023E80u,
    G_DISABLE_STRUCTS_ADDRESS = 0x02023E0Cu,
    G_TERRAIN_TYPE_ADDRESS = 0x0203DFA0u,
    G_ABILITY_POPUP_HELPER_ADDRESS = 0x0203DFA7u,
    G_NEW_BS_PTR_ADDRESS = 0x0203DFB0u,
    G_CONTROLLER_FUNCS_ADDRESS = 0x03005020u,
    G_GLOBAL_RNG_ADDRESS = 0x03005040u,
    G_SAVE_BLOCK1_PTR_ADDRESS = 0x03005048u,
    G_SAVE_BLOCK2_PTR_ADDRESS = 0x0300504Cu,
    G_BASE_MAILBOX_NONCE_ADDRESS = 0x0203F828u,
    G_BATTLE_STRINGS_TABLE_ADDRESS = 0x083C3F08u,
    G_MIRAGE_STATE_ADDRESS = 0x0203EE00u,
    G_MIRAGE_MAGIC = 0x4D505331u,
    G_MIRAGE_ACTIVE_OFFSET = 0x28u,
    CBR_BATTLE_STRUCT_SWITCHOUT_INDEX_OFFSET = 0x92u,
    CBR_BATTLE_STRUCT_GIVEN_EXP_OFFSET = 0xDFu,
    CBR_SAVE_BLOCK1_MONEY_OFFSET = 0x290u,
    CBR_SAVE_BLOCK1_DEX_SEEN_OFFSET = 0x310u,
    CBR_SAVE_BLOCK1_DEX_SEEN_SIZE = 150u,
    CBR_SAVE_BLOCK1_FLAGS_OFFSET = 0x0EE0u,
    CBR_SAVE_BLOCK1_FLAGS_VARS_SIZE = 0x320u,
    CBR_SAVE_BLOCK1_GAME_STATS_OFFSET = 0x1200u,
    CBR_SAVE_BLOCK2_POKEDEX_OFFSET = 0x18u,
    CBR_SAVE_BLOCK2_POKEDEX_SIZE = 16u,
    CBR_SAVE_BLOCK2_ENCRYPTION_KEY_OFFSET = 0x0F20u,
    CBR_GAME_STATS_COUNT = 64u,
};

#define G_PLAYER_PARTY PTR(Pokemon100 *, G_PLAYER_PARTY_ADDRESS)
#define G_ENEMY_PARTY PTR(Pokemon100 *, G_ENEMY_PARTY_ADDRESS)
#define G_PLAYER_COUNT PTR(volatile u8 *, G_PLAYER_COUNT_ADDRESS)
#define G_ENEMY_COUNT PTR(volatile u8 *, G_ENEMY_COUNT_ADDRESS)
#define G_TRAINER_OPPONENT_A \
    PTR(volatile u16 *, G_TRAINER_OPPONENT_A_ADDRESS)
#define G_TRAINER_TABLE PTR(const u8 *, G_TRAINER_TABLE_ADDRESS)
#define G_SELECTED PTR(volatile u8 *, G_SELECTED_ORDER_ADDRESS)
#define G_SPECIAL_RESULT PTR(volatile u16 *, G_SPECIAL_RESULT_ADDRESS)
#define G_BATTLE_OUTCOME PTR(volatile u8 *, G_BATTLE_OUTCOME_ADDRESS)
#define G_BATTLE_FLAGS PTR(volatile u32 *, G_BATTLE_TYPE_FLAGS_ADDRESS)
#define G_BATTLE_BUFFER_A PTR(volatile u8 *, G_BATTLE_BUFFER_A_ADDRESS)
#define G_BATTLE_BUFFER_B PTR(volatile u8 *, G_BATTLE_BUFFER_B_ADDRESS)
#define G_BATTLE_CONTROLLER_EXEC_FLAGS \
    PTR(volatile u32 *, G_BATTLE_CONTROLLER_EXEC_FLAGS_ADDRESS)
#define G_BATTLERS_COUNT PTR(volatile u8 *, G_BATTLERS_COUNT_ADDRESS)
#define G_BATTLE_STRUCT_PTR \
    PTR(volatile u8 * volatile *, G_BATTLE_STRUCT_PTR_ADDRESS)
#define G_ACTIVE_BATTLER PTR(volatile u8 *, G_ACTIVE_BATTLER_ADDRESS)
#define G_BATTLE_MONS PTR(volatile u8 *, G_BATTLE_MONS_ADDRESS)
/* CFRU keeps gBattlerPartyIndexes as u16[MAX_BATTLERS_COUNT].  Treating this
 * address as bytes makes bank 1 read bank 0's high byte (normally zero),
 * which aliases every opponent switch back onto selection slot 1. */
#define G_BATTLER_PARTY_INDEXES \
    PTR(volatile u16 *, G_BATTLER_PARTY_INDEXES_ADDRESS)
#define G_BANK_ATTACKER PTR(volatile u8 *, G_BANK_ATTACKER_ADDRESS)
#define G_BANK_TARGET PTR(volatile u8 *, G_BANK_TARGET_ADDRESS)
#define G_EFFECT_BANK PTR(volatile u8 *, G_EFFECT_BANK_ADDRESS)
#define G_SIDE_STATUSES PTR(volatile u16 *, G_SIDE_STATUSES_ADDRESS)
#define G_SIDE_TIMERS PTR(volatile u8 *, G_SIDE_TIMERS_ADDRESS)
#define G_STATUSES3 PTR(volatile u32 *, G_STATUSES3_ADDRESS)
#define G_DISABLE_STRUCTS PTR(volatile u8 *, G_DISABLE_STRUCTS_ADDRESS)
#define G_BATTLE_WEATHER PTR(volatile u16 *, G_BATTLE_WEATHER_ADDRESS)
#define G_WISH_FUTURE_KNOCK PTR(volatile u8 *, G_WISH_FUTURE_KNOCK_ADDRESS)
#define G_TERRAIN_TYPE PTR(volatile u8 *, G_TERRAIN_TYPE_ADDRESS)
#define G_ABILITY_POPUP_HELPER \
    PTR(volatile u8 *, G_ABILITY_POPUP_HELPER_ADDRESS)
#define G_NEW_BS_PTR PTR(volatile u8 * volatile *, G_NEW_BS_PTR_ADDRESS)
#define G_CONTROLLER_FUNCS PTR(volatile u32 *, G_CONTROLLER_FUNCS_ADDRESS)
#define G_GLOBAL_RNG PTR(volatile u32 *, G_GLOBAL_RNG_ADDRESS)
#define G_SAVE_BLOCK1_PTR PTR(volatile u8 * volatile *, G_SAVE_BLOCK1_PTR_ADDRESS)
#define G_SAVE_BLOCK2_PTR PTR(volatile u8 * volatile *, G_SAVE_BLOCK2_PTR_ADDRESS)
#define G_BASE_NONCE PTR(volatile u32 *, G_BASE_MAILBOX_NONCE_ADDRESS)
#define G_BASE_STATS PTR(const volatile u8 *, CODEX_RUNTIME_BASE_STATS_ADDRESS)
#define G_BATTLE_STRINGS_TABLE \
    PTR(const volatile u32 *, G_BATTLE_STRINGS_TABLE_ADDRESS)
#define G_EXPERIENCE_TABLES \
    PTR(const volatile u32 *, CODEX_RUNTIME_EXPERIENCE_TABLES)

#define FN_READ_KEYS_DELEGATE PTR(VoidFn, CODEX_RUNTIME_DELEGATE_READ_KEYS)
#define FN_TRAINER_PARTY_DELEGATE PTR(VoidFn, CODEX_RUNTIME_DELEGATE_TRAINER_PARTY)
#define FN_SAVE_LOAD_DELEGATE PTR(U8Fn, CODEX_RUNTIME_DELEGATE_SAVE_LOAD)
#define FN_FIND_DYNAMAX_BAND_DELEGATE \
    PTR(U16FromU8Fn, CODEX_RUNTIME_DELEGATE_FIND_DYNAMAX_BAND)
#define FN_GET_MON_DATA PTR(GetMonDataFn, CODEX_RUNTIME_ENGINE_GET_MON_DATA)
#define FN_SET_MON_DATA PTR(SetMonDataFn, CODEX_RUNTIME_ENGINE_SET_MON_DATA)
#define FN_CREATE_MON PTR(CreateMonFn, CODEX_RUNTIME_ENGINE_CREATE_MON)
#define FN_CALCULATE_STATS PTR(CalculateStatsFn, CODEX_RUNTIME_ENGINE_CALCULATE_STATS)
#define FN_CALCULATE_PP PTR(CalculatePpFn, CODEX_RUNTIME_ENGINE_CALCULATE_PP)
#define FN_GET_GENDER PTR(GetGenderFn, CODEX_RUNTIME_ENGINE_GET_GENDER)
#define FN_IS_SHINY PTR(IsShinyFn, CODEX_RUNTIME_ENGINE_IS_SHINY)
#define FN_PARTY_COUNT PTR(CalculatePartyCountFn, CODEX_RUNTIME_ENGINE_PARTY_COUNT)
#define FN_VAR_GET PTR(VarGetFn, CODEX_RUNTIME_ENGINE_VAR_GET)
#define FN_VAR_SET PTR(VarSetFn, CODEX_RUNTIME_ENGINE_VAR_SET)
#define FN_FLAG_GET PTR(FlagFn, CODEX_RUNTIME_ENGINE_FLAG_GET)
#define FN_FLAG_SET PTR(FlagFn, CODEX_RUNTIME_ENGINE_FLAG_SET)
#define FN_FLAG_CLEAR PTR(FlagFn, CODEX_RUNTIME_ENGINE_FLAG_CLEAR)
#define FN_PREPARE_BUFFER PTR(PrepareBufferFn, CODEX_RUNTIME_ENGINE_PREPARE_BUFFER)
#define FN_EMIT_TWO PTR(EmitTwoFn, CODEX_RUNTIME_ENGINE_EMIT_TWO)
#define FN_EMIT_MON PTR(EmitMonFn, CODEX_RUNTIME_ENGINE_EMIT_MON)
#define FN_OPPONENT_COMPLETE PTR(VoidFn, CODEX_RUNTIME_ENGINE_OPPONENT_COMPLETE)
#define G_BATTLE_MAIN_FUNC \
    PTR(volatile u32 *, CODEX_RUNTIME_ENGINE_BATTLE_MAIN_FUNC)
#define G_END_TURN_FUNCS \
    PTR(const volatile u32 *, CODEX_RUNTIME_ENGINE_END_TURN_FUNCS)
#define FN_CAN_MEGA PTR(CanMegaFn, CODEX_RUNTIME_ENGINE_CAN_MEGA)
#define FN_CAN_Z PTR(CanZFn, CODEX_RUNTIME_ENGINE_CAN_Z)
#define FN_CAN_DYNAMAX PTR(CanGimmickFn, CODEX_RUNTIME_ENGINE_CAN_DYNAMAX)
#define FN_CAN_TERA PTR(CanGimmickFn, CODEX_RUNTIME_ENGINE_CAN_TERA)
#define FN_POLICY_CAN_MEGA PTR(PolicyCanFn, CODEX_RUNTIME_DELEGATE_CAN_MEGA)
#define FN_POLICY_MARK_MEGA PTR(PolicyMarkFn, CODEX_RUNTIME_DELEGATE_MARK_MEGA)
#define FN_POLICY_CAN_Z PTR(PolicyCanFn, CODEX_RUNTIME_DELEGATE_CAN_Z)
#define FN_POLICY_MARK_Z PTR(PolicyMarkFn, CODEX_RUNTIME_DELEGATE_MARK_Z)
#define FN_POLICY_CAN_DYNAMAX PTR(PolicyCanFn, CODEX_RUNTIME_DELEGATE_CAN_DYNAMAX)
#define FN_POLICY_MARK_DYNAMAX PTR(PolicyMarkFn, CODEX_RUNTIME_DELEGATE_MARK_DYNAMAX)
#define FN_POLICY_CAN_TERA PTR(PolicyCanFn, CODEX_RUNTIME_DELEGATE_CAN_TERA)
#define FN_POLICY_MARK_TERA PTR(PolicyMarkFn, CODEX_RUNTIME_DELEGATE_MARK_TERA)

typedef struct ChooseMoveStruct120 {
    u16 moves[4];
    u8 current_pp[4];
    u8 max_pp[4];
    u16 species;
    u8 type1;
    u8 type2;
    u8 move_types[4];
    u8 move_results[4][4];
    u8 z_results[4][4];
    u16 move_powers[4];
    u16 move_accuracy[4];
    u8 split[4];
    u8 contact[4];
    u8 type3;
    u8 tera_type;
    u8 can_mega;
    u8 mega_variance;
    u8 used_flags;
    u8 bank;
    u8 z_party_index;
    u8 alignment0;
    u16 possible_z[4];
    u16 ability;
    u8 can_dynamax;
    u8 alignment1;
    u16 possible_max[4];
    u16 max_power[4];
    u8 dynamax_party_index;
    u8 tera_party_index;
    u8 can_tera;
    u8 alignment2;
} ChooseMoveStruct120;

_Static_assert(sizeof(ChooseMoveStruct120) == 120u,
               "expanded choose-move ABI differs");

static u32 mix32(u32 value);
static u32 member_seed(u8 slot);

static void barrier(void) { __asm__ volatile("" ::: "memory"); }

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

static u32 crc32_volatile(const volatile u8 *bytes, u32 size)
{
    u32 crc = 0xFFFFFFFFu;
    u32 index;
    for (index = 0u; index < size; ++index)
        crc = crc_byte(crc, bytes[index]);
    return crc ^ 0xFFFFFFFFu;
}

static u32 fnv32(const volatile void *data, u32 size)
{
    const volatile u8 *bytes = (const volatile u8 *)data;
    u32 value = 2166136261u;
    u32 index;
    for (index = 0u; index < size; ++index) {
        value ^= bytes[index];
        value *= 16777619u;
    }
    return value;
}

static u32 fnv32_continue(u32 value, const volatile void *data, u32 size)
{
    const volatile u8 *bytes = (const volatile u8 *)data;
    u32 index;
    for (index = 0u; index < size; ++index) {
        value ^= bytes[index];
        value *= 16777619u;
    }
    return value;
}

static u32 current_save_hash(void)
{
    const volatile u8 *save1 = *G_SAVE_BLOCK1_PTR;
    const volatile u8 *save2 = *G_SAVE_BLOCK2_PTR;
    u32 value = 2166136261u;
    u32 key;
    u32 logical;
    u8 index;
    if (save1 == NULL || save2 == NULL)
        return 0u;
    key = read32(save2 + CBR_SAVE_BLOCK2_ENCRYPTION_KEY_OFFSET);
    /* SaveBlocks are relocated and re-encrypted during normal field/battle
     * transitions.  Hash only persistent logical state owned by this match,
     * decrypting key-protected words and excluding play time. */
    logical = read32(save1 + CBR_SAVE_BLOCK1_MONEY_OFFSET) ^ key;
    value = fnv32_continue(value, &logical, sizeof(logical));
    value = fnv32_continue(
        value, save1 + CBR_SAVE_BLOCK1_DEX_SEEN_OFFSET,
        CBR_SAVE_BLOCK1_DEX_SEEN_SIZE);
    value = fnv32_continue(
        value, save1 + CBR_SAVE_BLOCK1_FLAGS_OFFSET,
        CBR_SAVE_BLOCK1_FLAGS_VARS_SIZE);
    for (index = 0u; index < CBR_GAME_STATS_COUNT; ++index) {
        logical = read32(save1 + CBR_SAVE_BLOCK1_GAME_STATS_OFFSET
                         + (u32)index * 4u) ^ key;
        value = fnv32_continue(value, &logical, sizeof(logical));
    }
    return fnv32_continue(
        value, save2 + CBR_SAVE_BLOCK2_POKEDEX_OFFSET,
        CBR_SAVE_BLOCK2_POKEDEX_SIZE);
}

static u32 trainer_id(void)
{
    const volatile u8 *save2 = *G_SAVE_BLOCK2_PTR;
    return save2 == NULL ? 0u : read32(save2 + 0x0Au);
}

static u8 personality_is_shiny(u32 personality, u32 owner)
{
    u16 value = (u16)owner ^ (u16)(owner >> 16)
        ^ (u16)personality ^ (u16)(personality >> 16);
    return (u8)(value < 8u);
}

static u32 member_personality(u8 slot, u8 shiny)
{
    u32 seed = member_seed(slot);
    u32 owner = trainer_id();
    if (shiny) {
        u16 high = (u16)(seed >> 16);
        u16 low = (u16)owner ^ (u16)(owner >> 16) ^ high;
        return ((u32)high << 16) | low;
    }
    while (personality_is_shiny(seed, owner))
        seed = mix32(seed + 0x9E3779B9u);
    return seed;
}

static u32 next_sequence(u32 value)
{
    ++value;
    return value == 0u ? 1u : value;
}

static u32 mix32(u32 value)
{
    value ^= value << 13;
    value ^= value >> 17;
    value ^= value << 5;
    return value != 0u ? value : 0x43425232u;
}

static u8 state_valid(void)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    return (u8)(state != NULL && state->magic == CBR_STATE_MAGIC
        && state->magic_inverse == ~CBR_STATE_MAGIC);
}

static u8 runtime_active(void)
{
    return (u8)(state_valid() && gCodexBattleRuntimeState->active != 0u);
}

static u8 mirage_active(void)
{
    const volatile u8 *state = PTR(const volatile u8 *, G_MIRAGE_STATE_ADDRESS);
    return (u8)(read32(state) == G_MIRAGE_MAGIC
        && state[G_MIRAGE_ACTIVE_OFFSET] != 0u);
}

static u8 type_valid(u8 type)
{
    return (u8)(type <= 17u || type == 23u || type == 24u);
}

static u8 held_item_safe(u16 item)
{
    if (item > CODEX_RUNTIME_ITEM_MAX)
        return 0u;
    return (u8)((gCodexRuntimeHeldItemSafe[item >> 3]
                 >> (item & 7u)) & 1u);
}

static void set_result(u16 value)
{
    *G_SPECIAL_RESULT = value;
}

static void initialize_state(u32 nonce)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    clear_bytes(state, CODEX_RUNTIME_STATE_SIZE);
    state->magic = CBR_STATE_MAGIC;
    state->magic_inverse = ~CBR_STATE_MAGIC;
    state->session_nonce = nonce;
    state->phase = CODEX_RUNTIME_PHASE_IDLE;
    state->status = CBR_STATUS_READY;
}

static void capture_player_preview(void)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    u8 count = FN_PARTY_COUNT();
    u8 index;
    if (count > CBR_TEAM_SIZE)
        count = CBR_TEAM_SIZE;
    for (index = 0u; index < CBR_TEAM_SIZE; ++index) {
        state->player_preview_species[index] = index < count
            ? (u16)FN_GET_MON_DATA(&G_PLAYER_PARTY[index],
                                   CBR_MON_DATA_SPECIES, NULL)
            : 0u;
    }
}

static u8 player_preview_matches_current_party(void)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    u8 count = FN_PARTY_COUNT();
    u8 index;
    if (count > CBR_TEAM_SIZE)
        count = CBR_TEAM_SIZE;
    for (index = 0u; index < CBR_TEAM_SIZE; ++index) {
        u16 species = index < count
            ? (u16)FN_GET_MON_DATA(&G_PLAYER_PARTY[index],
                                   CBR_MON_DATA_SPECIES, NULL)
            : 0u;
        if (species != state->player_preview_species[index])
            return 0u;
    }
    return 1u;
}

static u8 valid_ewram_range(const volatile u8 *pointer, u32 size)
{
    u32 address = (u32)(uintptr_t)pointer;
    return (u8)(address >= 0x02000000u
        && size <= 0x40000u
        && address <= 0x02040000u - size);
}

static volatile u8 *battle_mon(u8 bank)
{
    return G_BATTLE_MONS + (u32)bank * CBR_BATTLE_MON_SIZE;
}

static u8 major_status(u32 raw, volatile u8 *detail)
{
    *detail = 0u;
    if ((raw & 0x7u) != 0u) {
        /* The cart stores the randomly selected remaining sleep turns here.
         * An online opponent only sees SLEEP, not that private countdown. */
        return 1u; /* sleep */
    }
    if (raw & 0x80u) {
        *detail = (u8)((raw >> 8) & 0xFu);
        return 3u; /* toxic */
    }
    if (raw & 0x8u)
        return 2u; /* poison */
    if (raw & 0x10u)
        return 4u; /* burn */
    if (raw & 0x20u)
        return 5u; /* freeze */
    if (raw & 0x40u)
        return 6u; /* paralysis */
    return 0u;
}

static u32 public_status2(u32 raw)
{
    u32 result = raw & ~(0x00000007u | 0x00000070u | 0x00000300u
        | 0x00000C00u | 0x0000E000u | 0x000F0000u);
    /* Multi-bit fields contain hidden/random counters or a battler index.
     * Preserve only the screen-public fact that the volatile is active. */
    if (raw & 0x00000007u)
        result |= 0x00000001u; /* confusion */
    if (raw & 0x00000070u)
        result |= 0x00000010u; /* uproar */
    if (raw & 0x00000300u)
        result |= 0x00000100u; /* bide */
    if (raw & 0x00000C00u)
        result |= 0x00000400u; /* locked move / later confusion */
    if (raw & 0x0000E000u)
        result |= 0x00002000u; /* wrapped */
    if (raw & 0x000F0000u)
        result |= 0x00010000u; /* infatuated; source is implicit in singles */
    return result;
}

static u32 public_status3(u32 raw)
{
    u32 result = raw & ~(0x00000003u | 0x00000018u | 0x00001800u);
    if (raw & 0x00000018u)
        result |= 0x00000008u; /* lock-on */
    if (raw & 0x00001800u)
        result |= 0x00000800u; /* yawn */
    return result;
}

static void pack_nibbles(volatile u8 *destination,
                         const volatile u8 *source, u8 count)
{
    u8 index;
    for (index = 0u; index < (u8)((count + 1u) / 2u); ++index) {
        u8 first = source[(u8)(index * 2u)];
        u8 second = (u8)(index * 2u + 1u) < count
            ? source[(u8)(index * 2u + 1u)] : 0u;
        destination[index] = (u8)((first & 0xFu) | ((second & 0xFu) << 4));
    }
}

static void pack_bits(volatile u8 *destination, u16 bit_offset,
                      u32 value, u8 width)
{
    u8 bit;
    for (bit = 0u; bit < width; ++bit) {
        if (value & (1u << bit)) {
            u16 output_bit = (u16)(bit_offset + bit);
            destination[output_bit >> 3] |= (u8)(1u << (output_bit & 7u));
        }
    }
}

static u8 clamp_public_value(u8 value, u8 maximum)
{
    return value > maximum ? maximum : value;
}

static void pack_personal_effects(
    volatile u8 *destination, u8 bank, const volatile u8 *disable,
    const volatile u8 *newbs)
{
    u16 bit = (u16)bank * 64u;
    u8 dmax_timer;
#define CBR_PACK_PERSONAL(value, width, maximum) do { \
    pack_bits(destination, bit, clamp_public_value((u8)(value), (maximum)), \
              (width)); \
    bit = (u16)(bit + (width)); \
} while (0)
    CBR_PACK_PERSONAL(disable[CBR_DISABLE_TIMER_OFFSET] & 0xFu, 4u, 15u);
    CBR_PACK_PERSONAL(disable[CBR_ENCORE_TIMER_OFFSET] & 0xFu, 4u, 15u);
    CBR_PACK_PERSONAL(disable[CBR_PERISH_TIMER_OFFSET] & 0xFu, 2u, 3u);
    CBR_PACK_PERSONAL(disable[CBR_TAUNT_TIMER_OFFSET] & 0xFu, 4u, 15u);
    CBR_PACK_PERSONAL(newbs[CBR_NEWBS_TELEKINESIS_OFFSET + bank], 3u, 7u);
    CBR_PACK_PERSONAL(newbs[CBR_NEWBS_MAGNET_RISE_OFFSET + bank], 3u, 7u);
    CBR_PACK_PERSONAL(newbs[CBR_NEWBS_HEAL_BLOCK_OFFSET + bank], 3u, 7u);
    CBR_PACK_PERSONAL(newbs[CBR_NEWBS_LASER_FOCUS_OFFSET + bank], 2u, 3u);
    CBR_PACK_PERSONAL(newbs[CBR_NEWBS_THROAT_CHOP_OFFSET + bank], 2u, 3u);
    CBR_PACK_PERSONAL(newbs[CBR_NEWBS_EMBARGO_OFFSET + bank], 3u, 7u);
    CBR_PACK_PERSONAL(newbs[CBR_NEWBS_SLOW_START_OFFSET + bank], 3u, 7u);
    CBR_PACK_PERSONAL(newbs[CBR_NEWBS_GLAIVE_RUSH_OFFSET + bank], 1u, 1u);
    CBR_PACK_PERSONAL(newbs[CBR_NEWBS_SYRUP_BOMB_OFFSET + bank], 2u, 3u);
    CBR_PACK_PERSONAL(newbs[CBR_NEWBS_DRAGON_CHEER_OFFSET + bank], 2u, 3u);
    CBR_PACK_PERSONAL(newbs[CBR_NEWBS_CUD_CHEW_OFFSET + bank], 2u, 3u);
    CBR_PACK_PERSONAL(disable[CBR_STOCKPILE_OFFSET], 2u, 3u);
    CBR_PACK_PERSONAL(disable[CBR_ROLLOUT_TIMER_OFFSET] & 0xFu, 3u, 7u);
    CBR_PACK_PERSONAL(disable[CBR_CHARGE_TIMER_OFFSET] & 0xFu, 2u, 3u);
    CBR_PACK_PERSONAL(disable[CBR_PROTECT_USES_OFFSET], 3u, 7u);
    CBR_PACK_PERSONAL(disable[CBR_FURY_CUTTER_OFFSET], 3u, 7u);
    dmax_timer = (s8)newbs[CBR_NEWBS_DMAX_TIMER_OFFSET + bank] < 0
        ? 7u : clamp_public_value(
            newbs[CBR_NEWBS_DMAX_TIMER_OFFSET + bank], 6u);
    CBR_PACK_PERSONAL(dmax_timer, 3u, 7u);
    CBR_PACK_PERSONAL(newbs[CBR_NEWBS_PARADOX_STAT_OFFSET + bank], 3u, 7u);
    CBR_PACK_PERSONAL(
        (newbs[CBR_NEWBS_ROOST_BITS_OFFSET] >> bank) & 1u, 1u, 1u);
    /* Four bits per side are intentionally reserved for another public
     * persistent effect without changing the fixed 180-byte ABI. */
#undef CBR_PACK_PERSONAL
}

static u8 party_gender_code(const Pokemon100 *mon)
{
    u16 species = (u16)FN_GET_MON_DATA(mon, CBR_MON_DATA_SPECIES, NULL);
    u32 personality;
    u8 gender;
    if (species == 0u)
        return 3u;
    personality = FN_GET_MON_DATA(mon, CBR_MON_DATA_PERSONALITY, NULL);
    gender = FN_GET_GENDER(species, personality);
    if (gender == 0u)
        return 0u; /* male */
    if (gender == 0xFEu)
        return 1u; /* female */
    if (gender == 0xFFu)
        return 2u; /* genderless */
    return 3u;
}

static u8 party_is_shiny(const Pokemon100 *mon)
{
    u32 personality = FN_GET_MON_DATA(
        mon, CBR_MON_DATA_PERSONALITY, NULL);
    u32 ot_id = FN_GET_MON_DATA(mon, CBR_MON_DATA_OT_ID, NULL);
    return (u8)(FN_IS_SHINY(ot_id, personality) != 0u);
}

/* Assign an opaque identity in first-appearance order.  This preserves
 * screen-revealed knowledge across switches (including duplicate species)
 * without exposing the player's private selection order or original slot.
 * revealed_player_mask packs three 2-bit slot mappings and a 2-bit count. */
static u8 public_player_identity(void)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    u8 slot = (u8)G_BATTLER_PARTY_INDEXES[0];
    u8 packed = state->revealed_player_mask;
    u8 identity;
    u8 count;
    u8 shift;
    if (slot >= CBR_SELECTION_SIZE)
        return 0u;
    shift = (u8)(slot * 2u);
    identity = (u8)((packed >> shift) & 3u);
    if (identity != 0u)
        return identity;
    count = (u8)((packed >> 6u) & 3u);
    if (count >= CBR_SELECTION_SIZE)
        return 0u;
    identity = (u8)(count + 1u);
    packed = (u8)((packed & ~(3u << shift)) | (identity << shift));
    packed = (u8)((packed & 0x3Fu) | (identity << 6u));
    state->revealed_player_mask = packed;
    return identity;
}

static void fill_snapshot_preview_details(
    volatile CodexBattleRuntimeSnapshotV2 *snapshot)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    volatile u8 *levels = (volatile u8 *)snapshot->own_current_hp;
    const Pokemon100 *party = G_PLAYER_PARTY;
    u32 appearance = 0u;
    u8 index;
    if (!state->configured
        || state->phase > CODEX_RUNTIME_PHASE_AWAITING_CODEX_SELECTION)
        return;
    if (runtime_active() && state->player_count_before != 0u)
        party = (const Pokemon100 *)(const void *)state->player_party_backup;
    for (index = 0u; index < CBR_TEAM_SIZE; ++index) {
        const Pokemon100 *mon = &party[index];
        if (state->player_preview_species[index] == 0u)
            continue;
        levels[index] = state->level_mode == 0u ? 50u
            : (u8)FN_GET_MON_DATA(mon, CBR_MON_DATA_LEVEL, NULL);
        appearance |= (u32)party_gender_code(mon) << ((u32)index * 2u);
        appearance |= (u32)party_is_shiny(mon) << (12u + index);
    }
    write32((volatile u8 *)snapshot->own_max_hp, appearance);
}

static void fill_snapshot_battle_state(
    volatile CodexBattleRuntimeSnapshotV2 *snapshot)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    volatile u8 *own = battle_mon(1u);
    volatile u8 *player = battle_mon(0u);
    volatile u8 *newbs = *G_NEW_BS_PTR;
    u8 active = 3u;
    u8 index;
    u16 hp;
    u16 max_hp;
    u16 appearance = 0u;
    snapshot->battle_flags = 3u;
    snapshot->public_player_species = 0u;
    snapshot->public_player_hp_percent = 0u;
    for (index = 0u; index < CBR_SELECTION_SIZE; ++index) {
        snapshot->own_current_hp[index] = 0u;
        snapshot->own_max_hp[index] = 0u;
    }
    for (index = 0u; index < 4u; ++index) {
        snapshot->own_live_moves[index] = 0u;
        snapshot->own_live_pp[index] = 0u;
    }
    fill_snapshot_preview_details(snapshot);
    if (!runtime_active() || !state->player_selection_valid
        || !state->controller_installed) {
        if (state->public_flags & 1u)
            snapshot->battle_flags |= 0x40u;
        return;
    }
    active = G_BATTLER_PARTY_INDEXES[1];
    if (active >= CBR_SELECTION_SIZE)
        active = 3u;
    snapshot->battle_flags = active;
    snapshot->battle_flags |= 0x80u;
    for (index = 0u; index < CBR_SELECTION_SIZE; ++index) {
        hp = (u16)FN_GET_MON_DATA(&G_ENEMY_PARTY[index],
                                  CBR_MON_DATA_HP, NULL);
        max_hp = (u16)FN_GET_MON_DATA(&G_ENEMY_PARTY[index],
                                      CBR_MON_DATA_MAX_HP, NULL);
        snapshot->own_current_hp[index] = hp;
        snapshot->own_max_hp[index] = max_hp;
    }
    if (active < CBR_SELECTION_SIZE) {
        hp = read16(own + CBR_BATTLE_MON_HP_OFFSET);
        max_hp = read16(own + CBR_BATTLE_MON_MAX_HP_OFFSET);
        snapshot->own_current_hp[active] = hp;
        snapshot->own_max_hp[active] = max_hp;
        if (hp == 0u)
            snapshot->battle_flags |= 0x08u;
    }
    /* During a live battle the owner already has the six-member preview in
     * match.json.  Reuse that 12-byte static field for exact BattlePokemon
     * combat stats plus screen-public appearance, without growing SnapshotV2. */
    for (index = 0u; index < 5u; ++index) {
        snapshot->codex_preview_species[index] = read16(
            own + CBR_BATTLE_MON_ATTACK_OFFSET + (u32)index * 2u);
    }
    for (index = 0u; index < CBR_SELECTION_SIZE; ++index) {
        appearance |= (u16)party_gender_code(&G_ENEMY_PARTY[index])
            << ((u16)index * 2u);
        appearance |= (u16)party_is_shiny(&G_ENEMY_PARTY[index])
            << (6u + index);
    }
    if (G_BATTLER_PARTY_INDEXES[0] < CBR_SELECTION_SIZE
        && (G_STATUSES3[0] & CBR_STATUS3_ILLUSION) == 0u) {
        u8 player_slot = (u8)G_BATTLER_PARTY_INDEXES[0];
        appearance |= (u16)party_gender_code(&G_PLAYER_PARTY[player_slot])
            << 9u;
        appearance |= (u16)party_is_shiny(&G_PLAYER_PARTY[player_slot])
            << 11u;
    } else {
        appearance |= (u16)(3u << 9u);
        appearance |= 1u << 12u;
    }
    appearance |= (u16)public_player_identity() << 13u;
    snapshot->codex_preview_species[5] = appearance;
    for (index = 0u; index < 4u; ++index) {
        snapshot->own_live_moves[index] = read16(
            own + CBR_BATTLE_MON_MOVES_OFFSET + (u32)index * 2u);
        snapshot->own_live_pp[index] = own[CBR_BATTLE_MON_PP_OFFSET + index];
    }
    snapshot->public_player_species = read16(player);
    /* Illusion is public as the disguise, not as the underlying party slot. */
    if ((G_STATUSES3[0] & 0x80000000u) != 0u
        && valid_ewram_range(newbs, CBR_NEWBS_DISGUISED_AS_OFFSET + 1u)) {
        u8 disguise = newbs[CBR_NEWBS_DISGUISED_AS_OFFSET];
        if (disguise >= 1u && disguise <= CBR_SELECTION_SIZE)
            snapshot->public_player_species = (u16)FN_GET_MON_DATA(
                &G_PLAYER_PARTY[disguise - 1u], CBR_MON_DATA_SPECIES, NULL);
    }
    hp = read16(player + CBR_BATTLE_MON_HP_OFFSET);
    max_hp = read16(player + CBR_BATTLE_MON_MAX_HP_OFFSET);
    if (hp == 0u) {
        snapshot->battle_flags |= 0x04u;
    } else if (max_hp != 0u) {
        u32 percent = ((u32)hp * 100u + max_hp - 1u) / max_hp;
        snapshot->public_player_hp_percent = (u8)(percent > 100u
            ? 100u : percent);
    }
    if (state->switch_context == CBR_SWITCH_FORCED)
        snapshot->battle_flags |= 0x10u;
    else if (state->switch_context == CBR_SWITCH_VOLUNTARY)
        snapshot->battle_flags |= 0x20u;
}

static u32 public_state_crc(void)
{
    volatile CodexBattlePublicStateV2 *public_state =
        &gCodexBattleRuntimeState->public_state;
    const volatile u8 *bytes = (const volatile u8 *)public_state;
    u32 crc = 0xFFFFFFFFu;
    u32 index;
    for (index = 4u; index < 8u; ++index)
        crc = crc_byte(crc, bytes[index]);
    for (index = 16u; index < sizeof(*public_state); ++index)
        crc = crc_byte(crc, bytes[index]);
    return crc ^ 0xFFFFFFFFu;
}

static void fill_public_current_state(void)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    volatile CodexBattlePublicStateV2 *public_state = &state->public_state;
    volatile u8 *own = battle_mon(1u);
    volatile u8 *player = battle_mon(0u);
    volatile u8 *newbs = *G_NEW_BS_PTR;
    volatile u8 *player_disable = G_DISABLE_STRUCTS;
    volatile u8 *own_disable = G_DISABLE_STRUCTS + CBR_DISABLE_STRUCT_SIZE;
    u8 timers[22];
    u8 classic[8];
    u8 stages[14];
    u8 types[6];
    u8 own_party_statuses[3];
    u32 packed_types = 0u;
    u32 own_status2;
    u32 player_status2;
    u32 own_status3;
    u32 player_status3;
    u8 active_player;
    u8 active_own;
    u8 status_detail;
    u8 newbs_valid;
    u8 index;
    public_state->own_active_species = 0u;
    public_state->own_status = 0u;
    public_state->own_status_detail = 0u;
    public_state->player_status = 0u;
    public_state->player_status_detail = 0u;
    clear_bytes(public_state->stat_stages_packed,
                sizeof(public_state->stat_stages_packed));
    clear_bytes(public_state->status2, sizeof(public_state->status2));
    clear_bytes(public_state->status3, sizeof(public_state->status3));
    public_state->own_item_id = 0u;
    public_state->own_ability_id = 0u;
    clear_bytes(public_state->types_packed, sizeof(public_state->types_packed));
    write16((volatile u8 *)public_state
                + offsetof(CodexBattlePublicStateV2, weather), 0u);
    public_state->weather_duration = 0u;
    public_state->terrain = 0u;
    public_state->terrain_timer = 0u;
    clear_bytes(public_state->field_timers,
                sizeof(public_state->field_timers));
    clear_bytes(public_state->side_statuses,
                sizeof(public_state->side_statuses));
    clear_bytes(public_state->classic_side_timers_packed,
                sizeof(public_state->classic_side_timers_packed));
    clear_bytes(public_state->entry_hazards,
                sizeof(public_state->entry_hazards));
    clear_bytes(public_state->modern_side_timers_packed,
                sizeof(public_state->modern_side_timers_packed));
    public_state->mechanic_used_mask = state->mechanic_used_mask;
    public_state->native_gimmick_flags = 0u;
    public_state->player_level = 0u;
    clear_bytes(public_state->move_locks_packed,
                sizeof(public_state->move_locks_packed));
    clear_bytes(public_state->personal_effects_packed,
                sizeof(public_state->personal_effects_packed));
    clear_bytes(public_state->own_party_status_packed,
                sizeof(public_state->own_party_status_packed));
    clear_bytes(public_state->wish_future_packed,
                sizeof(public_state->wish_future_packed));
    public_state->player_item_knowledge = CBR_ITEM_KNOWLEDGE_UNKNOWN;
    public_state->own_level = 0u;
    if (!runtime_active() || !state->player_selection_valid
        || !state->controller_installed)
        return;

    active_player = G_BATTLER_PARTY_INDEXES[0];
    if (active_player >= CBR_SELECTION_SIZE)
        active_player = 3u;
    if ((state->public_flags & 0x08u) == 0u
        || ((state->public_flags >> 1) & 3u) != active_player) {
        /* Revealed moves, item and ability belong to the active public
         * identity.  Never carry them to a newly switched-in Pokemon. */
        public_state->player_revealed_item_id = 0u;
        public_state->player_revealed_ability_id = 0u;
        clear_bytes(public_state->player_revealed_moves,
                    sizeof(public_state->player_revealed_moves));
        state->public_flags = (u8)((state->public_flags & 0xF1u) | 0x08u
            | ((active_player & 3u) << 1));
    }
    public_state->own_active_species = read16(own);
    public_state->own_level = own[CBR_BATTLE_MON_LEVEL_OFFSET];
    public_state->player_level = player[CBR_BATTLE_MON_LEVEL_OFFSET];
    if (public_state->player_revealed_item_id != 0u) {
        u16 current_item = read16(player + CBR_BATTLE_MON_ITEM_OFFSET);
        if (current_item == public_state->player_revealed_item_id)
            public_state->player_item_knowledge = CBR_ITEM_KNOWLEDGE_HELD;
        else if (current_item == 0u)
            public_state->player_item_knowledge = CBR_ITEM_KNOWLEDGE_GONE;
        else
            public_state->player_item_knowledge = CBR_ITEM_KNOWLEDGE_CHANGED;
    }
    public_state->own_status = major_status(
        read32(own + CBR_BATTLE_MON_STATUS1_OFFSET),
        &public_state->own_status_detail);
    public_state->player_status = major_status(
        read32(player + CBR_BATTLE_MON_STATUS1_OFFSET),
        &public_state->player_status_detail);
    for (index = 0u; index < 7u; ++index) {
        u8 own_stage = own[CBR_BATTLE_MON_STAT_STAGES_OFFSET + index];
        u8 player_stage = player[CBR_BATTLE_MON_STAT_STAGES_OFFSET + index];
        stages[index] = own_stage <= 12u ? own_stage : 6u;
        stages[7u + index] = player_stage <= 12u ? player_stage : 6u;
    }
    pack_nibbles(public_state->stat_stages_packed, stages, 14u);
    own_status2 = public_status2(
        read32(own + CBR_BATTLE_MON_STATUS2_OFFSET));
    player_status2 = public_status2(
        read32(player + CBR_BATTLE_MON_STATUS2_OFFSET));
    own_status3 = public_status3(
        G_STATUSES3[1] & ~CBR_STATUS3_SWITCH_IN_ABILITY_DONE);
    player_status3 = G_STATUSES3[0];
    public_state->status3[1] = public_status3(player_status3
        & ~(CBR_STATUS3_SWITCH_IN_ABILITY_DONE | CBR_STATUS3_ILLUSION));
    public_state->own_item_id = read16(own + CBR_BATTLE_MON_ITEM_OFFSET);
    public_state->own_ability_id = read16(own + CBR_BATTLE_MON_ABILITY_OFFSET);
    types[0] = own[CBR_BATTLE_MON_TYPE1_OFFSET];
    types[1] = own[CBR_BATTLE_MON_TYPE2_OFFSET];
    types[2] = own[CBR_BATTLE_MON_TYPE3_OFFSET];
    if ((player_status3 & CBR_STATUS3_ILLUSION) == 0u) {
        types[3] = player[CBR_BATTLE_MON_TYPE1_OFFSET];
        types[4] = player[CBR_BATTLE_MON_TYPE2_OFFSET];
        types[5] = player[CBR_BATTLE_MON_TYPE3_OFFSET];
    } else {
        types[3] = 31u;
        types[4] = 31u;
        types[5] = 31u;
    }
    for (index = 0u; index < 6u; ++index) {
        u8 type = types[index] <= 30u ? types[index] : 31u;
        packed_types |= (u32)type << ((u32)index * 5u);
    }
    write32(public_state->types_packed, packed_types);
    newbs_valid = valid_ewram_range(
        newbs, CBR_NEWBS_AI_ABILITIES_OFFSET + 8u);
    if (newbs_valid) {
        for (index = 0u; index < 8u; ++index)
            public_state->field_timers[index] = newbs[index];
        public_state->terrain_timer = newbs[8u];
        for (index = 0u; index < 22u; ++index)
            timers[index] = newbs[9u + index];
        pack_nibbles(public_state->modern_side_timers_packed, timers, 22u);
        if (newbs[CBR_NEWBS_Z_USED_OFFSET + 1u])
            public_state->native_gimmick_flags |= 0x01u;
        if (newbs[CBR_NEWBS_Z_USED_OFFSET])
            public_state->native_gimmick_flags |= 0x02u;
        if ((s8)newbs[CBR_NEWBS_DMAX_TIMER_OFFSET + 1u] != 0)
            public_state->native_gimmick_flags |= 0x04u;
        if ((s8)newbs[CBR_NEWBS_DMAX_TIMER_OFFSET] != 0)
            public_state->native_gimmick_flags |= 0x08u;
        if (newbs[CBR_NEWBS_TERA_DONE_OFFSET + 1u])
            public_state->native_gimmick_flags |= 0x10u;
        if (newbs[CBR_NEWBS_TERA_DONE_OFFSET])
            public_state->native_gimmick_flags |= 0x20u;
        if (newbs[CBR_NEWBS_DMAX_USED_OFFSET + 1u])
            public_state->native_gimmick_flags |= 0x40u;
        if (newbs[CBR_NEWBS_DMAX_USED_OFFSET])
            public_state->native_gimmick_flags |= 0x80u;
    }

    if ((player_disable[CBR_DISABLE_TIMER_OFFSET] & 0xFu) != 0u) {
        player_status2 |= CBR_PUBLIC_DISABLED;
        pack_bits(public_state->move_locks_packed, 0u,
                  read16(player_disable + CBR_DISABLE_MOVE_OFFSET), 12u);
    }
    if ((own_disable[CBR_DISABLE_TIMER_OFFSET] & 0xFu) != 0u) {
        own_status2 |= CBR_PUBLIC_DISABLED;
        pack_bits(public_state->move_locks_packed, 12u,
                  read16(own_disable + CBR_DISABLE_MOVE_OFFSET), 12u);
    }
    if ((player_disable[CBR_ENCORE_TIMER_OFFSET] & 0xFu) != 0u) {
        player_status2 |= CBR_PUBLIC_ENCORED;
        pack_bits(public_state->move_locks_packed, 24u,
                  read16(player_disable + CBR_ENCORE_MOVE_OFFSET), 12u);
    }
    if ((own_disable[CBR_ENCORE_TIMER_OFFSET] & 0xFu) != 0u) {
        own_status2 |= CBR_PUBLIC_ENCORED;
        pack_bits(public_state->move_locks_packed, 36u,
                  read16(own_disable + CBR_ENCORE_MOVE_OFFSET), 12u);
    }
    if (player_disable[CBR_TAUNT_TIMER_OFFSET] & 0xFu)
        player_status2 |= CBR_PUBLIC_TAUNT;
    if (own_disable[CBR_TAUNT_TIMER_OFFSET] & 0xFu)
        own_status2 |= CBR_PUBLIC_TAUNT;

    if (newbs_valid) {
#define CBR_SET_PERSONAL_FLAG(word, condition, flag) do { \
    if (condition) \
        (word) |= (flag); \
} while (0)
        CBR_SET_PERSONAL_FLAG(player_status2,
            newbs[CBR_NEWBS_MAGNET_RISE_OFFSET], CBR_PUBLIC_MAGNET_RISE);
        CBR_SET_PERSONAL_FLAG(own_status2,
            newbs[CBR_NEWBS_MAGNET_RISE_OFFSET + 1u], CBR_PUBLIC_MAGNET_RISE);
        CBR_SET_PERSONAL_FLAG(player_status2,
            newbs[CBR_NEWBS_HEAL_BLOCK_OFFSET], CBR_PUBLIC_HEAL_BLOCK);
        CBR_SET_PERSONAL_FLAG(own_status2,
            newbs[CBR_NEWBS_HEAL_BLOCK_OFFSET + 1u], CBR_PUBLIC_HEAL_BLOCK);
        CBR_SET_PERSONAL_FLAG(player_status2,
            newbs[CBR_NEWBS_LASER_FOCUS_OFFSET], CBR_PUBLIC_LASER_FOCUS);
        CBR_SET_PERSONAL_FLAG(own_status2,
            newbs[CBR_NEWBS_LASER_FOCUS_OFFSET + 1u], CBR_PUBLIC_LASER_FOCUS);
        CBR_SET_PERSONAL_FLAG(player_status2,
            newbs[CBR_NEWBS_THROAT_CHOP_OFFSET], CBR_PUBLIC_THROAT_CHOP);
        CBR_SET_PERSONAL_FLAG(own_status2,
            newbs[CBR_NEWBS_THROAT_CHOP_OFFSET + 1u], CBR_PUBLIC_THROAT_CHOP);
        CBR_SET_PERSONAL_FLAG(player_status2,
            newbs[CBR_NEWBS_EMBARGO_OFFSET], CBR_PUBLIC_EMBARGO);
        CBR_SET_PERSONAL_FLAG(own_status2,
            newbs[CBR_NEWBS_EMBARGO_OFFSET + 1u], CBR_PUBLIC_EMBARGO);
        CBR_SET_PERSONAL_FLAG(player_status2,
            newbs[CBR_NEWBS_ELECTRIFY_OFFSET], CBR_PUBLIC_ELECTRIFY);
        CBR_SET_PERSONAL_FLAG(own_status2,
            newbs[CBR_NEWBS_ELECTRIFY_OFFSET + 1u], CBR_PUBLIC_ELECTRIFY);
        CBR_SET_PERSONAL_FLAG(player_status2,
            newbs[CBR_NEWBS_SLOW_START_OFFSET], CBR_PUBLIC_SLOW_START);
        CBR_SET_PERSONAL_FLAG(own_status2,
            newbs[CBR_NEWBS_SLOW_START_OFFSET + 1u], CBR_PUBLIC_SLOW_START);
        CBR_SET_PERSONAL_FLAG(player_status2,
            newbs[CBR_NEWBS_SYRUP_BOMB_OFFSET], CBR_PUBLIC_SYRUP_BOMB);
        CBR_SET_PERSONAL_FLAG(own_status2,
            newbs[CBR_NEWBS_SYRUP_BOMB_OFFSET + 1u], CBR_PUBLIC_SYRUP_BOMB);
        CBR_SET_PERSONAL_FLAG(public_state->status3[1],
            newbs[CBR_NEWBS_DRAGON_CHEER_OFFSET], CBR_PUBLIC_DRAGON_CHEER);
        CBR_SET_PERSONAL_FLAG(own_status3,
            newbs[CBR_NEWBS_DRAGON_CHEER_OFFSET + 1u],
            CBR_PUBLIC_DRAGON_CHEER);
        CBR_SET_PERSONAL_FLAG(public_state->status3[1],
            newbs[CBR_NEWBS_PARADOX_STAT_OFFSET]
                || (player_disable[CBR_BOOSTER_ENERGY_OFFSET] & 1u),
            CBR_PUBLIC_PARADOX_BOOST);
        CBR_SET_PERSONAL_FLAG(own_status3,
            newbs[CBR_NEWBS_PARADOX_STAT_OFFSET + 1u]
                || (own_disable[CBR_BOOSTER_ENERGY_OFFSET] & 1u),
            CBR_PUBLIC_PARADOX_BOOST);
        CBR_SET_PERSONAL_FLAG(public_state->status3[1],
            newbs[CBR_NEWBS_POWDER_BITS_OFFSET] & 1u,
            CBR_PUBLIC_POWDER);
        CBR_SET_PERSONAL_FLAG(own_status3,
            newbs[CBR_NEWBS_POWDER_BITS_OFFSET] & 2u,
            CBR_PUBLIC_POWDER);
        CBR_SET_PERSONAL_FLAG(public_state->status3[1],
            newbs[CBR_NEWBS_TAR_SHOT_BITS_OFFSET] & 1u,
            CBR_PUBLIC_TAR_SHOT);
        CBR_SET_PERSONAL_FLAG(own_status3,
            newbs[CBR_NEWBS_TAR_SHOT_BITS_OFFSET] & 2u,
            CBR_PUBLIC_TAR_SHOT);
        CBR_SET_PERSONAL_FLAG(public_state->status3[1],
            newbs[CBR_NEWBS_OCTOLOCK_BITS_OFFSET] & 1u,
            CBR_PUBLIC_OCTOLOCK);
        CBR_SET_PERSONAL_FLAG(own_status3,
            newbs[CBR_NEWBS_OCTOLOCK_BITS_OFFSET] & 2u,
            CBR_PUBLIC_OCTOLOCK);
        CBR_SET_PERSONAL_FLAG(public_state->status3[1],
            newbs[CBR_NEWBS_NO_RETREAT_BITS_OFFSET] & 1u,
            CBR_PUBLIC_NO_RETREAT);
        CBR_SET_PERSONAL_FLAG(own_status3,
            newbs[CBR_NEWBS_NO_RETREAT_BITS_OFFSET] & 2u,
            CBR_PUBLIC_NO_RETREAT);
        CBR_SET_PERSONAL_FLAG(public_state->status3[1],
            newbs[CBR_NEWBS_SALT_CURE_BITS_OFFSET] & 1u,
            CBR_PUBLIC_SALT_CURE);
        CBR_SET_PERSONAL_FLAG(own_status3,
            newbs[CBR_NEWBS_SALT_CURE_BITS_OFFSET] & 2u,
            CBR_PUBLIC_SALT_CURE);
#undef CBR_SET_PERSONAL_FLAG
        pack_personal_effects(public_state->personal_effects_packed,
                              0u, player_disable, newbs);
        pack_personal_effects(public_state->personal_effects_packed,
                              1u, own_disable, newbs);
    }
    public_state->status2[0] = own_status2;
    public_state->status2[1] = player_status2;
    public_state->status3[0] = own_status3;

    active_own = G_BATTLER_PARTY_INDEXES[1];
    for (index = 0u; index < CBR_SELECTION_SIZE; ++index) {
        u32 raw_status = FN_GET_MON_DATA(
            &G_ENEMY_PARTY[index], CBR_MON_DATA_STATUS, NULL);
        own_party_statuses[index] = major_status(raw_status, &status_detail);
    }
    if (active_own < CBR_SELECTION_SIZE)
        own_party_statuses[active_own] = public_state->own_status;
    for (index = 0u; index < CBR_SELECTION_SIZE; ++index)
        pack_bits(public_state->own_party_status_packed,
                  (u16)index * 3u, own_party_statuses[index], 3u);

    pack_bits(public_state->wish_future_packed, 0u,
              clamp_public_value(
                  G_WISH_FUTURE_KNOCK[CBR_WISH_COUNTER_OFFSET], 3u), 2u);
    pack_bits(public_state->wish_future_packed, 2u,
              clamp_public_value(
                  G_WISH_FUTURE_KNOCK[CBR_WISH_COUNTER_OFFSET + 1u], 3u), 2u);
    pack_bits(public_state->wish_future_packed, 4u,
              clamp_public_value(G_WISH_FUTURE_KNOCK[0u], 3u), 2u);
    pack_bits(public_state->wish_future_packed, 6u,
              clamp_public_value(G_WISH_FUTURE_KNOCK[1u], 3u), 2u);
    if (G_WISH_FUTURE_KNOCK[0u] != 0u)
        pack_bits(public_state->wish_future_packed, 8u,
                  read16(G_WISH_FUTURE_KNOCK
                         + CBR_WISH_FUTURE_MOVE_OFFSET), 11u);
    if (G_WISH_FUTURE_KNOCK[1u] != 0u)
        pack_bits(public_state->wish_future_packed, 19u,
                  read16(G_WISH_FUTURE_KNOCK
                         + CBR_WISH_FUTURE_MOVE_OFFSET + 2u), 11u);
    if (newbs_valid) {
        pack_bits(public_state->wish_future_packed, 30u,
                  newbs[CBR_NEWBS_HEALING_WISH_BITS_OFFSET] & 1u, 1u);
        pack_bits(public_state->wish_future_packed, 31u,
                  (newbs[CBR_NEWBS_HEALING_WISH_BITS_OFFSET] >> 1) & 1u, 1u);
    }

    write16((volatile u8 *)public_state
                + offsetof(CodexBattlePublicStateV2, weather),
            *G_BATTLE_WEATHER);
    public_state->weather_duration = G_WISH_FUTURE_KNOCK[0x28u];
    public_state->terrain = *G_TERRAIN_TYPE;
    for (index = 0u; index < 2u; ++index) {
        volatile u8 *side = G_SIDE_TIMERS + (u32)index * 12u;
        public_state->side_statuses[index] = G_SIDE_STATUSES[index];
        classic[index * 4u] = side[0u];
        classic[index * 4u + 1u] = side[2u];
        classic[index * 4u + 2u] = side[4u];
        classic[index * 4u + 3u] = side[6u];
        public_state->entry_hazards[index] = side[10u];
    }
    pack_nibbles(public_state->classic_side_timers_packed, classic, 8u);
}

static void commit_public_state(void)
{
    volatile CodexBattlePublicStateV2 *public_state =
        &gCodexBattleRuntimeState->public_state;
    u32 sequence = next_sequence(public_state->sequence);
    public_state->struct_size = sizeof(*public_state);
    public_state->version = CBR_PUBLIC_STATE_VERSION;
    public_state->event_capacity = CBR_PUBLIC_EVENT_CAPACITY;
    public_state->crc32 = public_state_crc();
    barrier();
    public_state->sequence_inverse = ~sequence;
    barrier();
    public_state->sequence = sequence;
}

static void publish_public_state(void)
{
    fill_public_current_state();
    commit_public_state();
}

static u16 public_string_crc16(const volatile u8 *bytes)
{
    u32 crc = 0xFFFFFFFFu;
    u32 index;
    for (index = 0u; index < CBR_PUBLIC_MESSAGE_LOADER_SIZE; ++index) {
        u8 value = bytes[index];
        crc = crc_byte(crc, value);
        if (value == 0xFFu)
            break;
    }
    return (u16)(crc ^ 0xFFFFFFFFu);
}

static const volatile u8 *public_message_template(
    u16 message_id, const volatile u8 *buffer, u16 *limit)
{
    u32 address;
    if (message_id == CBR_STRING_CUSTOM) {
        *limit = CBR_PUBLIC_MESSAGE_LOADER_SIZE;
        return buffer + CBR_PUBLIC_MESSAGE_LOADER_OFFSET;
    }
    if (message_id < CBR_BATTLE_STRING_ID_ADDER
        || message_id >= CBR_BATTLE_STRING_ID_ADDER
            + CBR_BATTLE_STRING_COUNT) {
        *limit = 0u;
        return NULL;
    }
    address = G_BATTLE_STRINGS_TABLE[
        message_id - CBR_BATTLE_STRING_ID_ADDER];
    if (address < 0x08000000u || address >= 0x0A000000u) {
        *limit = 0u;
        return NULL;
    }
    *limit = CBR_PUBLIC_MESSAGE_LOADER_SIZE;
    return PTR(const volatile u8 *, address);
}

static u8 public_template_uses(const volatile u8 *text, u16 limit, u8 token)
{
    u16 index;
    if (text == NULL)
        return 0u;
    for (index = 0u; index + 1u < limit && text[index] != 0xFFu; ++index) {
        if (text[index] == CBR_TEXT_PLACEHOLDER
            && text[index + 1u] == token)
            return 1u;
    }
    return 0u;
}

static u8 public_item_subject_bank(
    const volatile u8 *text, u16 limit, const volatile u8 *buffer, u8 bank)
{
    u8 subject = 0xFFu;
    u16 index;
    if (text == NULL)
        return subject;
    for (index = 0u; index + 1u < limit && text[index] != 0xFFu; ++index) {
        u8 token;
        u8 buffer_index = 0u;
        const volatile u8 *detail;
        if (text[index] != CBR_TEXT_PLACEHOLDER)
            continue;
        token = text[++index];
        if (token == 0x0Fu)
            subject = *G_BANK_ATTACKER & 3u;
        else if (token == 0x10u)
            subject = *G_BANK_TARGET & 3u;
        else if (token == 0x11u)
            subject = *G_EFFECT_BANK & 3u;
        else if (token == 0x12u)
            subject = bank & 3u;
        else if (token == 0x13u)
            subject = buffer[11u] & 3u;
        else if (token == CBR_TEXT_LAST_ITEM)
            return subject;
        else if (token == CBR_TEXT_BUFF1)
            buffer_index = 0u;
        else if (token == CBR_TEXT_BUFF2)
            buffer_index = 1u;
        else if (token == CBR_TEXT_BUFF3)
            buffer_index = 2u;
        else
            continue;
        if (token != CBR_TEXT_BUFF1 && token != CBR_TEXT_BUFF2
            && token != CBR_TEXT_BUFF3)
            continue;
        detail = buffer + CBR_PUBLIC_TEXT_BUFFERS_OFFSET
            + (u32)buffer_index * CBR_PUBLIC_TEXT_BUFFER_SIZE;
        if (detail[0] == CBR_TEXT_PLACEHOLDER
            && detail[1] == CBR_BUFFER_ITEM)
            return subject;
    }
    return 0xFFu;
}

static u8 public_event_context(
    u16 message_id, u8 bank, const volatile u8 *buffer,
    u16 *item, u16 *ability)
{
    static const u8 buffer_tokens[3] = {
        CBR_TEXT_BUFF1, CBR_TEXT_BUFF2, CBR_TEXT_BUFF3,
    };
    const volatile u8 *text;
    u16 limit;
    u8 flags = 0u;
    u8 index;
    u8 attacker = *G_BANK_ATTACKER & 3u;
    u8 target = *G_BANK_TARGET & 3u;
    u8 effect = *G_EFFECT_BANK & 3u;
    u8 scripting = buffer[11u] & 3u;
    (void)bank;
    *item = 0u;
    *ability = 0u;
    text = public_message_template(message_id, buffer, &limit);
    if (message_id == 4u || public_template_uses(
            text, limit, CBR_TEXT_CURRENT_MOVE))
        flags |= 0x04u;
    if (public_template_uses(text, limit, CBR_TEXT_LAST_MOVE))
        flags |= 0x08u;
    if (public_template_uses(text, limit, CBR_TEXT_LAST_ITEM)) {
        *item = read16(buffer + 8u);
        flags |= 0x01u;
    }
    if (public_template_uses(text, limit, CBR_TEXT_LAST_ABILITY)) {
        *ability = read16(buffer + 18u);
        flags |= 0x02u;
    } else if (public_template_uses(
                   text, limit, CBR_TEXT_ATTACKER_ABILITY)) {
        *ability = read16(buffer + CBR_PUBLIC_ABILITIES_OFFSET
                          + (u32)attacker * 2u);
        flags |= 0x02u;
    } else if (public_template_uses(
                   text, limit, CBR_TEXT_TARGET_ABILITY)) {
        *ability = read16(buffer + CBR_PUBLIC_ABILITIES_OFFSET
                          + (u32)target * 2u);
        flags |= 0x02u;
    } else if (public_template_uses(
                   text, limit, CBR_TEXT_SCRIPTING_ABILITY)) {
        *ability = read16(buffer + CBR_PUBLIC_ABILITIES_OFFSET
                          + (u32)scripting * 2u);
        flags |= 0x02u;
    } else if (public_template_uses(
                   text, limit, CBR_TEXT_EFFECT_ABILITY)) {
        *ability = read16(buffer + CBR_PUBLIC_ABILITIES_OFFSET
                          + (u32)effect * 2u);
        flags |= 0x02u;
    }
    for (index = 0u; index < 3u; ++index) {
        const volatile u8 *detail;
        if (!public_template_uses(text, limit, buffer_tokens[index]))
            continue;
        flags |= 0x10u;
        detail = buffer + CBR_PUBLIC_TEXT_BUFFERS_OFFSET
            + (u32)index * CBR_PUBLIC_TEXT_BUFFER_SIZE;
        if (detail[0] != CBR_TEXT_PLACEHOLDER)
            continue;
        if (detail[1] == CBR_BUFFER_ITEM) {
            *item = read16(detail + 2u);
            flags |= 0x01u;
        } else if (detail[1] == CBR_BUFFER_ABILITY) {
            *ability = read16(detail + 2u);
            flags |= 0x02u;
        }
    }
    if ((flags & 0x01u) != 0u && *item != 0u) {
        u8 item_bank = public_item_subject_bank(text, limit, buffer, bank);
        if (item_bank == 0u
            || (item_bank == 0xFFu && (bank & 3u) == 0u
                && *item == read16(
                    battle_mon(0u) + CBR_BATTLE_MON_ITEM_OFFSET)))
            gCodexBattleRuntimeState->public_state.player_revealed_item_id =
                *item;
    }
    return flags;
}

static void remember_public_player_move(u16 move)
{
    volatile u16 *moves =
        gCodexBattleRuntimeState->public_state.player_revealed_moves;
    u8 index;
    if (move == 0u)
        return;
    for (index = 0u; index < 4u; ++index) {
        if (moves[index] == move)
            return;
        if (moves[index] == 0u) {
            moves[index] = move;
            return;
        }
    }
}

static void record_public_event(u8 bank, const volatile u8 *buffer)
{
    volatile CodexBattlePublicStateV2 *public_state =
        &gCodexBattleRuntimeState->public_state;
    volatile CodexBattlePublicEventV2 *event =
        &public_state->events[public_state->event_head];
    u16 sequence = (u16)(public_state->event_sequence + 1u);
    u16 message_id = read16(buffer + 2u);
    u16 current_move = read16(buffer + 4u);
    u16 original_move = read16(buffer + 6u);
    u16 last_item;
    u16 last_ability;
    u16 custom_crc = message_id == CBR_STRING_CUSTOM
        ? public_string_crc16(buffer + CBR_PUBLIC_MESSAGE_LOADER_OFFSET) : 0u;
    u8 scr_active = buffer[11u] & 3u;
    u8 string_bank = buffer[14u] & 3u;
    u8 banks = (u8)((bank & 3u) | (scr_active << 2)
        | (string_bank << 4) | ((*G_BANK_ATTACKER & 3u) << 6));
    u8 flags = (u8)((*G_BANK_TARGET & 3u)
        | ((*G_EFFECT_BANK & 3u) << 2)
        | (buffer[16u] ? 0x10u : 0u)
        | (buffer[17u] ? 0x20u : 0u)
        | (public_player_identity() << 6u));
    u8 context = public_event_context(
        message_id, bank, buffer, &last_item, &last_ability);
    /* Store only a move that has actually reached the public USEDMOVE text.
     * For Z/Max moves original_move is the underlying selected move, while
     * current_move is the temporary presentation move.  AI history can hold
     * the latter before/after presentation and is not a public-info source. */
    if (message_id == 4u && (*G_BANK_ATTACKER & 3u) == 0u)
        remember_public_player_move(
            original_move != 0u ? original_move : current_move);
    if ((bank & 3u) == 0u && last_ability != 0u)
        public_state->player_revealed_ability_id = last_ability;
    if (sequence == 0u)
        sequence = 1u;
    clear_bytes(event->packed, sizeof(event->packed));
    pack_bits(event->packed, 0u, message_id, 9u);
    pack_bits(event->packed, 9u, current_move, 11u);
    pack_bits(event->packed, 20u, original_move, 11u);
    pack_bits(event->packed, 31u, last_item, 10u);
    pack_bits(event->packed, 41u, last_ability, 10u);
    pack_bits(event->packed, 51u, custom_crc, 16u);
    pack_bits(event->packed, 67u, banks, 8u);
    pack_bits(event->packed, 75u, flags, 8u);
    pack_bits(event->packed, 83u, context, 5u);
    public_state->event_sequence = sequence;
    public_state->event_head = (u8)((public_state->event_head + 1u)
                                    % CBR_PUBLIC_EVENT_CAPACITY);
    if (public_state->event_count < CBR_PUBLIC_EVENT_CAPACITY)
        ++public_state->event_count;
}

static void record_public_ability_popup(u8 bank)
{
    volatile CodexBattlePublicStateV2 *public_state =
        &gCodexBattleRuntimeState->public_state;
    volatile CodexBattlePublicEventV2 *event =
        &public_state->events[public_state->event_head];
    u16 sequence = (u16)(public_state->event_sequence + 1u);
    u16 ability = read16(G_ABILITY_POPUP_HELPER);
    u8 banks = (u8)((bank & 3u) | ((bank & 3u) << 2)
        | ((bank & 3u) << 4) | ((*G_BANK_ATTACKER & 3u) << 6));
    u8 flags = (u8)((*G_BANK_TARGET & 3u)
        | ((*G_EFFECT_BANK & 3u) << 2)
        | (public_player_identity() << 6u));
    if (sequence == 0u)
        sequence = 1u;
    if ((bank & 3u) == 0u && ability != 0u)
        public_state->player_revealed_ability_id = ability;
    clear_bytes(event->packed, sizeof(event->packed));
    pack_bits(event->packed, 0u, CBR_EVENT_ABILITY_POPUP, 9u);
    pack_bits(event->packed, 41u, ability, 10u);
    pack_bits(event->packed, 67u, banks, 8u);
    pack_bits(event->packed, 75u, flags, 8u);
    pack_bits(event->packed, 83u, 0x02u, 5u);
    public_state->event_sequence = sequence;
    public_state->event_head = (u8)((public_state->event_head + 1u)
                                    % CBR_PUBLIC_EVENT_CAPACITY);
    if (public_state->event_count < CBR_PUBLIC_EVENT_CAPACITY)
        ++public_state->event_count;
}

static void capture_public_events(void)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    u8 active = 0u;
    u8 previous = state->public_event_active_mask;
    u8 bank;
    u8 changed = 0u;
    if (!runtime_active() || !state->player_selection_valid
        || !state->controller_installed) {
        state->public_event_active_mask = 0u;
        return;
    }
    for (bank = 0u; bank < 4u; ++bank) {
        const volatile u8 *buffer = G_BATTLE_BUFFER_A + (u32)bank * 0x200u;
        u8 bit = (u8)(1u << bank);
        if ((*G_BATTLE_CONTROLLER_EXEC_FLAGS & bit) != 0u
            && (buffer[0] == CBR_CONTROLLER_PRINTSTRING
                || (buffer[0] == CBR_CONTROLLER_BATTLEANIMATION
                    && buffer[1u] == CBR_ANIM_LOAD_ABILITY_POPUP))) {
            active |= bit;
            if ((previous & bit) == 0u) {
                /* Apply any switch identity reset before remembering facts
                 * from this newly public command. */
                fill_public_current_state();
                if (buffer[0] == CBR_CONTROLLER_PRINTSTRING)
                    record_public_event(bank, buffer);
                else
                    record_public_ability_popup(bank);
                changed = 1u;
            }
        }
    }
    state->public_event_active_mask = active;
    if (changed) {
        /* Recompute derived knowledge (for example HELD vs consumed) after
         * the event has revealed its move/item/ability.  Revealed facts are
         * persistent per active identity and are not cleared by this fill. */
        fill_public_current_state();
        commit_public_state();
    }
}

static u32 snapshot_crc(void)
{
    volatile CodexBattleRuntimeMailboxV2 *mailbox =
        gCodexBattleRuntimeMailbox;
    u32 crc = 0xFFFFFFFFu;
    const volatile u8 *header = (const volatile u8 *)mailbox;
    const volatile u8 *snapshot = (const volatile u8 *)&mailbox->snapshot;
    u32 index;
    for (index = 0u; index < 56u; ++index)
        crc = crc_byte(crc, header[index]);
    for (index = 4u; index < sizeof(mailbox->snapshot); ++index)
        crc = crc_byte(crc, snapshot[index]);
    return crc ^ 0xFFFFFFFFu;
}

static void publish_snapshot(u16 current_status)
{
    volatile CodexBattleRuntimeMailboxV2 *mailbox =
        gCodexBattleRuntimeMailbox;
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    volatile CodexBattleRuntimeSnapshotV2 *snapshot = &mailbox->snapshot;
    u32 sequence = next_sequence(mailbox->snapshot_sequence);
    u8 index;
    mailbox->phase = state->phase;
    mailbox->status = current_status;
    mailbox->match_id = state->match_id;
    mailbox->turn = state->turn;
    snapshot->payload_size = sizeof(*snapshot);
    snapshot->current_status = current_status;
    snapshot->rejected_count = state->rejected_count;
    snapshot->action_mask = 0u;
    if (runtime_active()) {
        if (state->phase == CODEX_RUNTIME_PHASE_BATTLE_AWAITING_ACTION)
            snapshot->action_mask = 0x0007u;
        else if (state->phase == CODEX_RUNTIME_PHASE_BATTLE_AWAITING_MOVE)
            snapshot->action_mask = 0x0005u;
        else if (state->phase == CODEX_RUNTIME_PHASE_BATTLE_AWAITING_SWITCH)
            snapshot->action_mask = 0x0006u;
    }
    snapshot->turn = state->turn;
    snapshot->legal_switch_mask = state->legal_switch_mask;
    snapshot->legal_move_mask = state->legal_move_mask;
    snapshot->phase_echo = state->phase;
    for (index = 0u; index < 4u; ++index)
        snapshot->legal_gimmicks[index] = state->legal_gimmicks[index];
    for (index = 0u; index < CBR_TEAM_SIZE; ++index) {
        snapshot->codex_preview_species[index] = state->team[index].species_id;
        snapshot->player_preview_species[index] =
            state->player_preview_species[index];
    }
    fill_snapshot_battle_state(snapshot);
    /* BattlePokemon/NewBS values are authoritative only after the manual
     * controller is installed.  Keep the last pre-battle public commit while
     * the stock party-selection UI owns the field flow. */
    if (!runtime_active() || state->controller_installed)
        publish_public_state();
    snapshot->crc32 = snapshot_crc();
    barrier();
    mailbox->snapshot_sequence_inverse = ~sequence;
    barrier();
    mailbox->snapshot_sequence = sequence;
}

static u8 mailbox_valid(void)
{
    volatile CodexBattleRuntimeMailboxV2 *mailbox =
        gCodexBattleRuntimeMailbox;
    return (u8)(mailbox->magic == CODEX_RUNTIME_MAGIC
        && mailbox->protocol_major == CODEX_RUNTIME_PROTOCOL_MAJOR
        && mailbox->protocol_minor == CODEX_RUNTIME_PROTOCOL_MINOR
        && mailbox->struct_size == CODEX_RUNTIME_MAILBOX_SIZE
        && mailbox->header_size == CODEX_RUNTIME_HEADER_SIZE
        && mailbox->snapshot_offset == CODEX_RUNTIME_SNAPSHOT_OFFSET
        && mailbox->snapshot_size == CODEX_RUNTIME_SNAPSHOT_SIZE
        && mailbox->request_offset == CODEX_RUNTIME_REQUEST_OFFSET
        && mailbox->request_size == CODEX_RUNTIME_REQUEST_SIZE
        && mailbox->request_payload_max == CODEX_RUNTIME_REQUEST_PAYLOAD_MAX
        && mailbox->stage_number == CODEX_RUNTIME_STAGE_NUMBER
        && mailbox->capabilities == CODEX_RUNTIME_CAPABILITIES
        && mailbox->stage_identity == CODEX_RUNTIME_STAGE_IDENTITY
        && mailbox->build_identity == CODEX_RUNTIME_BUILD_IDENTITY
        && mailbox->session_nonce != 0u
        && mailbox->session_nonce_inverse == ~mailbox->session_nonce);
}

CBR_EXPORT(CodexBattleRuntime_Initialize)
void CodexBattleRuntime_Initialize(void)
{
    volatile CodexBattleRuntimeMailboxV2 *mailbox =
        gCodexBattleRuntimeMailbox;
    u32 nonce = state_valid()
        ? gCodexBattleRuntimeState->session_nonce : *G_BASE_NONCE;
    if (nonce == 0u)
        nonce = 0x43425232u;
    if (!state_valid())
        initialize_state(nonce);
    if (!state_valid())
        return;
    clear_bytes(mailbox, CODEX_RUNTIME_MAILBOX_SIZE);
    mailbox->magic = CODEX_RUNTIME_MAGIC;
    mailbox->protocol_major = CODEX_RUNTIME_PROTOCOL_MAJOR;
    mailbox->protocol_minor = CODEX_RUNTIME_PROTOCOL_MINOR;
    mailbox->struct_size = CODEX_RUNTIME_MAILBOX_SIZE;
    mailbox->header_size = CODEX_RUNTIME_HEADER_SIZE;
    mailbox->snapshot_offset = CODEX_RUNTIME_SNAPSHOT_OFFSET;
    mailbox->snapshot_size = CODEX_RUNTIME_SNAPSHOT_SIZE;
    mailbox->request_offset = CODEX_RUNTIME_REQUEST_OFFSET;
    mailbox->request_size = CODEX_RUNTIME_REQUEST_SIZE;
    mailbox->request_payload_max = CODEX_RUNTIME_REQUEST_PAYLOAD_MAX;
    mailbox->stage_number = CODEX_RUNTIME_STAGE_NUMBER;
    mailbox->capabilities = CODEX_RUNTIME_CAPABILITIES;
    mailbox->stage_identity = CODEX_RUNTIME_STAGE_IDENTITY;
    mailbox->build_identity = CODEX_RUNTIME_BUILD_IDENTITY;
    mailbox->session_nonce = nonce;
    mailbox->session_nonce_inverse = ~nonce;
    mailbox->phase = gCodexBattleRuntimeState->phase;
    mailbox->status = gCodexBattleRuntimeState->status;
    mailbox->snapshot.response_sequence_inverse = ~0u;
    publish_snapshot(gCodexBattleRuntimeState->status);
}

static u32 member_seed(u8 slot)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    return mix32(state->session_nonce ^ state->match_id
                 ^ ((u32)(slot + 1u) * 0x9E3779B9u));
}

static u8 member_valid_and_resolve(CodexBattleTeamMemberV1 *member, u8 slot)
{
    u32 seed = member_seed(slot);
    u16 ev_total = 0u;
    u8 index;
    u8 saw_zero = 0u;
    if (member->reserved != 0u || member->species_id == 0u
        || member->species_id > CODEX_RUNTIME_SPECIES_MAX
        || member->level == 0u || member->level > 100u)
        return 0u;
    if (!(member->presence & CBR_PRESENCE_ITEM))
        member->held_item_id = 0u;
    if (!held_item_safe(member->held_item_id))
        return 0u;
    if (!(member->presence & CBR_PRESENCE_MOVES)) {
        member->moves[0] = 33u;
        member->moves[1] = 0u;
        member->moves[2] = 0u;
        member->moves[3] = 0u;
    }
    for (index = 0u; index < 4u; ++index) {
        if (member->moves[index] == 0u)
            saw_zero = 1u;
        else if (member->moves[index] > CODEX_RUNTIME_MOVE_MAX || saw_zero)
            return 0u;
    }
    if (member->moves[0] == 0u)
        return 0u;
    if (!(member->presence & CBR_PRESENCE_ABILITY))
        member->ability_slot = (u8)(seed % 3u);
    if (member->ability_slot > 2u)
        return 0u;
    if (!(member->presence & CBR_PRESENCE_NATURE))
        member->nature_id = (u8)((seed >> 8) % 25u);
    if (member->nature_id > 24u)
        return 0u;
    for (index = 0u; index < 6u; ++index) {
        if (!(member->presence & CBR_PRESENCE_IVS))
            member->ivs[index] = (u8)((seed >> ((index & 3u) * 5u)) & 31u);
        if (!(member->presence & CBR_PRESENCE_EVS))
            member->evs[index] = 0u;
        if (member->ivs[index] > 31u || member->evs[index] > 252u)
            return 0u;
        ev_total = (u16)(ev_total + member->evs[index]);
    }
    if (ev_total > 510u)
        return 0u;
    if (!(member->presence & CBR_PRESENCE_SHINY))
        member->shiny = 0u;
    if (member->shiny > 1u)
        return 0u;
    if (!(member->presence & CBR_PRESENCE_TERA))
        member->tera_type = (u8)((seed >> 16) % 18u);
    if (!type_valid(member->tera_type))
        return 0u;
    member->presence = 0xFFu;
    return 1u;
}

static void set_ability_slot(Pokemon100 *mon, u8 slot)
{
    u16 met = read16(mon->bytes + CBR_MET_BITS_OFFSET);
    u32 iv = read32(mon->bytes + CBR_IV_BITS_OFFSET);
    met &= (u16)~CBR_HIDDEN_ABILITY_MASK;
    iv &= ~CBR_ABILITY_NUM_MASK;
    if (slot == 1u)
        iv |= CBR_ABILITY_NUM_MASK;
    else if (slot == 2u)
        met |= CBR_HIDDEN_ABILITY_MASK;
    write16(mon->bytes + CBR_MET_BITS_OFFSET, met);
    write32(mon->bytes + CBR_IV_BITS_OFFSET, iv);
}

static u8 build_member(Pokemon100 *mon,
                       const volatile CodexBattleTeamMemberV1 *source,
                       u8 force_flat, u8 team_slot)
{
    CodexBattleTeamMemberV1 member;
    u32 value;
    u8 index;
    copy_bytes(&member, source, sizeof(member));
    clear_bytes(mon, sizeof(*mon));
    FN_CREATE_MON(mon, member.species_id,
                  force_flat ? 50u : member.level,
                  31u, 1u, member_personality(team_slot, member.shiny),
                  0u, 0u);
    value = member.held_item_id;
    FN_SET_MON_DATA(mon, CBR_MON_DATA_HELD_ITEM, &value);
    value = 0u;
    FN_SET_MON_DATA(mon, CBR_MON_DATA_PP_BONUSES, &value);
    for (index = 0u; index < 4u; ++index) {
        value = member.moves[index];
        FN_SET_MON_DATA(mon, CBR_MON_DATA_MOVE1 + index, &value);
        value = member.moves[index] == 0u ? 0u
            : FN_CALCULATE_PP(member.moves[index], 0u, index);
        FN_SET_MON_DATA(mon, CBR_MON_DATA_PP1 + index, &value);
    }
    for (index = 0u; index < 6u; ++index) {
        value = member.evs[index];
        FN_SET_MON_DATA(mon, CBR_MON_DATA_EV_HP + index, &value);
        value = member.ivs[index];
        FN_SET_MON_DATA(mon, CBR_MON_DATA_IV_HP + index, &value);
    }
    mon->bytes[CBR_NATURE_MINT_OFFSET] = (u8)(member.nature_id + 1u);
    mon->bytes[CBR_TERA_TYPE_OFFSET] = member.tera_type;
    set_ability_slot(mon, member.ability_slot);
    FN_CALCULATE_STATS(mon);
    write16(mon->bytes + CBR_HP_OFFSET,
            read16(mon->bytes + CBR_MAX_HP_OFFSET));
    return (u8)(FN_GET_MON_DATA(mon, CBR_MON_DATA_SPECIES, NULL)
        == member.species_id);
}

static u8 build_codex_selection(void)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    u8 index;
    clear_bytes(G_ENEMY_PARTY, CBR_TEAM_SIZE * CBR_MON_SIZE);
    for (index = 0u; index < CBR_SELECTION_SIZE; ++index) {
        u8 slot = state->codex_selected[index];
        if (slot < 1u || slot > CBR_TEAM_SIZE
            || !build_member(&G_ENEMY_PARTY[index],
                             &state->team[slot - 1u],
                             (u8)(state->level_mode == 0u),
                             (u8)(slot - 1u))) {
            clear_bytes(G_ENEMY_PARTY, CBR_TEAM_SIZE * CBR_MON_SIZE);
            *G_ENEMY_COUNT = 0u;
            return 0u;
        }
    }
    *G_ENEMY_COUNT = CBR_SELECTION_SIZE;
    return 1u;
}

static void accept_request(u32 sequence, u16 command, u16 next_phase)
{
    volatile CodexBattleRuntimeMailboxV2 *mailbox =
        gCodexBattleRuntimeMailbox;
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    state->last_request_sequence = sequence;
    state->last_rejected_sequence = 0u;
    state->last_rejected_request_crc32 = 0u;
    state->current_request_crc32 = 0u;
    state->phase = next_phase;
    state->status = CBR_STATUS_ACCEPTED;
    mailbox->snapshot.response_sequence = sequence;
    mailbox->snapshot.response_sequence_inverse = ~sequence;
    mailbox->snapshot.response_status = CBR_STATUS_ACCEPTED;
    mailbox->snapshot.response_error = CODEX_RUNTIME_ERROR_NONE;
    mailbox->snapshot.last_command = command;
    mailbox->snapshot.response_payload_size = 0u;
    mailbox->snapshot.last_accepted_sequence = sequence;
    publish_snapshot(CBR_STATUS_ACCEPTED);
}

static void reject_request(u32 sequence, u16 command, u16 error)
{
    volatile CodexBattleRuntimeMailboxV2 *mailbox =
        gCodexBattleRuntimeMailbox;
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    state->last_rejected_sequence = sequence;
    state->last_rejected_request_crc32 = state->current_request_crc32;
    ++state->rejected_count;
    mailbox->snapshot.response_sequence = sequence;
    mailbox->snapshot.response_sequence_inverse = ~sequence;
    mailbox->snapshot.response_status = CBR_STATUS_ERROR;
    mailbox->snapshot.response_error = error;
    mailbox->snapshot.last_command = command;
    mailbox->snapshot.response_payload_size = 0u;
    publish_snapshot(CBR_STATUS_ERROR);
}

static void restore_player_party(u16 reason)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    volatile u8 *save1;
    volatile u8 *save2;
    u32 key;
    u32 save_after;
    u8 index;
    if (!state_valid() || !state->active)
        return;
    copy_bytes(G_PLAYER_PARTY, state->player_party_backup,
               CBR_TEAM_SIZE * CBR_MON_SIZE);
    *G_PLAYER_COUNT = state->player_count_before;
    *G_ENEMY_COUNT = state->enemy_count_before;
    for (index = 0u; index < CBR_TEAM_SIZE; ++index)
        G_SELECTED[index] = state->selected_order_before[index];
    *G_BATTLE_FLAGS = state->battle_flags_before;
    *G_GLOBAL_RNG = state->rng_before;
    (void)FN_VAR_SET(CBR_VAR_FACILITY_NUMBER, state->facility_vars_before[0]);
    (void)FN_VAR_SET(CBR_VAR_PARTY_SIZE, state->facility_vars_before[1]);
    (void)FN_VAR_SET(CBR_VAR_LEVEL, state->facility_vars_before[2]);
    (void)FN_VAR_SET(CBR_VAR_BATTLE_TYPE, state->facility_vars_before[3]);
    (void)FN_VAR_SET(CBR_VAR_TIER, state->facility_vars_before[4]);
    if (state->facility_flag_before)
        (void)FN_FLAG_SET(CBR_FLAG_BATTLE_FACILITY);
    else
        (void)FN_FLAG_CLEAR(CBR_FLAG_BATTLE_FACILITY);
    if (state->disable_bag_flag_before)
        (void)FN_FLAG_SET(CBR_FLAG_DISABLE_BAG);
    else
        (void)FN_FLAG_CLEAR(CBR_FLAG_DISABLE_BAG);
    if (state->trainer_flag_before)
        (void)FN_FLAG_SET(CBR_FLAG_CODEX_TRAINER);
    else
        (void)FN_FLAG_CLEAR(CBR_FLAG_CODEX_TRAINER);
    save1 = *G_SAVE_BLOCK1_PTR;
    save2 = *G_SAVE_BLOCK2_PTR;
    if (save1 != NULL && save2 != NULL) {
        /* The engine may relocate both SaveBlocks and rotate its encryption
         * key while returning from trainerbattle.  Restore logical values
         * into the current blocks with the current key; copying the old raw
         * encrypted bytes would corrupt money and game statistics. */
        key = read32(save2 + CBR_SAVE_BLOCK2_ENCRYPTION_KEY_OFFSET);
        write32(save1 + CBR_SAVE_BLOCK1_MONEY_OFFSET,
                state->money_before ^ key);
        copy_bytes(save1 + CBR_SAVE_BLOCK1_DEX_SEEN_OFFSET,
                   state->save1_dex_seen_before,
                   CBR_SAVE_BLOCK1_DEX_SEEN_SIZE);
        for (index = 0u; index < CBR_GAME_STATS_COUNT; ++index) {
            write32(save1 + CBR_SAVE_BLOCK1_GAME_STATS_OFFSET
                    + (u32)index * 4u,
                    state->game_stats_before[index] ^ key);
        }
        copy_bytes(save2 + CBR_SAVE_BLOCK2_POKEDEX_OFFSET,
                   state->save2_pokedex_before,
                   CBR_SAVE_BLOCK2_POKEDEX_SIZE);
    }
    save_after = current_save_hash();
    clear_bytes(G_ENEMY_PARTY, CBR_TEAM_SIZE * CBR_MON_SIZE);
    state->cleanup_reason = reason;
    state->active = 0u;
    state->controller_installed = 0u;
    state->opponent_delegate = 0u;
    state->action_kind = 0u;
    state->switch_context = CBR_SWITCH_NONE;
    state->private_player_committed = 0u;
    state->private_seal_crc32 = 0u;
    state->private_seal_length = 0u;
    state->player_choice_observed = 0u;
    state->mechanic_used_mask = 0u;
    clear_bytes(state->player_selected, CBR_SELECTION_SIZE);
    state->public_flags = (u8)(state->save_hash_before == 0u
        || save_after == state->save_hash_before);
    state->phase = reason == CBR_CLEANUP_ABORT || reason == CBR_CLEANUP_RESET
        ? CODEX_RUNTIME_PHASE_ABORTED : CODEX_RUNTIME_PHASE_RESULT;
    state->status = CBR_STATUS_RESULT;
    publish_snapshot(CBR_STATUS_RESULT);
}

CBR_EXPORT(CodexBattleRuntime_Abort)
u16 CodexBattleRuntime_Abort(void)
{
    restore_player_party(CBR_CLEANUP_ABORT);
    set_result(CBR_RESULT_CANCELLED);
    return CBR_RESULT_CANCELLED;
}

static u8 action_allowed(u16 command, const volatile u8 *payload, u16 size)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    u16 phase = state->phase;
    if (!state->active || !state->player_selection_valid
        || state->disconnect_mode == CBR_DISCONNECT_CPU)
        return 0u;
    if (command == CODEX_RUNTIME_COMMAND_MOVE) {
        u8 slot;
        u8 gimmick;
        if ((phase != CODEX_RUNTIME_PHASE_BATTLE_AWAITING_ACTION
                && phase != CODEX_RUNTIME_PHASE_BATTLE_AWAITING_MOVE)
            || size != 3u)
            return 0u;
        slot = payload[0];
        gimmick = payload[2];
        if (slot < 1u || slot > 4u || payload[1] > 3u
            || gimmick > CBR_GIMMICK_TERA
            || !(state->legal_move_mask & (1u << (slot - 1u)))
            || !(state->legal_gimmicks[slot - 1u] & (1u << gimmick)))
            return 0u;
        state->action_kind = CBR_ACTION_MOVE;
        state->action_move = (u8)(slot - 1u);
        state->action_target = payload[1];
        state->action_gimmick = gimmick;
        return 1u;
    }
    if (command == CODEX_RUNTIME_COMMAND_SWITCH) {
        u8 slot;
        if ((phase != CODEX_RUNTIME_PHASE_BATTLE_AWAITING_ACTION
                && phase != CODEX_RUNTIME_PHASE_BATTLE_AWAITING_SWITCH)
            || size != 1u)
            return 0u;
        slot = payload[0];
        if (slot < 1u || slot > CBR_SELECTION_SIZE
            || !(state->legal_switch_mask & (1u << (slot - 1u))))
            return 0u;
        state->action_kind = CBR_ACTION_SWITCH;
        state->action_switch = (u8)(slot - 1u);
        if (phase == CODEX_RUNTIME_PHASE_BATTLE_AWAITING_ACTION)
            state->switch_context = CBR_SWITCH_VOLUNTARY;
        return 1u;
    }
    if (command == CODEX_RUNTIME_COMMAND_FORFEIT && size == 0u
        && (phase == CODEX_RUNTIME_PHASE_BATTLE_AWAITING_ACTION
            || phase == CODEX_RUNTIME_PHASE_BATTLE_AWAITING_MOVE
            || phase == CODEX_RUNTIME_PHASE_BATTLE_AWAITING_SWITCH)) {
        state->action_kind = CBR_ACTION_FORFEIT;
        return 1u;
    }
    if (command == CODEX_RUNTIME_COMMAND_DISCONNECT_CPU && size == 0u
        && phase == CODEX_RUNTIME_PHASE_BATTLE_AWAITING_ACTION) {
        state->disconnect_mode = CBR_DISCONNECT_CPU;
        state->action_kind = CBR_ACTION_CPU;
        return 1u;
    }
    if (command == CODEX_RUNTIME_COMMAND_DISCONNECT_FORFEIT && size == 0u
        && (phase == CODEX_RUNTIME_PHASE_BATTLE_AWAITING_ACTION
            || phase == CODEX_RUNTIME_PHASE_BATTLE_AWAITING_MOVE
            || phase == CODEX_RUNTIME_PHASE_BATTLE_AWAITING_SWITCH)) {
        state->disconnect_mode = CBR_DISCONNECT_FORFEIT;
        state->action_kind = CBR_ACTION_FORFEIT;
        return 1u;
    }
    return 0u;
}

static void execute_request(u32 sequence, u16 command,
                            const volatile u8 *payload, u16 size)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    if (command == CODEX_RUNTIME_COMMAND_CONFIGURE) {
        u32 preserved_nonce;
        if (state->active || state->field_completion_pending
            || size != 1u || payload[0] > 1u) {
            reject_request(sequence, command,
                (state->active || state->field_completion_pending)
                    ? CODEX_RUNTIME_ERROR_BUSY
                    : CODEX_RUNTIME_ERROR_PAYLOAD_FORMAT);
            return;
        }
        preserved_nonce = state->session_nonce;
        initialize_state(preserved_nonce);
        state->configured = 1u;
        state->level_mode = payload[0];
        state->match_id = mix32(preserved_nonce ^ sequence ^ 0x53494E47u);
        accept_request(sequence, command, CODEX_RUNTIME_PHASE_CONFIGURING);
        return;
    }
    if (command == CODEX_RUNTIME_COMMAND_UPLOAD_MEMBER) {
        CodexBattleTeamMemberV1 member;
        u8 slot;
        if (!state->configured || state->active
            || state->phase != CODEX_RUNTIME_PHASE_CONFIGURING
            || size != 33u || payload[0] >= CBR_TEAM_SIZE) {
            reject_request(sequence, command,
                           CODEX_RUNTIME_ERROR_PAYLOAD_FORMAT);
            return;
        }
        slot = payload[0];
        copy_bytes(&member, payload + 1u, sizeof(member));
        if (!member_valid_and_resolve(&member, slot)) {
            reject_request(sequence, command,
                           CODEX_RUNTIME_ERROR_INVALID_MEMBER);
            return;
        }
        copy_bytes(&state->team[slot], &member, sizeof(member));
        state->upload_mask |= (u8)(1u << slot);
        state->team_valid = 0u;
        accept_request(sequence, command, CODEX_RUNTIME_PHASE_CONFIGURING);
        return;
    }
    if (command == CODEX_RUNTIME_COMMAND_COMMIT_TEAM) {
        if (state->active
            || state->phase != CODEX_RUNTIME_PHASE_CONFIGURING
            || size != 0u || state->upload_mask != 0x3Fu) {
            reject_request(sequence, command,
                           CODEX_RUNTIME_ERROR_PAYLOAD_FORMAT);
            return;
        }
        state->team_valid = 1u;
        capture_player_preview();
        accept_request(sequence, command, CODEX_RUNTIME_PHASE_TEAM_PREVIEW);
        return;
    }
    if (command == CODEX_RUNTIME_COMMAND_CHOOSE_TEAM) {
        u8 index;
        u8 mask = 0u;
        if (!state->team_valid || state->active
            || state->phase != CODEX_RUNTIME_PHASE_TEAM_PREVIEW
            || size != 3u) {
            reject_request(sequence, command,
                           CODEX_RUNTIME_ERROR_PAYLOAD_FORMAT);
            return;
        }
        for (index = 0u; index < CBR_SELECTION_SIZE; ++index) {
            u8 slot = payload[index];
            if (slot < 1u || slot > CBR_TEAM_SIZE
                || (mask & (1u << (slot - 1u)))) {
                reject_request(sequence, command,
                               CODEX_RUNTIME_ERROR_PAYLOAD_FORMAT);
                return;
            }
            mask |= (u8)(1u << (slot - 1u));
            state->codex_selected[index] = slot;
        }
        state->codex_selection_valid = 1u;
        accept_request(sequence, command, CODEX_RUNTIME_PHASE_TEAM_PREVIEW);
        return;
    }
    if (command == CODEX_RUNTIME_COMMAND_ABORT) {
        if (size != 0u) {
            reject_request(sequence, command,
                           CODEX_RUNTIME_ERROR_PAYLOAD_FORMAT);
            return;
        }
        if (state->active && state->player_selection_valid) {
            /* A transport abort in a running battle must leave through the
             * stock controller/end path.  Mark it here; the interposer enters
             * the normal player-win handler at the next CHOOSEACTION (after
             * completing any open subchoice), then AfterBattle restores the
             * exact before image with an ABORT result. */
            state->cleanup_reason = CBR_CLEANUP_ABORT;
            state->disconnect_mode = CBR_DISCONNECT_FORFEIT;
            state->action_kind = 0u;
            accept_request(sequence, command,
                           CODEX_RUNTIME_PHASE_BATTLE_RESOLVING);
            return;
        }
        restore_player_party(CBR_CLEANUP_ABORT);
        accept_request(sequence, command, CODEX_RUNTIME_PHASE_ABORTED);
        return;
    }
    if (action_allowed(command, payload, size)) {
        accept_request(sequence, command, CODEX_RUNTIME_PHASE_BATTLE_RESOLVING);
        return;
    }
    reject_request(sequence, command, CODEX_RUNTIME_ERROR_ILLEGAL_ACTION);
}

static void poll_request(void)
{
    volatile CodexBattleRuntimeMailboxV2 *mailbox =
        gCodexBattleRuntimeMailbox;
    volatile CodexBattleRuntimeRequestV2 *request = &mailbox->request;
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    u32 sequence_before = request->request_sequence;
    u32 inverse_before = request->request_sequence_inverse;
    u8 local[CBR_REQUEST_COPY_SIZE];
    u32 expected;
    u16 command;
    u16 phase;
    u16 turn;
    u16 size;
    u32 sequence_after;
    if (sequence_before == 0u || inverse_before != ~sequence_before)
        return;
    if (sequence_before == state->last_request_sequence)
        return;
    copy_bytes(local, request, sizeof(local));
    barrier();
    sequence_after = request->request_sequence;
    if (sequence_after != sequence_before
        || request->request_sequence_inverse != inverse_before)
        return;
    state->current_request_crc32 = read32(local + 84u);
    if (sequence_after == state->last_rejected_sequence
        && state->current_request_crc32
            == state->last_rejected_request_crc32)
        return;
    expected = next_sequence(state->last_request_sequence);
    command = read16(local + 10u);
    phase = read16(local + 8u);
    turn = read16(local + 12u);
    size = read16(local + 14u);
    if (sequence_after != expected) {
        reject_request(sequence_after, command,
            sequence_after < expected ? CODEX_RUNTIME_ERROR_STALE_SEQUENCE
                                      : CODEX_RUNTIME_ERROR_FUTURE_SEQUENCE);
        return;
    }
    if (read32(local) != state->session_nonce) {
        reject_request(sequence_after, command,
                       CODEX_RUNTIME_ERROR_WRONG_NONCE);
        return;
    }
    if (size > CODEX_RUNTIME_REQUEST_PAYLOAD_MAX) {
        reject_request(sequence_after, command,
                       CODEX_RUNTIME_ERROR_OVERSIZE);
        return;
    }
    if (crc32_volatile(local + 20u, size) != read32(local + 16u)) {
        reject_request(sequence_after, command,
                       CODEX_RUNTIME_ERROR_PAYLOAD_CRC);
        return;
    }
    if (crc32_volatile(local, CBR_REQUEST_CRC_SIZE) != read32(local + 84u)) {
        reject_request(sequence_after, command,
                       CODEX_RUNTIME_ERROR_REQUEST_CRC);
        return;
    }
    if (phase != state->phase) {
        reject_request(sequence_after, command,
                       CODEX_RUNTIME_ERROR_WRONG_PHASE);
        return;
    }
    if (command != CODEX_RUNTIME_COMMAND_CONFIGURE
        && read32(local + 4u) != state->match_id) {
        reject_request(sequence_after, command,
                       CODEX_RUNTIME_ERROR_WRONG_MATCH);
        return;
    }
    if (runtime_active() && turn != state->turn) {
        reject_request(sequence_after, command,
                       CODEX_RUNTIME_ERROR_WRONG_TURN);
        return;
    }
    if (command < CODEX_RUNTIME_COMMAND_CONFIGURE
        || command > CODEX_RUNTIME_COMMAND_ABORT) {
        reject_request(sequence_after, command,
                       CODEX_RUNTIME_ERROR_UNKNOWN_COMMAND);
        return;
    }
    execute_request(sequence_after, command, local + 20u, size);
}

static void update_basic_legal(void)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    volatile u8 *battle_mon = G_BATTLE_MONS + 88u;
    u8 active_slot = G_BATTLER_PARTY_INDEXES[1];
    u8 index;
    state->legal_move_mask = 0u;
    for (index = 0u; index < 4u; ++index) {
        u16 move = read16(battle_mon + 0x0Cu + (u32)index * 2u);
        u8 pp = battle_mon[0x24u + index];
        u8 gimmicks = 1u << CBR_GIMMICK_NONE;
        if (move != 0u && pp != 0u) {
            state->legal_move_mask |= (u8)(1u << index);
            if (FN_CAN_MEGA(1u, 0u) != NULL)
                gimmicks |= 1u << CBR_GIMMICK_MEGA;
            if (FN_CAN_Z(1u, index, move) != 0u)
                gimmicks |= 1u << CBR_GIMMICK_Z;
            if (FN_CAN_DYNAMAX(1u))
                gimmicks |= 1u << CBR_GIMMICK_DYNAMAX;
            if (FN_CAN_TERA(1u))
                gimmicks |= 1u << CBR_GIMMICK_TERA;
        }
        state->legal_gimmicks[index] = gimmicks;
    }
    state->legal_switch_mask = 0u;
    for (index = 0u; index < CBR_SELECTION_SIZE; ++index) {
        if (index != active_slot
            && FN_GET_MON_DATA(&G_ENEMY_PARTY[index], CBR_MON_DATA_SPECIES,
                               NULL) != 0u
            && FN_GET_MON_DATA(&G_ENEMY_PARTY[index], CBR_MON_DATA_HP,
                               NULL) != 0u
            && FN_GET_MON_DATA(&G_ENEMY_PARTY[index], CBR_MON_DATA_IS_EGG,
                               NULL) == 0u)
            state->legal_switch_mask |= (u8)(1u << index);
    }
}

static u8 gimmick_legal_exact(const ChooseMoveStruct120 *info,
                              u8 move, u8 gimmick)
{
    if (move >= 4u || info->moves[move] == 0u
        || info->current_pp[move] == 0u)
        return 0u;
    if (gimmick == CBR_GIMMICK_NONE)
        return 1u;
    if (gimmick == CBR_GIMMICK_MEGA)
        return info->can_mega;
    if (gimmick == CBR_GIMMICK_Z)
        return (u8)(info->possible_z[move] != 0u);
    if (gimmick == CBR_GIMMICK_DYNAMAX)
        /* CFRU-JP leaves the legacy canDynamax byte unset and treats each
         * nonzero possibleMaxMoves entry as the authoritative permission. */
        return (u8)(info->possible_max[move] != 0u);
    if (gimmick == CBR_GIMMICK_TERA)
        return info->can_tera;
    return 0u;
}

static void publish_exact_move_legal(const ChooseMoveStruct120 *info)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    u8 index;
    state->legal_move_mask = 0u;
    for (index = 0u; index < 4u; ++index) {
        u8 mask = 0u;
        u8 gimmick;
        if (info->moves[index] != 0u && info->current_pp[index] != 0u)
            state->legal_move_mask |= (u8)(1u << index);
        for (gimmick = 0u; gimmick <= CBR_GIMMICK_TERA; ++gimmick) {
            if (gimmick_legal_exact(info, index, gimmick))
                mask |= (u8)(1u << gimmick);
        }
        state->legal_gimmicks[index] = mask;
    }
}

static void finish_manual_choice(void)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    state->action_kind = 0u;
    state->private_player_committed = 0u;
    state->player_choice_observed = 0u;
    state->private_seal_crc32 = 0u;
    state->private_seal_length = 0u;
    state->switch_context = CBR_SWITCH_NONE;
    ++state->turn;
}

static void complete_controller_choice(void)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    FN_OPPONENT_COMPLETE();
    state->controller_installed = 1u;
}

static void finish_codex_forfeit(u16 reason)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    /* ACTION_RUN is only honored for player-side banks in the fixed CFRU
     * turn-order code.  End an opponent forfeit through the engine's normal
     * B_OUTCOME_WON handler instead, then let the field trainerbattle command
     * return and call AfterBattle for exact restoration. */
    state->cleanup_reason = reason;
    *G_BATTLE_OUTCOME = 1u;
    *G_BATTLE_MAIN_FUNC = G_END_TURN_FUNCS[1u];
    complete_controller_choice();
    finish_manual_choice();
    state->phase = CODEX_RUNTIME_PHASE_BATTLE_RESOLVING;
    state->status = CBR_STATUS_ACTIVE;
    publish_snapshot(CBR_STATUS_ACTIVE);
}

static u32 choice_delegate(u8 command)
{
    if (command == CBR_CONTROLLER_CHOOSEACTION)
        return CODEX_RUNTIME_DELEGATE_CHOOSE_ACTION;
    if (command == CBR_CONTROLLER_CHOOSEMOVE)
        return CODEX_RUNTIME_DELEGATE_CHOOSE_MOVE;
    if (command == CBR_CONTROLLER_CHOOSEPOKEMON)
        return CODEX_RUNTIME_DELEGATE_CHOOSE_POKEMON;
    return 0u;
}

static void delegate_choice(u8 command)
{
    u32 delegate = choice_delegate(command);
    if (delegate != 0u)
        PTR(VoidFn, delegate)();
}

CBR_EXPORT(CodexBattleRuntime_OpponentController)
void CodexBattleRuntime_OpponentController(void)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    u8 active_bank = (u8)(*G_ACTIVE_BATTLER & 3u);
    u8 command = G_BATTLE_BUFFER_A[(u32)active_bank * 0x200u];
    if (!runtime_active()
        || !state->player_selection_valid
        || (state->disconnect_mode == CBR_DISCONNECT_CPU
            && state->action_kind != CBR_ACTION_CPU)
        || !(*G_BATTLE_FLAGS & CBR_BATTLE_TYPE_TRAINER)
        || *G_ACTIVE_BATTLER != 1u) {
        delegate_choice(command);
        return;
    }
    state->controller_installed = 1u;
    if (state->cleanup_reason == CBR_CLEANUP_ABORT) {
        if (command == CBR_CONTROLLER_CHOOSEACTION) {
            finish_codex_forfeit(CBR_CLEANUP_ABORT);
            return;
        }
        if (command == CBR_CONTROLLER_CHOOSEMOVE
            || command == CBR_CONTROLLER_CHOOSEPOKEMON) {
            /* Complete the choice already requested by the scheduler with
             * the pre-existing AI.  The following CHOOSEACTION enters the
             * normal battle-end handler, so no partial response is emitted. */
            state->phase = CODEX_RUNTIME_PHASE_BATTLE_RESOLVING;
            state->status = CBR_STATUS_ACTIVE;
            delegate_choice(command);
            return;
        }
    }
    if (command == CBR_CONTROLLER_CHOOSEACTION) {
        state->switch_context = CBR_SWITCH_NONE;
        update_basic_legal();
        if (state->action_kind == 0u) {
            state->phase = CODEX_RUNTIME_PHASE_BATTLE_AWAITING_ACTION;
            state->status = CBR_STATUS_WAITING;
            publish_snapshot(CBR_STATUS_WAITING);
            return;
        }
        if (state->action_kind == CBR_ACTION_MOVE) {
            FN_EMIT_TWO(1u, CBR_ACTION_USE_MOVE, 0u);
            complete_controller_choice();
            state->phase = CODEX_RUNTIME_PHASE_BATTLE_RESOLVING;
            return;
        }
        if (state->action_kind == CBR_ACTION_SWITCH) {
            state->switch_context = CBR_SWITCH_VOLUNTARY;
            FN_EMIT_TWO(1u, CBR_ENGINE_ACTION_SWITCH, 0u);
            complete_controller_choice();
            state->phase = CODEX_RUNTIME_PHASE_BATTLE_RESOLVING;
            state->status = CBR_STATUS_ACTIVE;
            publish_snapshot(CBR_STATUS_ACTIVE);
            return;
        }
        if (state->action_kind == CBR_ACTION_FORFEIT) {
            finish_codex_forfeit(CBR_CLEANUP_FORFEIT);
            return;
        }
        if (state->action_kind == CBR_ACTION_CPU) {
            state->action_kind = 0u;
            state->phase = CODEX_RUNTIME_PHASE_DISCONNECTED;
            state->status = CBR_STATUS_ACTIVE;
            state->controller_installed = 0u;
            publish_snapshot(CBR_STATUS_ACTIVE);
            delegate_choice(command);
            return;
        }
    } else if (command == CBR_CONTROLLER_CHOOSEMOVE) {
        const ChooseMoveStruct120 *info =
            (const ChooseMoveStruct120 *)(const void *)(G_BATTLE_BUFFER_A
                                                        + 0x204u);
        publish_exact_move_legal(info);
        if (state->action_kind != CBR_ACTION_MOVE
            || !gimmick_legal_exact(info, state->action_move,
                                    state->action_gimmick)) {
            state->action_kind = 0u;
            state->phase = CODEX_RUNTIME_PHASE_BATTLE_AWAITING_MOVE;
            state->status = CBR_STATUS_WAITING;
            publish_snapshot(CBR_STATUS_WAITING);
            return;
        }
        {
            u8 transfer[9];
            u8 gimmick = state->action_gimmick;
            transfer[0] = CBR_CONTROLLER_TWO_RETURN_VALUES;
            transfer[1] = CBR_ACTION_RUN_BATTLESCRIPT;
            transfer[2] = state->action_move;
            transfer[3] = state->action_target;
            transfer[4] = (u8)(gimmick == CBR_GIMMICK_MEGA);
            transfer[5] = 0u;
            transfer[6] = (u8)(gimmick == CBR_GIMMICK_Z);
            transfer[7] = (u8)(gimmick == CBR_GIMMICK_DYNAMAX);
            transfer[8] = (u8)(gimmick == CBR_GIMMICK_TERA);
            FN_PREPARE_BUFFER(1u, transfer, sizeof(transfer));
        }
        complete_controller_choice();
        finish_manual_choice();
        state->phase = CODEX_RUNTIME_PHASE_BATTLE_RESOLVING;
        publish_snapshot(CBR_STATUS_ACTIVE);
        return;
    } else if (command == CBR_CONTROLLER_CHOOSEPOKEMON) {
        update_basic_legal();
        if (state->action_kind != CBR_ACTION_SWITCH
            || !(state->legal_switch_mask & (1u << state->action_switch))) {
            state->action_kind = 0u;
            state->switch_context = CBR_SWITCH_FORCED;
            state->phase = CODEX_RUNTIME_PHASE_BATTLE_AWAITING_SWITCH;
            state->status = CBR_STATUS_WAITING;
            publish_snapshot(CBR_STATUS_WAITING);
            return;
        }
        /* The upstream opponent handler also maintains switchoutIndex,
         * monToSwitchIntoId and its AI cache.  Seed only the explicit slot,
         * then delegate the stock CHOOSEPOKEMON handler so all engine-owned
         * switch bookkeeping remains exact. */
        {
            volatile u8 *battle = *G_BATTLE_STRUCT_PTR;
            if ((u32)(uintptr_t)battle >= 0x02000000u
                && (u32)(uintptr_t)battle < 0x02040000u) {
                battle[CBR_BATTLE_STRUCT_SWITCHOUT_INDEX_OFFSET
                       + (*G_ACTIVE_BATTLER & 1u)] = state->action_switch;
            }
        }
        delegate_choice(command);
        state->controller_installed = 1u;
        finish_manual_choice();
        state->phase = CODEX_RUNTIME_PHASE_BATTLE_RESOLVING;
        publish_snapshot(CBR_STATUS_ACTIVE);
        return;
    }
    delegate_choice(command);
}

static void install_controller(void)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    volatile u8 *battle;
    if (!runtime_active()
        || !state->player_selection_valid
        || state->disconnect_mode == CBR_DISCONNECT_CPU
        || !(*G_BATTLE_FLAGS & CBR_BATTLE_TYPE_TRAINER)
        || *G_BATTLERS_COUNT < 2u)
        return;
    /* trainerbattle initializes its own flags after FieldPrepareBattle.  Keep
     * only the ordinary Dynamax permission bit asserted locally; never add
     * BATTLE_TOWER or any Raid ownership state. */
    *G_BATTLE_FLAGS |= CBR_BATTLE_TYPE_DYNAMAX;
    (void)FN_FLAG_SET(CBR_FLAG_DISABLE_BAG);
    battle = *G_BATTLE_STRUCT_PTR;
    if ((u32)(uintptr_t)battle >= 0x02000000u
        && (u32)(uintptr_t)battle < 0x02040000u) {
        /* Every opponent slot is already accounted for, so the stock faint
         * path never enters EXP/EV distribution or prints an EXP message. */
        battle[CBR_BATTLE_STRUCT_GIVEN_EXP_OFFSET] = 0x3Fu;
    }
}

static u8 is_choice_command(u8 command)
{
    return (u8)(command == CBR_CONTROLLER_CHOOSEACTION
        || command == CBR_CONTROLLER_CHOOSEMOVE
        || command == CBR_CONTROLLER_CHOOSEPOKEMON);
}

static void observe_private_player_choice(void)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    u8 command;
    if (!runtime_active() || !state->player_selection_valid)
        return;
    command = G_BATTLE_BUFFER_A[0];
    if (!is_choice_command(command)) {
        state->player_choice_observed = 0u;
        return;
    }
    if ((*G_BATTLE_CONTROLLER_EXEC_FLAGS & 1u) != 0u) {
        state->player_choice_observed = 1u;
        state->private_player_committed = 0u;
        state->private_seal_crc32 = 0u;
        state->private_seal_length = 0u;
        return;
    }
    if (state->player_choice_observed
        && !state->private_player_committed) {
        state->private_seal_crc32 = crc32_volatile(
            G_BATTLE_BUFFER_B, CBR_PRIVATE_COMMAND_SIZE);
        state->private_seal_length = CBR_PRIVATE_COMMAND_SIZE;
        state->private_player_committed = 1u;
    }
}

static void sanitize_player_selection_order(void)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    u8 used = 0u;
    u8 valid = 0u;
    u8 index;
    if (!runtime_active()
        || state->phase != CODEX_RUNTIME_PHASE_AWAITING_PLAYER_SELECTION)
        return;
    for (index = 0u; index < CBR_SELECTION_SIZE; ++index) {
        u8 slot = G_SELECTED[index];
        if (slot < 1u || slot > state->player_count_before
            || (used & (u8)(1u << (slot - 1u))))
            break;
        used |= (u8)(1u << (slot - 1u));
        ++valid;
    }
    for (index = valid; index < CBR_TEAM_SIZE; ++index)
        G_SELECTED[index] = 0u;
}

CBR_EXPORT(CodexBattleRuntime_Poll)
void CodexBattleRuntime_Poll(void)
{
    u32 base_nonce = *G_BASE_NONCE;
    if (!state_valid())
        initialize_state(base_nonce);
    if (!state_valid())
        return;
    /* A valid Stage 44 match keeps its established nonce.  A real core reset
     * invalidates state magic and takes the initialization path above. */
    base_nonce = gCodexBattleRuntimeState->session_nonce;
    if (!mailbox_valid() || gCodexBattleRuntimeMailbox->session_nonce != base_nonce) {
        gCodexBattleRuntimeState->session_nonce = base_nonce;
        CodexBattleRuntime_Initialize();
    }
    sanitize_player_selection_order();
    capture_public_events();
    observe_private_player_choice();
    poll_request();
    install_controller();
}

CBR_EXPORT(CodexBattleRuntime_ReadKeysAdapter)
void CodexBattleRuntime_ReadKeysAdapter(void)
{
    FN_READ_KEYS_DELEGATE();
    CodexBattleRuntime_Poll();
}

CBR_EXPORT(CodexBattleRuntime_BuildTrainerPartyAdapter)
void CodexBattleRuntime_BuildTrainerPartyAdapter(void)
{
    u16 trainer_id;
    u8 party_size;

    FN_TRAINER_PARTY_DELEGATE();
    trainer_id = *G_TRAINER_OPPONENT_A;
    party_size = G_TRAINER_TABLE[(u32)trainer_id * CBR_TRAINER_RECORD_SIZE
                                + CBR_TRAINER_PARTY_SIZE_OFFSET];
    if (trainer_id != 0u && party_size >= 1u && party_size <= CBR_TEAM_SIZE)
        *G_ENEMY_COUNT = party_size;
    if (runtime_active())
        (void)build_codex_selection();
}

CBR_EXPORT(CodexBattleRuntime_SaveLoadAdapter)
u8 CodexBattleRuntime_SaveLoadAdapter(u8 save_type)
{
    if (runtime_active())
        restore_player_party(CBR_CLEANUP_RESET);
    return FN_SAVE_LOAD_DELEGATE(save_type);
}

CBR_EXPORT(CodexBattleRuntime_FindDynamaxBandAdapter)
u16 CodexBattleRuntime_FindDynamaxBandAdapter(u8 battler)
{
    /* This is a virtual battle-local permission only.  No bag, trainer
     * record or save byte is written. */
    if (runtime_active() && gCodexBattleRuntimeState->player_selection_valid)
        return 347u;
    return FN_FIND_DYNAMAX_BAND_DELEGATE(battler);
}

static u8 policy_can(PolicyCanFn delegate, u8 battler, u8 upstream)
{
    if (!runtime_active())
        return delegate(battler, upstream);
    /* Each fixed CFRU-JP Can* function calls this adapter before performing
     * its own Species/item/move, used-state and cross-gimmick checks.  Codex
     * Battle opens only that leading battle-mode/story gate.  Returning true
     * here also remains necessary while a mon is already Dynamaxed: the move
     * menu calls DynamaxEnabled again to populate possibleMaxMoves, and
     * closing this gate turns every displayed Max Move into an empty name.
     * Normal, Factory, Mirage and Raid battles still take the exact delegate
     * path above. */
    (void)delegate;
    (void)battler;
    (void)upstream;
    return 1u;
}

static u8 policy_mark(PolicyMarkFn delegate, u8 battler, u8 mechanic)
{
    u8 bit = (u8)(1u << ((battler & 1u) * 4u + mechanic));
    if (!runtime_active())
        return delegate(battler);
    /* Activation reaches this hook only after the fixed CFRU-JP engine has
     * accepted the compatible gimmick and updated its native gNewBS state.
     * Do not impose the T06 battle-wide single-mode policy on this dedicated
     * UPSTREAM_OPEN battle.  Native Mega/Z/Dynamax/Terastal used flags and
     * interaction predicates remain authoritative; this byte is telemetry. */
    gCodexBattleRuntimeState->mechanic_used_mask |= bit;
    return 1u;
}

CBR_EXPORT(CodexBattleRuntime_CanMegaAdapter)
u8 CodexBattleRuntime_CanMegaAdapter(u8 battler, u8 upstream)
{ return policy_can(FN_POLICY_CAN_MEGA, battler, upstream); }

CBR_EXPORT(CodexBattleRuntime_MarkMegaAdapter)
u8 CodexBattleRuntime_MarkMegaAdapter(u8 battler)
{ return policy_mark(FN_POLICY_MARK_MEGA, battler, 0u); }

CBR_EXPORT(CodexBattleRuntime_CanZAdapter)
u8 CodexBattleRuntime_CanZAdapter(u8 battler, u8 upstream)
{ return policy_can(FN_POLICY_CAN_Z, battler, upstream); }

CBR_EXPORT(CodexBattleRuntime_MarkZAdapter)
u8 CodexBattleRuntime_MarkZAdapter(u8 battler)
{ return policy_mark(FN_POLICY_MARK_Z, battler, 1u); }

CBR_EXPORT(CodexBattleRuntime_CanDynamaxAdapter)
u8 CodexBattleRuntime_CanDynamaxAdapter(u8 battler, u8 upstream)
{ return policy_can(FN_POLICY_CAN_DYNAMAX, battler, upstream); }

CBR_EXPORT(CodexBattleRuntime_MarkDynamaxAdapter)
u8 CodexBattleRuntime_MarkDynamaxAdapter(u8 battler)
{ return policy_mark(FN_POLICY_MARK_DYNAMAX, battler, 2u); }

CBR_EXPORT(CodexBattleRuntime_CanTeraAdapter)
u8 CodexBattleRuntime_CanTeraAdapter(u8 battler, u8 upstream)
{ return policy_can(FN_POLICY_CAN_TERA, battler, upstream); }

CBR_EXPORT(CodexBattleRuntime_MarkTeraAdapter)
u8 CodexBattleRuntime_MarkTeraAdapter(u8 battler)
{ return policy_mark(FN_POLICY_MARK_TERA, battler, 3u); }

CBR_EXPORT(CodexBattleRuntime_FieldBeginPlayerSelection)
u16 CodexBattleRuntime_FieldBeginPlayerSelection(void)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    u8 count;
    u8 battle_capable = 0u;
    u8 index;
    if (!state_valid() || !state->team_valid
        || !state->codex_selection_valid
        || !player_preview_matches_current_party()) {
        set_result(CBR_RESULT_NOT_READY);
        return CBR_RESULT_NOT_READY;
    }
    if (state->active || mirage_active() || *G_BATTLE_FLAGS != 0u) {
        set_result(CBR_RESULT_BUSY);
        return CBR_RESULT_BUSY;
    }
    count = FN_PARTY_COUNT();
    if (count > CBR_TEAM_SIZE)
        count = CBR_TEAM_SIZE;
    for (index = 0u; index < count; ++index) {
        u16 species = (u16)FN_GET_MON_DATA(&G_PLAYER_PARTY[index],
                                           CBR_MON_DATA_SPECIES, NULL);
        u16 hp = (u16)FN_GET_MON_DATA(&G_PLAYER_PARTY[index],
                                      CBR_MON_DATA_HP, NULL);
        u8 egg = (u8)FN_GET_MON_DATA(&G_PLAYER_PARTY[index],
                                     CBR_MON_DATA_IS_EGG, NULL);
        state->player_preview_species[index] = species;
        if (species != 0u && hp != 0u && egg == 0u)
            ++battle_capable;
    }
    if (battle_capable < CBR_SELECTION_SIZE) {
        set_result(CBR_RESULT_NOT_READY);
        return CBR_RESULT_NOT_READY;
    }
    state->player_count_before = *G_PLAYER_COUNT;
    state->enemy_count_before = *G_ENEMY_COUNT;
    state->battle_flags_before = *G_BATTLE_FLAGS;
    state->rng_before = *G_GLOBAL_RNG;
    state->facility_vars_before[0] = FN_VAR_GET(CBR_VAR_FACILITY_NUMBER);
    state->facility_vars_before[1] = FN_VAR_GET(CBR_VAR_PARTY_SIZE);
    state->facility_vars_before[2] = FN_VAR_GET(CBR_VAR_LEVEL);
    state->facility_vars_before[3] = FN_VAR_GET(CBR_VAR_BATTLE_TYPE);
    state->facility_vars_before[4] = FN_VAR_GET(CBR_VAR_TIER);
    state->facility_flag_before = FN_FLAG_GET(CBR_FLAG_BATTLE_FACILITY);
    copy_bytes(state->player_party_backup, G_PLAYER_PARTY,
               CBR_TEAM_SIZE * CBR_MON_SIZE);
    for (index = 0u; index < CBR_TEAM_SIZE; ++index) {
        state->selected_order_before[index] = G_SELECTED[index];
        G_SELECTED[index] = 0u;
    }
    state->party_hash_before = fnv32(state->player_party_backup,
                                     CBR_TEAM_SIZE * CBR_MON_SIZE);
    state->save_hash_before = current_save_hash();
    state->disable_bag_flag_before = FN_FLAG_GET(CBR_FLAG_DISABLE_BAG);
    state->trainer_flag_before = FN_FLAG_GET(CBR_FLAG_CODEX_TRAINER);
    {
        const volatile u8 *save1 = *G_SAVE_BLOCK1_PTR;
        const volatile u8 *save2 = *G_SAVE_BLOCK2_PTR;
        if (save1 == NULL || save2 == NULL) {
            state->money_before = 0u;
            clear_bytes(state->save1_dex_seen_before,
                        CBR_SAVE_BLOCK1_DEX_SEEN_SIZE);
            clear_bytes(state->game_stats_before,
                        CBR_GAME_STATS_COUNT * 4u);
            clear_bytes(state->save2_pokedex_before,
                        CBR_SAVE_BLOCK2_POKEDEX_SIZE);
        } else {
            u32 key = read32(
                save2 + CBR_SAVE_BLOCK2_ENCRYPTION_KEY_OFFSET);
            state->money_before = read32(
                save1 + CBR_SAVE_BLOCK1_MONEY_OFFSET) ^ key;
            copy_bytes(state->save1_dex_seen_before,
                       save1 + CBR_SAVE_BLOCK1_DEX_SEEN_OFFSET,
                       CBR_SAVE_BLOCK1_DEX_SEEN_SIZE);
            for (index = 0u; index < CBR_GAME_STATS_COUNT; ++index) {
                state->game_stats_before[index] = read32(
                    save1 + CBR_SAVE_BLOCK1_GAME_STATS_OFFSET
                    + (u32)index * 4u) ^ key;
            }
            copy_bytes(state->save2_pokedex_before,
                       save2 + CBR_SAVE_BLOCK2_POKEDEX_OFFSET,
                       CBR_SAVE_BLOCK2_POKEDEX_SIZE);
        }
    }
    state->public_flags = 0u;
    state->revealed_player_mask = 0u;
    state->switch_context = CBR_SWITCH_NONE;
    state->public_event_active_mask = 0u;
    state->private_player_committed = 0u;
    state->player_choice_observed = 0u;
    state->private_seal_crc32 = 0u;
    state->private_seal_length = 0u;
    state->mechanic_used_mask = 0u;
    state->field_completion_pending = 1u;
    state->active = 1u;
    state->phase = CODEX_RUNTIME_PHASE_AWAITING_PLAYER_SELECTION;
    state->status = CBR_STATUS_WAITING;
    (void)FN_VAR_SET(CBR_VAR_FACILITY_NUMBER, 0u);
    (void)FN_VAR_SET(CBR_VAR_PARTY_SIZE, CBR_SELECTION_SIZE);
    (void)FN_VAR_SET(CBR_VAR_LEVEL, state->level_mode == 0u ? 50u : 100u);
    (void)FN_VAR_SET(CBR_VAR_BATTLE_TYPE, 4u);
    /* Party selection must not inherit CFRU facility bans.  The only
     * selectable battle option is the Lv.50 copy toggle; all team-building
     * restrictions are agreements between the two players, not ROM rules. */
    (void)FN_VAR_SET(CBR_VAR_TIER, CBR_TIER_NO_RESTRICTIONS);
    (void)FN_FLAG_CLEAR(CBR_FLAG_BATTLE_FACILITY);
    publish_snapshot(CBR_STATUS_WAITING);
    set_result(CBR_RESULT_OK);
    return CBR_RESULT_OK;
}

CBR_EXPORT(CodexBattleRuntime_FieldCommitPlayerSelection)
u16 CodexBattleRuntime_FieldCommitPlayerSelection(void)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    u8 used = 0u;
    u8 index;
    if (!runtime_active()
        || state->phase != CODEX_RUNTIME_PHASE_AWAITING_PLAYER_SELECTION) {
        set_result(CBR_RESULT_INVALID);
        return CBR_RESULT_INVALID;
    }
    for (index = 0u; index < CBR_SELECTION_SIZE; ++index) {
        u8 slot = G_SELECTED[index];
        Pokemon100 *source;
        if (slot < 1u || slot > state->player_count_before
            || (used & (1u << (slot - 1u)))) {
            restore_player_party(CBR_CLEANUP_ABORT);
            set_result(CBR_RESULT_INVALID);
            return CBR_RESULT_INVALID;
        }
        source = (Pokemon100 *)(void *)(state->player_party_backup
                                       + (u32)(slot - 1u) * CBR_MON_SIZE);
        if (FN_GET_MON_DATA(source, CBR_MON_DATA_SPECIES, NULL) == 0u
            || FN_GET_MON_DATA(source, CBR_MON_DATA_HP, NULL) == 0u
            || FN_GET_MON_DATA(source, CBR_MON_DATA_IS_EGG, NULL) != 0u) {
            restore_player_party(CBR_CLEANUP_ABORT);
            set_result(CBR_RESULT_INVALID);
            return CBR_RESULT_INVALID;
        }
        used |= (u8)(1u << (slot - 1u));
        state->player_selected[index] = slot;
    }
    clear_bytes(G_PLAYER_PARTY, CBR_TEAM_SIZE * CBR_MON_SIZE);
    for (index = 0u; index < CBR_SELECTION_SIZE; ++index) {
        u8 slot = state->player_selected[index];
        Pokemon100 *destination = &G_PLAYER_PARTY[index];
        Pokemon100 *source = (Pokemon100 *)(void *)(
            state->player_party_backup + (u32)(slot - 1u) * CBR_MON_SIZE);
        copy_bytes(destination, source, sizeof(Pokemon100));
        if (state->level_mode == 0u) {
            u16 species = (u16)FN_GET_MON_DATA(
                destination, CBR_MON_DATA_SPECIES, NULL);
            u8 growth;
            u32 experience;
            if (species == 0u || species > CODEX_RUNTIME_SPECIES_MAX) {
                restore_player_party(CBR_CLEANUP_ABORT);
                set_result(CBR_RESULT_INVALID);
                return CBR_RESULT_INVALID;
            }
            growth = G_BASE_STATS[
                (u32)species * CODEX_RUNTIME_BASE_STATS_STRIDE
                + CODEX_RUNTIME_BASE_STATS_GROWTH_OFFSET];
            if (growth >= CODEX_RUNTIME_EXPERIENCE_GROWTH_COUNT) {
                restore_player_party(CBR_CLEANUP_ABORT);
                set_result(CBR_RESULT_INVALID);
                return CBR_RESULT_INVALID;
            }
            experience = G_EXPERIENCE_TABLES[
                (u32)growth * CODEX_RUNTIME_EXPERIENCE_TABLE_LEVELS + 50u];
            FN_SET_MON_DATA(destination, CBR_MON_DATA_EXP, &experience);
            FN_CALCULATE_STATS(destination);
            if (FN_GET_MON_DATA(destination, CBR_MON_DATA_LEVEL, NULL)
                != 50u) {
                restore_player_party(CBR_CLEANUP_ABORT);
                set_result(CBR_RESULT_INVALID);
                return CBR_RESULT_INVALID;
            }
            write16(destination->bytes + CBR_HP_OFFSET,
                    read16(destination->bytes + CBR_MAX_HP_OFFSET));
        }
    }
    *G_PLAYER_COUNT = CBR_SELECTION_SIZE;
    /* Selection order is an input to this commit only.  Codex Battle owns
     * the compacted temporary party until cleanup; no Factory/Tower setup may
     * reinterpret it a second time. */
    clear_bytes(G_SELECTED, CBR_TEAM_SIZE);
    (void)FN_VAR_SET(CBR_VAR_FACILITY_NUMBER, state->facility_vars_before[0]);
    (void)FN_VAR_SET(CBR_VAR_PARTY_SIZE, state->facility_vars_before[1]);
    (void)FN_VAR_SET(CBR_VAR_LEVEL, state->facility_vars_before[2]);
    (void)FN_VAR_SET(CBR_VAR_BATTLE_TYPE, state->facility_vars_before[3]);
    (void)FN_VAR_SET(CBR_VAR_TIER, state->facility_vars_before[4]);
    state->player_selection_valid = 1u;
    state->phase = CODEX_RUNTIME_PHASE_BATTLE_RESOLVING;
    state->status = CBR_STATUS_ACTIVE;
    state->turn = 1u;
    state->legal_move_mask = 0x0Fu;
    state->legal_switch_mask = 0x06u;
    for (index = 0u; index < 4u; ++index)
        state->legal_gimmicks[index] = 1u;
    publish_snapshot(CBR_STATUS_ACTIVE);
    set_result(CBR_RESULT_OK);
    return CBR_RESULT_OK;
}

CBR_EXPORT(CodexBattleRuntime_FieldPrepareBattle)
u16 CodexBattleRuntime_FieldPrepareBattle(void)
{
    if (!runtime_active() || !gCodexBattleRuntimeState->player_selection_valid
        || !gCodexBattleRuntimeState->codex_selection_valid) {
        restore_player_party(CBR_CLEANUP_ABORT);
        set_result(CBR_RESULT_INVALID);
        return CBR_RESULT_INVALID;
    }
    /* trainerbattle owns its pre-battle flag initialization.  Dynamax, bag
     * and EXP suppression are asserted by install_controller only after the
     * stock scheduler has created both battlers and gBattleStruct. */
    clear_bytes(G_ENEMY_PARTY, CBR_TEAM_SIZE * CBR_MON_SIZE);
    *G_ENEMY_COUNT = 0u;
    (void)FN_FLAG_CLEAR(CBR_FLAG_BATTLE_FACILITY);
    *G_BATTLE_OUTCOME = 0u;
    set_result(CBR_RESULT_OK);
    return CBR_RESULT_OK;
}

CBR_EXPORT(CodexBattleRuntime_AfterBattle)
u16 CodexBattleRuntime_AfterBattle(void)
{
    u16 requested = gCodexBattleRuntimeState->cleanup_reason;
    u16 reason = (requested == CBR_CLEANUP_ABORT
                  || requested == CBR_CLEANUP_FORFEIT)
        ? requested : ((*G_BATTLE_OUTCOME & 0x7Fu) == 1u
                        ? CBR_CLEANUP_WIN : CBR_CLEANUP_LOSS);
    restore_player_party(reason);
    set_result(CBR_RESULT_OK);
    return CBR_RESULT_OK;
}

CBR_EXPORT(CodexBattleRuntime_FieldFinish)
u16 CodexBattleRuntime_FieldFinish(void)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    if (!state_valid() || state->active
        || state->field_completion_pending == 0u) {
        set_result(CBR_RESULT_INVALID);
        return CBR_RESULT_INVALID;
    }
    /* This call sits after the terminal result/error msgbox and immediately
     * before release/end.  Only now can configure replace the match state
     * without a delayed callback from the older field script. */
    state->field_completion_pending = 0u;
    state->phase = CODEX_RUNTIME_PHASE_IDLE;
    state->status = CBR_STATUS_READY;
    publish_snapshot(CBR_STATUS_READY);
    set_result(CBR_RESULT_OK);
    return CBR_RESULT_OK;
}

CBR_EXPORT(CodexBattleRuntime_SealPrivateForTest)
u32 CodexBattleRuntime_SealPrivateForTest(const volatile u8 *bytes, u16 size)
{
    if (size > 512u)
        return 0u;
    gCodexBattleRuntimeState->private_player_committed = 1u;
    gCodexBattleRuntimeState->private_seal_crc32 = crc32_volatile(bytes, size);
    gCodexBattleRuntimeState->private_seal_length = size;
    return gCodexBattleRuntimeState->private_seal_crc32;
}

CBR_EXPORT(CodexBattleRuntime_TestInitialize)
u32 CodexBattleRuntime_TestInitialize(u32 nonce)
{
    if (runtime_active())
        restore_player_party(CBR_CLEANUP_RESET);
    initialize_state(nonce == 0u ? 0x12345678u : nonce);
    if (!state_valid())
        return 0u;
    *G_BASE_NONCE = gCodexBattleRuntimeState->session_nonce;
    CodexBattleRuntime_Initialize();
    return gCodexBattleRuntimeState->session_nonce;
}

CBR_EXPORT(CodexBattleRuntime_TestStateHash)
u32 CodexBattleRuntime_TestStateHash(void)
{
    return fnv32(gCodexBattleRuntimeState, CODEX_RUNTIME_STATE_SIZE);
}

CBR_EXPORT(CodexBattleRuntime_Probe)
u32 CodexBattleRuntime_Probe(u32 selector)
{
    switch (selector) {
    case 0u: return CBR_STATE_MAGIC;
    case 1u: return CODEX_RUNTIME_MAILBOX_ADDRESS;
    case 2u: return CODEX_RUNTIME_MAILBOX_SIZE;
    case 3u: return CODEX_RUNTIME_STATE_ADDRESS;
    case 4u: return CODEX_RUNTIME_STATE_SIZE;
    case 5u: return gCodexBattleRuntimeState->phase;
    case 6u: return gCodexBattleRuntimeState->match_id;
    case 7u: return gCodexBattleRuntimeState->turn;
    case 8u: return gCodexBattleRuntimeState->last_request_sequence;
    case 9u: return gCodexBattleRuntimeState->party_hash_before;
    case 10u: return gCodexBattleRuntimeState->cleanup_reason;
    default: return 0u;
    }
}
