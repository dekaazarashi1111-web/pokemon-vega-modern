/*
 * Final Trainer ChangeKit runtime.
 *
 * This is a consumer-scoped successor to trainer_v5_stage32_runtime.  It does
 * not replace global FlagGet/Set/Clear. Every generated trainer owns a CFRU
 * AI policy; mechanic mode STANDARD explicitly denies un-authored gimmicks.
 */

#include <stddef.h>
#include <stdint.h>

#include "trainer_changekit_final_runtime.h"

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;

#define PTR(type, address) ((type)(uintptr_t)(address))
#define TRAINER_CHANGEKIT_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))

enum {
    TRAINER_CHANGEKIT_FLAG_START = 0x0500,
    TRAINER_CHANGEKIT_OPPONENT_SIDE = 1,
    TRAINER_CHANGEKIT_MAX_PARTY_SIZE = 6,
    TRAINER_CHANGEKIT_MON_SIZE = 100,
    TRAINER_CHANGEKIT_BATTLE_MON_SIZE = 88,
    TRAINER_CHANGEKIT_BATTLE_MON_ABILITY_OFFSET = 0x38,
    TRAINER_CHANGEKIT_NATURE_MINT_OFFSET = 0x0F,
    TRAINER_CHANGEKIT_TERA_TYPE_OFFSET = 0x11,
    TRAINER_CHANGEKIT_BACKUP_SPECIES_OFFSET = 0x1C,
    TRAINER_CHANGEKIT_SPECIES_OFFSET = 0x20,
    TRAINER_CHANGEKIT_EV_HP_OFFSET = 0x38,
    TRAINER_CHANGEKIT_EV_ATK_OFFSET = 0x39,
    TRAINER_CHANGEKIT_EV_DEF_OFFSET = 0x3A,
    TRAINER_CHANGEKIT_EV_SPEED_OFFSET = 0x3B,
    TRAINER_CHANGEKIT_EV_SPATK_OFFSET = 0x3C,
    TRAINER_CHANGEKIT_EV_SPDEF_OFFSET = 0x3D,
    TRAINER_CHANGEKIT_MET_BITS_OFFSET = 0x46,
    TRAINER_CHANGEKIT_IV_BITS_OFFSET = 0x48,
    TRAINER_CHANGEKIT_LEVEL_OFFSET = 0x54,
    TRAINER_CHANGEKIT_HP_OFFSET = 0x56,
    TRAINER_CHANGEKIT_MAX_HP_OFFSET = 0x58,
    TRAINER_CHANGEKIT_HIDDEN_ABILITY_MASK = 0x1000,
    TRAINER_CHANGEKIT_IV_FIELD_MASK = 0x3FFFFFFF,
    TRAINER_CHANGEKIT_ABILITY_NUM_MASK = 0x80000000u,
    TRAINER_CHANGEKIT_ABILITY_SECONDARY = 1,
    TRAINER_CHANGEKIT_ABILITY_HIDDEN = 2,
    TRAINER_CHANGEKIT_BATTLE_TYPE_TRAINER = 0x00000008u,
    TRAINER_CHANGEKIT_RUNTIME_MAGIC = 0x54434631u /* TCF1 */
};

typedef u8 (*FlagFn)(u16 flag);
typedef u16 (*GetTrainerFlagFn)(void);
typedef u16 (*GetRematchFn)(u16 trainer_id);
typedef void (*BuildTrainerPartyFn)(void);
typedef void (*CalculateMonStatsFn)(void *mon);
typedef const u8 *(*ConfigureTrainerBattleFn)(const u8 *data);
typedef u8 (*ConfigurePolicyFn)(u8 ai_profile, u8 mechanic_mode);
typedef void (*PendingClearFn)(void);
typedef u8 (*PolicyCanFn)(u8 battler, u8 upstream_allowed);
typedef u8 (*PolicyMarkFn)(u8 battler);
typedef u8 (*PolicyLifetimeFn)(void);
typedef u8 (*LoadGameDataFn)(u8 save_type);
typedef void (*LoadProperAbilityBattleDataFn)(void);

#ifdef TRAINER_CHANGEKIT_FINAL_HOST_TEST
extern u16 TrainerChangeKitHost_GetTrainerFlag(void);
extern u8 TrainerChangeKitHost_FlagSet(u16 flag);
extern u8 TrainerChangeKitHost_FlagClear(u16 flag);
extern u8 TrainerChangeKitHost_FlagGet(u16 flag);
extern u16 TrainerChangeKitHost_GetRematch(u16 trainer_id);
extern void TrainerChangeKitHost_BuildTrainerParty(void);
extern void TrainerChangeKitHost_CalculateMonStats(void *mon);
extern const u8 *TrainerChangeKitHost_ConfigureTrainerBattle(const u8 *data);
extern u8 TrainerChangeKitHost_ConfigurePolicy(u8 ai_profile, u8 mechanic_mode);
extern void TrainerChangeKitHost_PendingClear(void);
extern u8 TrainerChangeKitHost_PolicyCanMega(u8 battler, u8 allowed);
extern u8 TrainerChangeKitHost_PolicyMarkMega(u8 battler);
extern u8 TrainerChangeKitHost_PolicyCanZ(u8 battler, u8 allowed);
extern u8 TrainerChangeKitHost_PolicyMarkZ(u8 battler);
extern u8 TrainerChangeKitHost_PolicyCanDynamax(u8 battler, u8 allowed);
extern u8 TrainerChangeKitHost_PolicyMarkDynamax(u8 battler);
extern u8 TrainerChangeKitHost_PolicyCanTera(u8 battler, u8 allowed);
extern u8 TrainerChangeKitHost_PolicyMarkTera(u8 battler);
extern u8 TrainerChangeKitHost_PolicyBegin(void);
extern u8 TrainerChangeKitHost_PolicyEnd(void);
extern u8 TrainerChangeKitHost_SaveLoadGameData(u8 save_type);
extern void TrainerChangeKitHost_LoadProperAbilityBattleData(void);
extern u32 TrainerChangeKitHost_CommandAddress(const u8 *data);
extern u8 gTrainerChangeKitHostEnemyParty[600];
extern volatile u16 gTrainerChangeKitHostOpponentA;
extern volatile u32 gTrainerChangeKitHostBattleTypeFlags;
extern volatile u8 gTrainerChangeKitHostBattlersCount;
extern volatile u8 gTrainerChangeKitHostAbsentBattlerFlags;
extern volatile u16 gTrainerChangeKitHostBattlerPartyIndexes[4];
extern volatile u8 gTrainerChangeKitHostActiveBattler;
extern u8 gTrainerChangeKitHostBattleMons[352];

#define FN_GET_TRAINER_FLAG TrainerChangeKitHost_GetTrainerFlag
#define FN_FLAG_SET TrainerChangeKitHost_FlagSet
#define FN_FLAG_CLEAR TrainerChangeKitHost_FlagClear
#define FN_FLAG_GET TrainerChangeKitHost_FlagGet
#define FN_GET_REMATCH TrainerChangeKitHost_GetRematch
#define FN_BUILD_TRAINER_PARTY TrainerChangeKitHost_BuildTrainerParty
#define FN_CALCULATE_MON_STATS TrainerChangeKitHost_CalculateMonStats
#define FN_CONFIGURE_TRAINER_BATTLE TrainerChangeKitHost_ConfigureTrainerBattle
#define FN_CONFIGURE_POLICY TrainerChangeKitHost_ConfigurePolicy
#define FN_PENDING_CLEAR TrainerChangeKitHost_PendingClear
#define FN_POLICY_CAN_MEGA TrainerChangeKitHost_PolicyCanMega
#define FN_POLICY_MARK_MEGA TrainerChangeKitHost_PolicyMarkMega
#define FN_POLICY_CAN_Z TrainerChangeKitHost_PolicyCanZ
#define FN_POLICY_MARK_Z TrainerChangeKitHost_PolicyMarkZ
#define FN_POLICY_CAN_DYNAMAX TrainerChangeKitHost_PolicyCanDynamax
#define FN_POLICY_MARK_DYNAMAX TrainerChangeKitHost_PolicyMarkDynamax
#define FN_POLICY_CAN_TERA TrainerChangeKitHost_PolicyCanTera
#define FN_POLICY_MARK_TERA TrainerChangeKitHost_PolicyMarkTera
#define FN_POLICY_BEGIN TrainerChangeKitHost_PolicyBegin
#define FN_POLICY_END TrainerChangeKitHost_PolicyEnd
#define FN_SAVE_LOAD_GAME_DATA TrainerChangeKitHost_SaveLoadGameData
#define FN_LOAD_PROPER_ABILITY_BATTLE_DATA \
    TrainerChangeKitHost_LoadProperAbilityBattleData
#define G_ENEMY_PARTY gTrainerChangeKitHostEnemyParty
#define G_TRAINER_OPPONENT_A gTrainerChangeKitHostOpponentA
#define G_BATTLE_TYPE_FLAGS gTrainerChangeKitHostBattleTypeFlags
#define G_BATTLERS_COUNT gTrainerChangeKitHostBattlersCount
#define G_ABSENT_BATTLER_FLAGS gTrainerChangeKitHostAbsentBattlerFlags
#define G_BATTLER_PARTY_INDEXES gTrainerChangeKitHostBattlerPartyIndexes
#define G_ACTIVE_BATTLER gTrainerChangeKitHostActiveBattler
#define G_BATTLE_MONS gTrainerChangeKitHostBattleMons
#define COMMAND_ADDRESS(data) TrainerChangeKitHost_CommandAddress(data)
#else
#ifndef VEGA_GET_TRAINER_FLAG_ADDRESS
#error "VEGA_GET_TRAINER_FLAG_ADDRESS is required"
#endif
#ifndef VEGA_FLAG_SET_ADDRESS
#error "VEGA_FLAG_SET_ADDRESS is required"
#endif
#ifndef VEGA_FLAG_CLEAR_ADDRESS
#error "VEGA_FLAG_CLEAR_ADDRESS is required"
#endif
#ifndef VEGA_FLAG_GET_ADDRESS
#error "VEGA_FLAG_GET_ADDRESS is required"
#endif
#ifndef VEGA_GET_REMATCH_TRAMPOLINE_ADDRESS
#error "VEGA_GET_REMATCH_TRAMPOLINE_ADDRESS is required"
#endif
#ifndef VEGA_BUILD_TRAINER_PARTY_TRAMPOLINE_ADDRESS
#error "VEGA_BUILD_TRAINER_PARTY_TRAMPOLINE_ADDRESS is required"
#endif
#ifndef VEGA_CONFIGURE_TRAINER_BATTLE_ADDRESS
#error "VEGA_CONFIGURE_TRAINER_BATTLE_ADDRESS is required"
#endif
#ifndef VEGA_CALCULATE_MON_STATS_ADDRESS
#error "VEGA_CALCULATE_MON_STATS_ADDRESS is required"
#endif
#ifndef VEGA_ENEMY_PARTY_ADDRESS
#error "VEGA_ENEMY_PARTY_ADDRESS is required"
#endif
#ifndef VEGA_TRAINER_OPPONENT_A_ADDRESS
#error "VEGA_TRAINER_OPPONENT_A_ADDRESS is required"
#endif
#ifndef VEGA_BATTLE_TYPE_FLAGS_ADDRESS
#error "VEGA_BATTLE_TYPE_FLAGS_ADDRESS is required"
#endif
#ifndef VEGA_CONFIGURE_NEXT_BATTLE_POLICY_ADDRESS
#error "VEGA_CONFIGURE_NEXT_BATTLE_POLICY_ADDRESS is required"
#endif
#ifndef VEGA_CFRU_PENDING_CLEAR_ADDRESS
#error "VEGA_CFRU_PENDING_CLEAR_ADDRESS is required"
#endif
#ifndef VEGA_BATTLE_POLICY_CAN_MEGA_ADDRESS
#error "VEGA_BATTLE_POLICY_CAN_MEGA_ADDRESS is required"
#endif
#ifndef VEGA_BATTLE_POLICY_MARK_MEGA_ADDRESS
#error "VEGA_BATTLE_POLICY_MARK_MEGA_ADDRESS is required"
#endif
#ifndef VEGA_BATTLE_POLICY_CAN_Z_ADDRESS
#error "VEGA_BATTLE_POLICY_CAN_Z_ADDRESS is required"
#endif
#ifndef VEGA_BATTLE_POLICY_MARK_Z_ADDRESS
#error "VEGA_BATTLE_POLICY_MARK_Z_ADDRESS is required"
#endif
#ifndef VEGA_BATTLE_POLICY_CAN_DYNAMAX_ADDRESS
#error "VEGA_BATTLE_POLICY_CAN_DYNAMAX_ADDRESS is required"
#endif
#ifndef VEGA_BATTLE_POLICY_MARK_DYNAMAX_ADDRESS
#error "VEGA_BATTLE_POLICY_MARK_DYNAMAX_ADDRESS is required"
#endif
#ifndef VEGA_BATTLE_POLICY_CAN_TERA_ADDRESS
#error "VEGA_BATTLE_POLICY_CAN_TERA_ADDRESS is required"
#endif
#ifndef VEGA_BATTLE_POLICY_MARK_TERA_ADDRESS
#error "VEGA_BATTLE_POLICY_MARK_TERA_ADDRESS is required"
#endif
#ifndef VEGA_BATTLE_POLICY_BEGIN_ADDRESS
#error "VEGA_BATTLE_POLICY_BEGIN_ADDRESS is required"
#endif
#ifndef VEGA_BATTLE_POLICY_END_ADDRESS
#error "VEGA_BATTLE_POLICY_END_ADDRESS is required"
#endif
#ifndef VEGA_SAVE_LOAD_GAME_DATA_TRAMPOLINE_ADDRESS
#error "VEGA_SAVE_LOAD_GAME_DATA_TRAMPOLINE_ADDRESS is required"
#endif
#ifndef VEGA_BATTLERS_COUNT_ADDRESS
#error "VEGA_BATTLERS_COUNT_ADDRESS is required"
#endif
#ifndef VEGA_BATTLER_PARTY_INDEXES_ADDRESS
#error "VEGA_BATTLER_PARTY_INDEXES_ADDRESS is required"
#endif
#ifndef VEGA_ABSENT_BATTLER_FLAGS_ADDRESS
#error "VEGA_ABSENT_BATTLER_FLAGS_ADDRESS is required"
#endif
#ifndef VEGA_ACTIVE_BATTLER_ADDRESS
#error "VEGA_ACTIVE_BATTLER_ADDRESS is required"
#endif
#ifndef VEGA_BATTLE_MONS_ADDRESS
#error "VEGA_BATTLE_MONS_ADDRESS is required"
#endif
#ifndef VEGA_LOAD_PROPER_ABILITY_BATTLE_DATA_ADDRESS
#error "VEGA_LOAD_PROPER_ABILITY_BATTLE_DATA_ADDRESS is required"
#endif
#ifndef VEGA_TRAINER_CHANGEKIT_STATE_ADDRESS
#error "VEGA_TRAINER_CHANGEKIT_STATE_ADDRESS is required"
#endif

#define FN_GET_TRAINER_FLAG \
    PTR(GetTrainerFlagFn, VEGA_GET_TRAINER_FLAG_ADDRESS)
#define FN_FLAG_SET PTR(FlagFn, VEGA_FLAG_SET_ADDRESS)
#define FN_FLAG_CLEAR PTR(FlagFn, VEGA_FLAG_CLEAR_ADDRESS)
#define FN_FLAG_GET PTR(FlagFn, VEGA_FLAG_GET_ADDRESS)
#define FN_GET_REMATCH PTR(GetRematchFn, VEGA_GET_REMATCH_TRAMPOLINE_ADDRESS)
#define FN_BUILD_TRAINER_PARTY \
    PTR(BuildTrainerPartyFn, VEGA_BUILD_TRAINER_PARTY_TRAMPOLINE_ADDRESS)
#define FN_CALCULATE_MON_STATS \
    PTR(CalculateMonStatsFn, VEGA_CALCULATE_MON_STATS_ADDRESS)
#define FN_CONFIGURE_TRAINER_BATTLE \
    PTR(ConfigureTrainerBattleFn, VEGA_CONFIGURE_TRAINER_BATTLE_ADDRESS)
#define FN_CONFIGURE_POLICY \
    PTR(ConfigurePolicyFn, VEGA_CONFIGURE_NEXT_BATTLE_POLICY_ADDRESS)
#define FN_PENDING_CLEAR \
    PTR(PendingClearFn, VEGA_CFRU_PENDING_CLEAR_ADDRESS)
#define FN_POLICY_CAN_MEGA \
    PTR(PolicyCanFn, VEGA_BATTLE_POLICY_CAN_MEGA_ADDRESS)
#define FN_POLICY_MARK_MEGA \
    PTR(PolicyMarkFn, VEGA_BATTLE_POLICY_MARK_MEGA_ADDRESS)
#define FN_POLICY_CAN_Z \
    PTR(PolicyCanFn, VEGA_BATTLE_POLICY_CAN_Z_ADDRESS)
#define FN_POLICY_MARK_Z \
    PTR(PolicyMarkFn, VEGA_BATTLE_POLICY_MARK_Z_ADDRESS)
#define FN_POLICY_CAN_DYNAMAX \
    PTR(PolicyCanFn, VEGA_BATTLE_POLICY_CAN_DYNAMAX_ADDRESS)
#define FN_POLICY_MARK_DYNAMAX \
    PTR(PolicyMarkFn, VEGA_BATTLE_POLICY_MARK_DYNAMAX_ADDRESS)
#define FN_POLICY_CAN_TERA \
    PTR(PolicyCanFn, VEGA_BATTLE_POLICY_CAN_TERA_ADDRESS)
#define FN_POLICY_MARK_TERA \
    PTR(PolicyMarkFn, VEGA_BATTLE_POLICY_MARK_TERA_ADDRESS)
#define FN_POLICY_BEGIN \
    PTR(PolicyLifetimeFn, VEGA_BATTLE_POLICY_BEGIN_ADDRESS)
#define FN_POLICY_END \
    PTR(PolicyLifetimeFn, VEGA_BATTLE_POLICY_END_ADDRESS)
#define FN_SAVE_LOAD_GAME_DATA \
    PTR(LoadGameDataFn, VEGA_SAVE_LOAD_GAME_DATA_TRAMPOLINE_ADDRESS)
#define FN_LOAD_PROPER_ABILITY_BATTLE_DATA \
    PTR(LoadProperAbilityBattleDataFn, \
        VEGA_LOAD_PROPER_ABILITY_BATTLE_DATA_ADDRESS)
#define G_ENEMY_PARTY PTR(u8 *, VEGA_ENEMY_PARTY_ADDRESS)
#define G_TRAINER_OPPONENT_A \
    (*PTR(volatile u16 *, VEGA_TRAINER_OPPONENT_A_ADDRESS))
#define G_BATTLE_TYPE_FLAGS \
    (*PTR(volatile u32 *, VEGA_BATTLE_TYPE_FLAGS_ADDRESS))
#define G_BATTLERS_COUNT \
    (*PTR(volatile u8 *, VEGA_BATTLERS_COUNT_ADDRESS))
#define G_ABSENT_BATTLER_FLAGS \
    (*PTR(volatile u8 *, VEGA_ABSENT_BATTLER_FLAGS_ADDRESS))
#define G_BATTLER_PARTY_INDEXES \
    PTR(volatile u16 *, VEGA_BATTLER_PARTY_INDEXES_ADDRESS)
#define G_ACTIVE_BATTLER \
    (*PTR(volatile u8 *, VEGA_ACTIVE_BATTLER_ADDRESS))
#define G_BATTLE_MONS PTR(u8 *, VEGA_BATTLE_MONS_ADDRESS)
#define COMMAND_ADDRESS(data) ((u32)(uintptr_t)(data))
#endif

_Static_assert(sizeof(struct TrainerChangeKitMemberSidecarV1) == 18u,
               "Trainer ChangeKit sidecar ABI must remain 18 bytes");
_Static_assert(sizeof(struct TrainerChangeKitExactBindingV1) == 12u,
               "Trainer ChangeKit exact binding ABI must remain 12 bytes");
_Static_assert(sizeof(struct TrainerChangeKitRematchV2) == 8u,
               "Trainer ChangeKit rematch ABI must remain 8 bytes");
_Static_assert(sizeof(struct TrainerChangeKitArchiveBindingV1) == 16u,
               "Trainer ChangeKit archive ABI must remain 16 bytes");
_Static_assert(sizeof(struct TrainerChangeKitGimmickV1) == 12u,
               "Trainer ChangeKit gimmick ABI must remain 12 bytes");
_Static_assert(sizeof(struct TrainerChangeKitFlagMapV1) == 4u,
               "Trainer ChangeKit flag map ABI must remain 4 bytes");
_Static_assert(TRAINER_CHANGEKIT_FINAL_GENERATED_ENCOUNTER_COUNT == 1302u,
               "final Trainer ChangeKit scope must remain 1302 catalog rows");
_Static_assert(TRAINER_CHANGEKIT_FINAL_GENERATED_TRAINER_TABLE_COUNT >= 4284u,
               "trainer table must cover the highest allocated ID 4283");

struct TrainerChangeKitRuntimeState {
    u16 trainer_id;
    u16 dispatch_id;
    u16 physical_flag;
    u8 mechanic_mode;
    u8 ai_profile;
    u8 user_slot;
    u8 phase;
    u8 activation_used;
    u8 transient_active;
    u8 user_present;
    u8 user_seen;
};

#ifdef TRAINER_CHANGEKIT_FINAL_HOST_TEST
static struct TrainerChangeKitRuntimeState sRuntimeState;
static const struct TrainerChangeKitGimmickV1 *sCurrentGimmick;
static u16 sArchiveSelection;
static u32 sCommandDataAddress;
static u16 sCommandSource;
static u16 sCommandDispatch;
static u8 sCommandKind;
static u8 sPartySetupPending;
static u16 sPartySetupTrainerId;
static u32 sAmbiguousBindings;
static u32 sPolicyFailures;

static void ensure_runtime_storage(void)
{
}
#else
enum {
    TRAINER_CHANGEKIT_STORAGE_MAGIC = 0x54434653u, /* TCFS */
    TRAINER_CHANGEKIT_STORAGE_SIZE = 48u
};

struct __attribute__((packed)) TrainerChangeKitRuntimeStorage {
    u32 magic;
    u32 magic_inverse;
    struct TrainerChangeKitRuntimeState runtime_state;
    u16 archive_selection;
    u32 command_data_address;
    u16 command_source;
    u16 command_dispatch;
    u8 command_kind;
    u8 party_setup_pending;
    u16 party_setup_trainer_id;
    const struct TrainerChangeKitGimmickV1 *current_gimmick;
    u32 ambiguous_bindings;
    u32 policy_failures;
};

_Static_assert(sizeof(struct TrainerChangeKitRuntimeState) == 14u,
               "Trainer ChangeKit runtime state ABI changed");
_Static_assert(sizeof(struct TrainerChangeKitRuntimeStorage)
                   == TRAINER_CHANGEKIT_STORAGE_SIZE,
               "Trainer ChangeKit EWRAM storage ABI changed");

#define TRAINER_CHANGEKIT_STORAGE \
    PTR(volatile struct TrainerChangeKitRuntimeStorage *, \
        VEGA_TRAINER_CHANGEKIT_STATE_ADDRESS)
#define sRuntimeState (TRAINER_CHANGEKIT_STORAGE->runtime_state)
#define sCurrentGimmick (TRAINER_CHANGEKIT_STORAGE->current_gimmick)
#define sArchiveSelection (TRAINER_CHANGEKIT_STORAGE->archive_selection)
#define sCommandDataAddress (TRAINER_CHANGEKIT_STORAGE->command_data_address)
#define sCommandSource (TRAINER_CHANGEKIT_STORAGE->command_source)
#define sCommandDispatch (TRAINER_CHANGEKIT_STORAGE->command_dispatch)
#define sCommandKind (TRAINER_CHANGEKIT_STORAGE->command_kind)
#define sPartySetupPending (TRAINER_CHANGEKIT_STORAGE->party_setup_pending)
#define sPartySetupTrainerId \
    (TRAINER_CHANGEKIT_STORAGE->party_setup_trainer_id)
#define sAmbiguousBindings (TRAINER_CHANGEKIT_STORAGE->ambiguous_bindings)
#define sPolicyFailures (TRAINER_CHANGEKIT_STORAGE->policy_failures)

static void ensure_runtime_storage(void)
{
    volatile struct TrainerChangeKitRuntimeStorage *storage =
        TRAINER_CHANGEKIT_STORAGE;
    volatile u8 *raw;
    u32 index;

    if (storage->magic == TRAINER_CHANGEKIT_STORAGE_MAGIC
        && storage->magic_inverse
            == (u32)~(u32)TRAINER_CHANGEKIT_STORAGE_MAGIC)
        return;
    raw = (volatile u8 *)storage;
    for (index = 0u; index < TRAINER_CHANGEKIT_STORAGE_SIZE; ++index)
        raw[index] = 0u;
    storage->magic_inverse = (u32)~(u32)TRAINER_CHANGEKIT_STORAGE_MAGIC;
    storage->magic = TRAINER_CHANGEKIT_STORAGE_MAGIC;
}
#endif

static u16 read_u16(const u8 *source)
{
    return (u16)((u16)source[0] | ((u16)source[1] << 8));
}

static void write_u16(u8 *destination, u16 value)
{
    destination[0] = (u8)value;
    destination[1] = (u8)(value >> 8);
}

static u32 read_u32(const u8 *source)
{
    return (u32)source[0]
        | ((u32)source[1] << 8)
        | ((u32)source[2] << 16)
        | ((u32)source[3] << 24);
}

static void write_u32(u8 *destination, u32 value)
{
    destination[0] = (u8)value;
    destination[1] = (u8)(value >> 8);
    destination[2] = (u8)(value >> 16);
    destination[3] = (u8)(value >> 24);
}

static u8 supported_kind(u8 kind)
{
    return (u8)(kind <= 9u);
}

static u8 double_kind(u8 kind)
{
    return (u8)(kind == 4u || kind == 6u || kind == 7u || kind == 8u);
}

static u8 valid_ai_profile(u8 profile)
{
    return (u8)(profile == 1u || profile == 3u || profile == 5u);
}

static u8 valid_tera_type(u8 type)
{
    return (u8)(type <= 0x08u
        || (type >= 0x0Au && type <= 0x11u)
        || type == 0x17u || type == 0x18u);
}

static void reset_runtime_state(void)
{
    sRuntimeState.trainer_id = 0u;
    sRuntimeState.dispatch_id = 0u;
    sRuntimeState.physical_flag = 0u;
    sRuntimeState.mechanic_mode = TRAINER_CHANGEKIT_MECHANIC_STANDARD;
    sRuntimeState.ai_profile = 0u;
    sRuntimeState.user_slot = 0u;
    sRuntimeState.phase = TRAINER_CHANGEKIT_PHASE_IDLE;
    sRuntimeState.activation_used = 0u;
    sRuntimeState.transient_active = 0u;
    sRuntimeState.user_present = 0u;
    sRuntimeState.user_seen = 0u;
    sCurrentGimmick = NULL;
    sPartySetupPending = 0u;
    sPartySetupTrainerId = 0u;
}

static void clear_command_context(void)
{
    sCommandDataAddress = 0u;
    sCommandSource = 0u;
    sCommandDispatch = 0u;
    sCommandKind = 0u;
}

static void cleanup_stale_owned_policy(void)
{
    ensure_runtime_storage();
    if (sRuntimeState.phase == TRAINER_CHANGEKIT_PHASE_PENDING)
        FN_PENDING_CLEAR();
    else if (sRuntimeState.phase == TRAINER_CHANGEKIT_PHASE_ACTIVE)
        /* Use the public policy lifetime owner so a Tera battle restores the
         * party's backed-up types before CFRU clears its transient state. */
        (void)FN_POLICY_END();
    reset_runtime_state();
}

static u16 map_flag(u16 flag)
{
    size_t low = 0u;
    size_t high = TRAINER_CHANGEKIT_FINAL_GENERATED_FLAG_MAP_COUNT;

    while (low < high) {
        size_t middle = low + ((high - low) >> 1);
        u16 external = gTrainerChangeKitFlagMap[middle].external_flag;
        if (external < flag)
            low = middle + 1u;
        else
            high = middle;
    }
    if (low < TRAINER_CHANGEKIT_FINAL_GENERATED_FLAG_MAP_COUNT
        && gTrainerChangeKitFlagMap[low].external_flag == flag)
        return gTrainerChangeKitFlagMap[low].physical_flag;
    return flag;
}

static const struct TrainerChangeKitArchiveBindingV1 *
find_archive(u16 archive_id)
{
    size_t low = 0u;
    size_t high = TRAINER_CHANGEKIT_FINAL_GENERATED_ARCHIVE_COUNT;

    while (low < high) {
        size_t middle = low + ((high - low) >> 1);
        u16 current = gTrainerChangeKitArchiveBindings[middle].archive_id;
        if (current < archive_id)
            low = middle + 1u;
        else
            high = middle;
    }
    if (low >= TRAINER_CHANGEKIT_FINAL_GENERATED_ARCHIVE_COUNT
        || gTrainerChangeKitArchiveBindings[low].archive_id != archive_id)
        return NULL;
    if (low + 1u < TRAINER_CHANGEKIT_FINAL_GENERATED_ARCHIVE_COUNT
        && gTrainerChangeKitArchiveBindings[low + 1u].archive_id == archive_id) {
        ++sAmbiguousBindings;
        return NULL;
    }
    return &gTrainerChangeKitArchiveBindings[low];
}

static u8 archive_matches(
    const struct TrainerChangeKitArchiveBindingV1 *row,
    u32 data_address,
    u16 source,
    u8 kind)
{
    u8 expected_format;

    if (row == NULL || !supported_kind(kind)
        || row->data_address != data_address
        || row->source_trainer_id != source || row->kind != kind)
        return 0u;
    expected_format = double_kind(kind)
        ? TRAINER_CHANGEKIT_FORMAT_DOUBLE : TRAINER_CHANGEKIT_FORMAT_SINGLE;
    return (u8)(row->battle_format == expected_format);
}

static const struct TrainerChangeKitExactBindingV1 *find_exact_binding(
    u32 data_address,
    u16 source,
    u8 kind)
{
    const struct TrainerChangeKitExactBindingV1 *match = NULL;
    size_t matches = 0u;
    size_t low = 0u;
    size_t high = TRAINER_CHANGEKIT_FINAL_GENERATED_EXACT_BINDING_COUNT;
    size_t index;

    while (low < high) {
        size_t middle = low + ((high - low) >> 1);
        u32 current = gTrainerChangeKitExactBindings[middle].data_address;
        if (current < data_address)
            low = middle + 1u;
        else
            high = middle;
    }
    for (index = low;
         index < TRAINER_CHANGEKIT_FINAL_GENERATED_EXACT_BINDING_COUNT
             && gTrainerChangeKitExactBindings[index].data_address == data_address;
         ++index) {
        const struct TrainerChangeKitExactBindingV1 *row =
            &gTrainerChangeKitExactBindings[index];
        if (row->source_trainer_id == source && row->kind == kind
            && row->dispatch_id == 0u) {
            match = row;
            ++matches;
        }
    }
    if (matches > 1u) {
        ++sAmbiguousBindings;
        return NULL;
    }
    return matches == 1u ? match : NULL;
}

static const struct TrainerChangeKitGimmickV1 *find_gimmick_exact(
    u16 trainer_id,
    u16 dispatch_id)
{
    u32 target = ((u32)trainer_id << 16) | dispatch_id;
    size_t low = 0u;
    size_t high = TRAINER_CHANGEKIT_FINAL_GENERATED_GIMMICK_COUNT;

    while (low < high) {
        size_t middle = low + ((high - low) >> 1);
        const struct TrainerChangeKitGimmickV1 *row =
            &gTrainerChangeKitGimmicks[middle];
        u32 current = ((u32)row->trainer_id << 16) | row->dispatch_id;
        if (current < target)
            low = middle + 1u;
        else
            high = middle;
    }
    if (low >= TRAINER_CHANGEKIT_FINAL_GENERATED_GIMMICK_COUNT
        || gTrainerChangeKitGimmicks[low].trainer_id != trainer_id
        || gTrainerChangeKitGimmicks[low].dispatch_id != dispatch_id)
        return NULL;
    if (low + 1u < TRAINER_CHANGEKIT_FINAL_GENERATED_GIMMICK_COUNT
        && gTrainerChangeKitGimmicks[low + 1u].trainer_id == trainer_id
        && gTrainerChangeKitGimmicks[low + 1u].dispatch_id == dispatch_id) {
        ++sAmbiguousBindings;
        return NULL;
    }
    return &gTrainerChangeKitGimmicks[low];
}

static const struct TrainerChangeKitGimmickV1 *find_gimmick(
    u16 trainer_id,
    u16 dispatch_id)
{
    const struct TrainerChangeKitGimmickV1 *row =
        find_gimmick_exact(trainer_id, dispatch_id);
    if (row == NULL && dispatch_id != 0u)
        row = find_gimmick_exact(trainer_id, 0u);
    return row;
}

static const struct TrainerChangeKitMemberSidecarV1 *find_sidecar(
    u16 trainer_id,
    u8 side,
    u8 slot)
{
    u32 target = ((u32)trainer_id << 16) | ((u32)side << 8) | slot;
    size_t low = 0u;
    size_t high = TRAINER_CHANGEKIT_FINAL_GENERATED_SIDECAR_COUNT;
    const struct TrainerChangeKitMemberSidecarV1 *row;

    while (low < high) {
        size_t middle = low + ((high - low) >> 1);
        const struct TrainerChangeKitMemberSidecarV1 *candidate =
            &gTrainerChangeKitMemberSidecars[middle];
        u32 current = ((u32)candidate->trainer_id << 16)
            | ((u32)candidate->side << 8) | candidate->slot;
        if (current < target)
            low = middle + 1u;
        else
            high = middle;
    }
    if (low >= TRAINER_CHANGEKIT_FINAL_GENERATED_SIDECAR_COUNT)
        return NULL;
    row = &gTrainerChangeKitMemberSidecars[low];
    if (row->trainer_id != trainer_id || row->side != side || row->slot != slot)
        return NULL;
    if (low + 1u < TRAINER_CHANGEKIT_FINAL_GENERATED_SIDECAR_COUNT) {
        const struct TrainerChangeKitMemberSidecarV1 *next =
            &gTrainerChangeKitMemberSidecars[low + 1u];
        if (next->trainer_id == trainer_id && next->side == side
            && next->slot == slot) {
            ++sAmbiguousBindings;
            return NULL;
        }
    }
    return row;
}

static u32 repeated_iv_bits(u8 iv)
{
    u32 value = (u32)(iv & 31u);
    return value | (value << 5) | (value << 10) | (value << 15)
        | (value << 20) | (value << 25);
}

static void apply_sidecar(
    u8 *mon,
    const struct TrainerChangeKitMemberSidecarV1 *row)
{
    u16 met_bits;
    u32 iv_bits;
    u16 max_hp;

    if (row->species_id == 0u || row->level == 0u || row->level > 100u)
        return;

    /* CFRU's optional trainer scaling may alter a form and level before this
     * hook. ChangeKit parties are fixed authoring records, so restore their
     * exact identity before recalculating live stats. */
    write_u16(mon + TRAINER_CHANGEKIT_BACKUP_SPECIES_OFFSET, row->species_id);
    write_u16(mon + TRAINER_CHANGEKIT_SPECIES_OFFSET, row->species_id);
    mon[TRAINER_CHANGEKIT_LEVEL_OFFSET] = row->level;
    mon[TRAINER_CHANGEKIT_NATURE_MINT_OFFSET] = (u8)(row->nature_id + 1u);
    met_bits = read_u16(mon + TRAINER_CHANGEKIT_MET_BITS_OFFSET);
    met_bits = (u16)((met_bits & (u16)~0x007Fu) | row->level);
    met_bits &= (u16)~TRAINER_CHANGEKIT_HIDDEN_ABILITY_MASK;
    if (row->ability_mode == TRAINER_CHANGEKIT_ABILITY_HIDDEN)
        met_bits |= TRAINER_CHANGEKIT_HIDDEN_ABILITY_MASK;
    write_u16(mon + TRAINER_CHANGEKIT_MET_BITS_OFFSET, met_bits);

    iv_bits = read_u32(mon + TRAINER_CHANGEKIT_IV_BITS_OFFSET);
    iv_bits &= ~TRAINER_CHANGEKIT_IV_FIELD_MASK;
    iv_bits |= repeated_iv_bits(row->iv);
    if (row->ability_mode == TRAINER_CHANGEKIT_ABILITY_SECONDARY)
        iv_bits |= TRAINER_CHANGEKIT_ABILITY_NUM_MASK;
    else
        iv_bits &= ~TRAINER_CHANGEKIT_ABILITY_NUM_MASK;
    write_u32(mon + TRAINER_CHANGEKIT_IV_BITS_OFFSET, iv_bits);

    mon[TRAINER_CHANGEKIT_EV_HP_OFFSET] = row->hp_ev;
    mon[TRAINER_CHANGEKIT_EV_ATK_OFFSET] = row->atk_ev;
    mon[TRAINER_CHANGEKIT_EV_DEF_OFFSET] = row->def_ev;
    mon[TRAINER_CHANGEKIT_EV_SPEED_OFFSET] = row->speed_ev;
    mon[TRAINER_CHANGEKIT_EV_SPATK_OFFSET] = row->sp_atk_ev;
    mon[TRAINER_CHANGEKIT_EV_SPDEF_OFFSET] = row->sp_def_ev;

    FN_CALCULATE_MON_STATS(mon);
    max_hp = read_u16(mon + TRAINER_CHANGEKIT_MAX_HP_OFFSET);
    write_u16(mon + TRAINER_CHANGEKIT_HP_OFFSET, max_hp);
}

static void apply_authored_battle_ability(u8 battler)
{
    const struct TrainerChangeKitMemberSidecarV1 *row;
    u16 slot;

    if (sRuntimeState.phase == TRAINER_CHANGEKIT_PHASE_IDLE
        || battler >= 4u
        || (battler & 1u) != TRAINER_CHANGEKIT_OPPONENT_SIDE)
        return;
    slot = G_BATTLER_PARTY_INDEXES[battler];
    if (slot >= TRAINER_CHANGEKIT_MAX_PARTY_SIZE)
        return;
    row = find_sidecar(
        sRuntimeState.trainer_id,
        TRAINER_CHANGEKIT_OPPONENT_SIDE,
        (u8)slot);
    if (row == NULL || row->ability_id == 0u)
        return;
    write_u16(
        G_BATTLE_MONS
            + (u32)battler * TRAINER_CHANGEKIT_BATTLE_MON_SIZE
            + TRAINER_CHANGEKIT_BATTLE_MON_ABILITY_OFFSET,
        row->ability_id);
}

static void apply_all_authored_battle_abilities(void)
{
    u8 battler;
    u8 count = G_BATTLERS_COUNT;

    if (count > 4u)
        count = 4u;
    for (battler = TRAINER_CHANGEKIT_OPPONENT_SIDE;
         battler < count;
         battler = (u8)(battler + 2u)) {
        if (!(G_ABSENT_BATTLER_FLAGS & (1u << battler)))
            apply_authored_battle_ability(battler);
    }
}

static u16 rematch_for_active_context(u16 trainer_id)
{
    size_t index;
    u16 result = 0u;
    size_t matches = 0u;

    ensure_runtime_storage();
    if (sCommandDataAddress == 0u || sCommandSource != trainer_id)
        return 0u;
    if (sCommandDispatch != 0u) {
        const struct TrainerChangeKitArchiveBindingV1 *archive =
            find_archive(sCommandDispatch);
        if (archive_matches(
                archive, sCommandDataAddress, trainer_id, sCommandKind))
            return archive->target_trainer_id;
    }
    for (index = 0u;
         index < TRAINER_CHANGEKIT_FINAL_GENERATED_REMATCH_COUNT;
         ++index) {
        const struct TrainerChangeKitRematchV2 *row =
            &gTrainerChangeKitRematchMap[index];
        if (row->data_address == sCommandDataAddress
            && row->stock_trainer_id == trainer_id) {
            result = row->target_trainer_id;
            ++matches;
        }
    }
    if (matches > 1u) {
        ++sAmbiguousBindings;
        return 0u;
    }
    return matches == 1u ? result : 0u;
}

static void configure_gimmick_policy(
    u16 trainer_id,
    u16 dispatch_id,
    u16 physical_flag,
    u8 kind)
{
    const struct TrainerChangeKitGimmickV1 *row =
        find_gimmick(trainer_id, dispatch_id);

    if (row == NULL
        || row->mechanic_mode > TRAINER_CHANGEKIT_MECHANIC_TERASTAL
        || !valid_ai_profile(row->ai_profile)
        || row->user_slot >= TRAINER_CHANGEKIT_MAX_PARTY_SIZE
        || (row->mechanic_mode == TRAINER_CHANGEKIT_MECHANIC_STANDARD
            && ((row->flags & TRAINER_CHANGEKIT_GIMMICK_CONSUMER)
                || row->user_slot != 0u))
        || (row->mechanic_mode != TRAINER_CHANGEKIT_MECHANIC_STANDARD
            && !(row->flags & TRAINER_CHANGEKIT_GIMMICK_CONSUMER))
        || (row->mechanic_mode == TRAINER_CHANGEKIT_MECHANIC_TERASTAL
            && !valid_tera_type(row->tera_type))
        || (row->mechanic_mode != TRAINER_CHANGEKIT_MECHANIC_STANDARD
            && double_kind(kind)
            && !(row->flags & TRAINER_CHANGEKIT_GIMMICK_DOUBLE_OK)))
        return;

    if (!FN_CONFIGURE_POLICY(row->ai_profile, row->mechanic_mode)) {
        ++sPolicyFailures;
        FN_PENDING_CLEAR();
        return;
    }
    sRuntimeState.trainer_id = trainer_id;
    sRuntimeState.dispatch_id = dispatch_id;
    sRuntimeState.physical_flag = physical_flag;
    sRuntimeState.mechanic_mode = row->mechanic_mode;
    sRuntimeState.ai_profile = row->ai_profile;
    sRuntimeState.user_slot = row->user_slot;
    sRuntimeState.phase = TRAINER_CHANGEKIT_PHASE_PENDING;
    sRuntimeState.activation_used = 0u;
    sRuntimeState.transient_active = 0u;
    sRuntimeState.user_present = 1u;
    sRuntimeState.user_seen = 0u;
    sCurrentGimmick = row;
}

static void apply_authored_tera_type(void)
{
    if (sRuntimeState.phase == TRAINER_CHANGEKIT_PHASE_ACTIVE
        && sRuntimeState.mechanic_mode
            == TRAINER_CHANGEKIT_MECHANIC_TERASTAL
        && sCurrentGimmick != NULL
        && sRuntimeState.user_slot < TRAINER_CHANGEKIT_MAX_PARTY_SIZE
        && valid_tera_type(sCurrentGimmick->tera_type)) {
        G_ENEMY_PARTY[(u32)sRuntimeState.user_slot
                * TRAINER_CHANGEKIT_MON_SIZE
            + TRAINER_CHANGEKIT_TERA_TYPE_OFFSET] =
            sCurrentGimmick->tera_type;
    }
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_Probe)
u32 TrainerChangeKitFinalRuntime_Probe(u32 selector)
{
    ensure_runtime_storage();
    switch (selector) {
    case TRAINER_CHANGEKIT_PROBE_MAGIC:
        return TRAINER_CHANGEKIT_RUNTIME_MAGIC;
    case TRAINER_CHANGEKIT_PROBE_ENCOUNTER_COUNT:
        return TRAINER_CHANGEKIT_FINAL_GENERATED_ENCOUNTER_COUNT;
    case TRAINER_CHANGEKIT_PROBE_SIDECAR_COUNT:
        return TRAINER_CHANGEKIT_FINAL_GENERATED_SIDECAR_COUNT;
    case TRAINER_CHANGEKIT_PROBE_REMATCH_COUNT:
        return TRAINER_CHANGEKIT_FINAL_GENERATED_REMATCH_COUNT;
    case TRAINER_CHANGEKIT_PROBE_FLAG_MAP_COUNT:
        return TRAINER_CHANGEKIT_FINAL_GENERATED_FLAG_MAP_COUNT;
    case TRAINER_CHANGEKIT_PROBE_TRAINER_TABLE_COUNT:
        return TRAINER_CHANGEKIT_FINAL_GENERATED_TRAINER_TABLE_COUNT;
    case TRAINER_CHANGEKIT_PROBE_EXACT_BINDING_COUNT:
        return TRAINER_CHANGEKIT_FINAL_GENERATED_EXACT_BINDING_COUNT;
    case TRAINER_CHANGEKIT_PROBE_ARCHIVE_COUNT:
        return TRAINER_CHANGEKIT_FINAL_GENERATED_ARCHIVE_COUNT;
    case TRAINER_CHANGEKIT_PROBE_GIMMICK_COUNT:
        return TRAINER_CHANGEKIT_FINAL_GENERATED_GIMMICK_COUNT;
    case TRAINER_CHANGEKIT_PROBE_PHASE:
        return sRuntimeState.phase;
    case TRAINER_CHANGEKIT_PROBE_AMBIGUOUS_BINDINGS:
        return sAmbiguousBindings;
    case TRAINER_CHANGEKIT_PROBE_POLICY_FAILURES:
        return sPolicyFailures;
    case TRAINER_CHANGEKIT_PROBE_CURRENT_TRAINER:
        return sRuntimeState.trainer_id;
    case TRAINER_CHANGEKIT_PROBE_CURRENT_DISPATCH:
        return sRuntimeState.dispatch_id;
    default:
        return 0u;
    }
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_ScriptFlagGet)
u8 TrainerChangeKitFinalRuntime_ScriptFlagGet(void)
{
    return FN_FLAG_GET(map_flag(FN_GET_TRAINER_FLAG()));
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_ScriptFlagSet)
u8 TrainerChangeKitFinalRuntime_ScriptFlagSet(void)
{
    return FN_FLAG_SET(map_flag(FN_GET_TRAINER_FLAG()));
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_HasTrainerBeenFought)
u8 TrainerChangeKitFinalRuntime_HasTrainerBeenFought(u16 trainer_id)
{
    return FN_FLAG_GET(map_flag((u16)(TRAINER_CHANGEKIT_FLAG_START + trainer_id)));
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_SetTrainerFlag)
u8 TrainerChangeKitFinalRuntime_SetTrainerFlag(u16 trainer_id)
{
    return FN_FLAG_SET(map_flag((u16)(TRAINER_CHANGEKIT_FLAG_START + trainer_id)));
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_ClearTrainerFlag)
u8 TrainerChangeKitFinalRuntime_ClearTrainerFlag(u16 trainer_id)
{
    return FN_FLAG_CLEAR(map_flag((u16)(TRAINER_CHANGEKIT_FLAG_START + trainer_id)));
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_GetRematchTrainerId)
u16 TrainerChangeKitFinalRuntime_GetRematchTrainerId(u16 trainer_id)
{
    u16 resolved = FN_GET_REMATCH(trainer_id);
    u16 contextual = rematch_for_active_context(trainer_id);
    u16 fallback = 0u;
    size_t fallback_count = 0u;
    size_t index;

    /* Kind 5/7 proxy commands may use a generated ID beyond the stock
     * selector's range.  The exact command tuple is authoritative even when
     * that stock selector returns zero; only a context-free zero remains a
     * story/availability gate. */
    if (contextual != 0u)
        return contextual;
    if (resolved == 0u)
        return 0u;

    for (index = 0u;
         index < TRAINER_CHANGEKIT_FINAL_GENERATED_REMATCH_COUNT;
         ++index) {
        const struct TrainerChangeKitRematchV2 *row =
            &gTrainerChangeKitRematchMap[index];
        if (row->stock_trainer_id == trainer_id) {
            fallback = row->target_trainer_id;
            ++fallback_count;
        }
    }
    return fallback_count == 1u ? fallback : resolved;
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_SelectArchive)
u8 TrainerChangeKitFinalRuntime_SelectArchive(u16 archive_id)
{
    ensure_runtime_storage();
    if (archive_id == 0u || find_archive(archive_id) == NULL) {
        sArchiveSelection = 0u;
        return 0u;
    }
    sArchiveSelection = archive_id;
    return 1u;
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_ClearArchiveSelection)
void TrainerChangeKitFinalRuntime_ClearArchiveSelection(void)
{
    ensure_runtime_storage();
    sArchiveSelection = 0u;
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_ConfigureTrainerBattle)
const u8 *TrainerChangeKitFinalRuntime_ConfigureTrainerBattle(const u8 *data)
{
    const struct TrainerChangeKitArchiveBindingV1 *archive = NULL;
    const struct TrainerChangeKitExactBindingV1 *exact;
    const u8 *next;
    u32 address;
    u16 source;
    u16 target;
    u16 dispatch = 0u;
    u16 physical_flag = 0u;
    u8 kind;

    if (data == NULL)
        return NULL;
    cleanup_stale_owned_policy();
    address = COMMAND_ADDRESS(data);
    kind = data[0];
    source = read_u16(data + 1u);

    if (sArchiveSelection != 0u) {
        archive = find_archive(sArchiveSelection);
        if (!archive_matches(archive, address, source, kind))
            archive = NULL;
    }
    if (archive != NULL)
        dispatch = archive->archive_id;

    sCommandDataAddress = address;
    sCommandSource = source;
    sCommandKind = kind;
    sCommandDispatch = dispatch;
    next = FN_CONFIGURE_TRAINER_BATTLE(data);
    target = G_TRAINER_OPPONENT_A;

    if (archive != NULL) {
        target = archive->target_trainer_id;
        physical_flag = archive->physical_flag;
    } else {
        exact = find_exact_binding(address, source, kind);
        if (exact != NULL)
            target = exact->target_trainer_id;
    }
    G_TRAINER_OPPONENT_A = target;
    configure_gimmick_policy(target, dispatch, physical_flag, kind);
    sPartySetupPending = (u8)(sCurrentGimmick != NULL
        && sRuntimeState.phase == TRAINER_CHANGEKIT_PHASE_PENDING);
    sPartySetupTrainerId = sPartySetupPending ? target : 0u;

    sArchiveSelection = 0u;
    clear_command_context();
    return next;
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_DispatchArchive)
const u8 *TrainerChangeKitFinalRuntime_DispatchArchive(
    u16 archive_id,
    const u8 *data)
{
    (void)TrainerChangeKitFinalRuntime_SelectArchive(archive_id);
    return TrainerChangeKitFinalRuntime_ConfigureTrainerBattle(data);
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_BuildTrainerPartySetup)
void TrainerChangeKitFinalRuntime_BuildTrainerPartySetup(void)
{
    u16 trainer_id;
    u8 index;

    FN_BUILD_TRAINER_PARTY();
    ensure_runtime_storage();
    /* BuildTrainerPartySetup is also reached by wild and scripted-wild
     * battles.  G_TRAINER_OPPONENT_A is deliberately not cleared by every
     * one of those entrances, so it may still name the preceding trainer.
     * Never use that stale global as ownership: only a command configured by
     * this ChangeKit runtime may receive its generated sidecars. */
    trainer_id = sPartySetupTrainerId;
    if (!sPartySetupPending
        || (G_BATTLE_TYPE_FLAGS & TRAINER_CHANGEKIT_BATTLE_TYPE_TRAINER) == 0u
        || (sRuntimeState.phase != TRAINER_CHANGEKIT_PHASE_PENDING
            && sRuntimeState.phase != TRAINER_CHANGEKIT_PHASE_ACTIVE)
        || sCurrentGimmick == NULL
        || trainer_id != G_TRAINER_OPPONENT_A
        || sRuntimeState.trainer_id != trainer_id) {
        sPartySetupPending = 0u;
        sPartySetupTrainerId = 0u;
        return;
    }
    sPartySetupPending = 0u;
    sPartySetupTrainerId = 0u;
    for (index = 0u; index < TRAINER_CHANGEKIT_MAX_PARTY_SIZE; ++index) {
        const struct TrainerChangeKitMemberSidecarV1 *row =
            find_sidecar(trainer_id, TRAINER_CHANGEKIT_OPPONENT_SIDE, index);
        if (row != NULL)
            apply_sidecar(
                G_ENEMY_PARTY + (u32)index * TRAINER_CHANGEKIT_MON_SIZE,
                row);
    }
    /* CFRU begins its policy lifetime before the stock trainer-party builder
     * on the production scheduler route.  Reapply after the builder so the
     * authored byte is not overwritten; PolicyEnd still restores the backup
     * captured before this point on win/loss/abort/save-reload. */
    apply_authored_tera_type();
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_LoadProperAbilityBattleDataAdapter)
void TrainerChangeKitFinalRuntime_LoadProperAbilityBattleDataAdapter(void)
{
    ensure_runtime_storage();
    FN_LOAD_PROPER_ABILITY_BATTLE_DATA();
    apply_authored_battle_ability(G_ACTIVE_BATTLER);
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_BattleBegin)
u8 TrainerChangeKitFinalRuntime_BattleBegin(void)
{
    ensure_runtime_storage();
    if (sRuntimeState.phase != TRAINER_CHANGEKIT_PHASE_PENDING)
        return 0u;
    sRuntimeState.phase = TRAINER_CHANGEKIT_PHASE_ACTIVE;
    sRuntimeState.user_present = 1u;
    sRuntimeState.user_seen = 0u;
    return 1u;
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_BattleEnd)
void TrainerChangeKitFinalRuntime_BattleEnd(u8 cleanup_reason)
{
    ensure_runtime_storage();
    (void)cleanup_reason;
    if (sRuntimeState.phase == TRAINER_CHANGEKIT_PHASE_PENDING)
        FN_PENDING_CLEAR();
    reset_runtime_state();
    sArchiveSelection = 0u;
    clear_command_context();
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_BattleAbort)
void TrainerChangeKitFinalRuntime_BattleAbort(u8 cleanup_reason)
{
    ensure_runtime_storage();
    if (sRuntimeState.phase == TRAINER_CHANGEKIT_PHASE_ACTIVE) {
        /* VegaBattlePolicyEnd maps the live outcome, restores authored Tera
         * party bytes, then delegates to cfru_integration_battle_end. */
        (void)cleanup_reason;
        (void)FN_POLICY_END();
    } else if (sRuntimeState.phase == TRAINER_CHANGEKIT_PHASE_PENDING) {
        FN_PENDING_CLEAR();
    }
    reset_runtime_state();
    sArchiveSelection = 0u;
    clear_command_context();
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_SaveReloadCleanup)
void TrainerChangeKitFinalRuntime_SaveReloadCleanup(void)
{
    TrainerChangeKitFinalRuntime_BattleAbort(
        TRAINER_CHANGEKIT_CLEANUP_SAVE_RELOAD);
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_PartySlotExit)
void TrainerChangeKitFinalRuntime_PartySlotExit(u8 side, u8 slot)
{
    ensure_runtime_storage();
    if (sRuntimeState.phase == TRAINER_CHANGEKIT_PHASE_ACTIVE
        && side == TRAINER_CHANGEKIT_OPPONENT_SIDE
        && slot == sRuntimeState.user_slot) {
        sRuntimeState.transient_active = 0u;
        sRuntimeState.user_present = 0u;
        sRuntimeState.user_seen = 1u;
    }
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_ShouldActivate)
u8 TrainerChangeKitFinalRuntime_ShouldActivate(
    u16 trainer_id,
    u8 party_slot,
    u8 mechanic_mode)
{
    ensure_runtime_storage();
    return (u8)(sRuntimeState.phase == TRAINER_CHANGEKIT_PHASE_ACTIVE
        && sRuntimeState.trainer_id == trainer_id
        && sRuntimeState.mechanic_mode == mechanic_mode
        && sRuntimeState.user_slot == party_slot
        && sRuntimeState.user_present
        && !sRuntimeState.activation_used);
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_MarkActivated)
u8 TrainerChangeKitFinalRuntime_MarkActivated(
    u16 trainer_id,
    u8 party_slot,
    u8 mechanic_mode)
{
    if (!TrainerChangeKitFinalRuntime_ShouldActivate(
            trainer_id, party_slot, mechanic_mode))
        return 0u;
    sRuntimeState.activation_used = 1u;
    sRuntimeState.transient_active = 1u;
    return 1u;
}

static u8 active_consumer_battler(u8 battler)
{
    ensure_runtime_storage();
    return (u8)(sRuntimeState.phase == TRAINER_CHANGEKIT_PHASE_ACTIVE
        && sCurrentGimmick != NULL
        && battler < 4u
        && (battler & 1u) == TRAINER_CHANGEKIT_OPPONENT_SIDE);
}

static void refresh_gimmick_user_presence(void)
{
    u8 battler;
    u8 count;
    u8 present = 0u;

    if (sRuntimeState.phase != TRAINER_CHANGEKIT_PHASE_ACTIVE)
        return;
    count = G_BATTLERS_COUNT;
    if (count > 4u)
        count = 4u;
    for (battler = TRAINER_CHANGEKIT_OPPONENT_SIDE;
         battler < count;
         battler = (u8)(battler + 2u)) {
        if (!(G_ABSENT_BATTLER_FLAGS & (1u << battler))
            && G_BATTLER_PARTY_INDEXES[battler] == sRuntimeState.user_slot) {
            present = 1u;
            break;
        }
    }
    if (present) {
        sRuntimeState.user_present = 1u;
        sRuntimeState.user_seen = 1u;
    } else if (sRuntimeState.user_seen) {
        sRuntimeState.user_present = 0u;
        sRuntimeState.transient_active = 0u;
    }
}

static u8 adapted_policy_can(
    PolicyCanFn original,
    u8 battler,
    u8 upstream_allowed,
    u8 mechanic_mode)
{
    if (!active_consumer_battler(battler))
        return original(battler, upstream_allowed);
    refresh_gimmick_user_presence();
    if (!TrainerChangeKitFinalRuntime_ShouldActivate(
            sRuntimeState.trainer_id,
            (u8)G_BATTLER_PARTY_INDEXES[battler],
            mechanic_mode))
        return 0u;
    return original(battler, upstream_allowed);
}

static u8 adapted_policy_mark(
    PolicyMarkFn original,
    u8 battler,
    u8 mechanic_mode)
{
    u8 party_slot;

    if (!active_consumer_battler(battler))
        return original(battler);
    refresh_gimmick_user_presence();
    party_slot = (u8)G_BATTLER_PARTY_INDEXES[battler];
    if (!TrainerChangeKitFinalRuntime_ShouldActivate(
            sRuntimeState.trainer_id, party_slot, mechanic_mode))
        return 0u;
    if (!original(battler))
        return 0u;
    return TrainerChangeKitFinalRuntime_MarkActivated(
        sRuntimeState.trainer_id, party_slot, mechanic_mode);
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_CanMegaAdapter)
u8 TrainerChangeKitFinalRuntime_CanMegaAdapter(u8 battler, u8 upstream_allowed)
{
    return adapted_policy_can(
        FN_POLICY_CAN_MEGA,
        battler,
        upstream_allowed,
        TRAINER_CHANGEKIT_MECHANIC_MEGA);
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_MarkMegaAdapter)
u8 TrainerChangeKitFinalRuntime_MarkMegaAdapter(u8 battler)
{
    return adapted_policy_mark(
        FN_POLICY_MARK_MEGA, battler, TRAINER_CHANGEKIT_MECHANIC_MEGA);
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_CanZAdapter)
u8 TrainerChangeKitFinalRuntime_CanZAdapter(u8 battler, u8 upstream_allowed)
{
    return adapted_policy_can(
        FN_POLICY_CAN_Z,
        battler,
        upstream_allowed,
        TRAINER_CHANGEKIT_MECHANIC_Z_MOVE);
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_MarkZAdapter)
u8 TrainerChangeKitFinalRuntime_MarkZAdapter(u8 battler)
{
    return adapted_policy_mark(
        FN_POLICY_MARK_Z, battler, TRAINER_CHANGEKIT_MECHANIC_Z_MOVE);
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_CanDynamaxAdapter)
u8 TrainerChangeKitFinalRuntime_CanDynamaxAdapter(
    u8 battler,
    u8 upstream_allowed)
{
    return adapted_policy_can(
        FN_POLICY_CAN_DYNAMAX,
        battler,
        upstream_allowed,
        TRAINER_CHANGEKIT_MECHANIC_DYNAMAX);
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_MarkDynamaxAdapter)
u8 TrainerChangeKitFinalRuntime_MarkDynamaxAdapter(u8 battler)
{
    return adapted_policy_mark(
        FN_POLICY_MARK_DYNAMAX,
        battler,
        TRAINER_CHANGEKIT_MECHANIC_DYNAMAX);
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_CanTeraAdapter)
u8 TrainerChangeKitFinalRuntime_CanTeraAdapter(u8 battler, u8 upstream_allowed)
{
    return adapted_policy_can(
        FN_POLICY_CAN_TERA,
        battler,
        upstream_allowed,
        TRAINER_CHANGEKIT_MECHANIC_TERASTAL);
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_MarkTeraAdapter)
u8 TrainerChangeKitFinalRuntime_MarkTeraAdapter(u8 battler)
{
    return adapted_policy_mark(
        FN_POLICY_MARK_TERA, battler, TRAINER_CHANGEKIT_MECHANIC_TERASTAL);
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_PolicyBeginAdapter)
u8 TrainerChangeKitFinalRuntime_PolicyBeginAdapter(void)
{
    u8 result = FN_POLICY_BEGIN();
    if (result) {
        u8 owned = TrainerChangeKitFinalRuntime_BattleBegin();
        if (owned)
            apply_all_authored_battle_abilities();
        if (owned) {
            /* VegaBattlePolicyBegin has already backed up both parties and
             * installed species defaults.  This covers routes that build the
             * party before Begin; BuildTrainerPartySetup covers the observed
             * production order where the party is built immediately after. */
            apply_authored_tera_type();
        }
    }
    else
        TrainerChangeKitFinalRuntime_BattleAbort(
            TRAINER_CHANGEKIT_CLEANUP_ABORT);
    return result;
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_PolicyEndAdapter)
u8 TrainerChangeKitFinalRuntime_PolicyEndAdapter(void)
{
    u8 result = FN_POLICY_END();
    TrainerChangeKitFinalRuntime_BattleEnd(TRAINER_CHANGEKIT_CLEANUP_WIN);
    return result;
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_SaveLoadAdapter)
u8 TrainerChangeKitFinalRuntime_SaveLoadAdapter(u8 save_type)
{
    TrainerChangeKitFinalRuntime_SaveReloadCleanup();
    return FN_SAVE_LOAD_GAME_DATA(save_type);
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_CurrentGimmick)
const struct TrainerChangeKitGimmickV1 *
TrainerChangeKitFinalRuntime_CurrentGimmick(void)
{
    ensure_runtime_storage();
    return sCurrentGimmick;
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_SidecarTable)
const struct TrainerChangeKitMemberSidecarV1 *
TrainerChangeKitFinalRuntime_SidecarTable(void)
{
    return gTrainerChangeKitMemberSidecars;
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_ExactBindingTable)
const struct TrainerChangeKitExactBindingV1 *
TrainerChangeKitFinalRuntime_ExactBindingTable(void)
{
    return gTrainerChangeKitExactBindings;
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_RematchTable)
const struct TrainerChangeKitRematchV2 *
TrainerChangeKitFinalRuntime_RematchTable(void)
{
    return gTrainerChangeKitRematchMap;
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_ArchiveTable)
const struct TrainerChangeKitArchiveBindingV1 *
TrainerChangeKitFinalRuntime_ArchiveTable(void)
{
    return gTrainerChangeKitArchiveBindings;
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_GimmickTable)
const struct TrainerChangeKitGimmickV1 *
TrainerChangeKitFinalRuntime_GimmickTable(void)
{
    return gTrainerChangeKitGimmicks;
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_FlagTable)
const struct TrainerChangeKitFlagMapV1 *
TrainerChangeKitFinalRuntime_FlagTable(void)
{
    return gTrainerChangeKitFlagMap;
}

TRAINER_CHANGEKIT_EXPORT(TrainerChangeKitFinalRuntime_TrainerTable)
const void *TrainerChangeKitFinalRuntime_TrainerTable(void)
{
    return (const void *)(uintptr_t)TRAINER_CHANGEKIT_FINAL_TRAINER_TABLE_ADDRESS;
}

/* Stage 34 binary ABI wrappers. */
TRAINER_CHANGEKIT_EXPORT(TrainerV5Runtime_Probe)
u32 TrainerV5Runtime_Probe(u32 selector)
{
    return TrainerChangeKitFinalRuntime_Probe(selector);
}

TRAINER_CHANGEKIT_EXPORT(TrainerV5Runtime_ScriptFlagGet)
u8 TrainerV5Runtime_ScriptFlagGet(void)
{
    return TrainerChangeKitFinalRuntime_ScriptFlagGet();
}

TRAINER_CHANGEKIT_EXPORT(TrainerV5Runtime_ScriptFlagSet)
u8 TrainerV5Runtime_ScriptFlagSet(void)
{
    return TrainerChangeKitFinalRuntime_ScriptFlagSet();
}

TRAINER_CHANGEKIT_EXPORT(TrainerV5Runtime_HasTrainerBeenFought)
u8 TrainerV5Runtime_HasTrainerBeenFought(u16 trainer_id)
{
    return TrainerChangeKitFinalRuntime_HasTrainerBeenFought(trainer_id);
}

TRAINER_CHANGEKIT_EXPORT(TrainerV5Runtime_SetTrainerFlag)
u8 TrainerV5Runtime_SetTrainerFlag(u16 trainer_id)
{
    return TrainerChangeKitFinalRuntime_SetTrainerFlag(trainer_id);
}

TRAINER_CHANGEKIT_EXPORT(TrainerV5Runtime_ClearTrainerFlag)
u8 TrainerV5Runtime_ClearTrainerFlag(u16 trainer_id)
{
    return TrainerChangeKitFinalRuntime_ClearTrainerFlag(trainer_id);
}

TRAINER_CHANGEKIT_EXPORT(TrainerV5Runtime_GetRematchTrainerId)
u16 TrainerV5Runtime_GetRematchTrainerId(u16 trainer_id)
{
    return TrainerChangeKitFinalRuntime_GetRematchTrainerId(trainer_id);
}

TRAINER_CHANGEKIT_EXPORT(TrainerV5Runtime_ConfigureTrainerBattle)
const u8 *TrainerV5Runtime_ConfigureTrainerBattle(const u8 *data)
{
    return TrainerChangeKitFinalRuntime_ConfigureTrainerBattle(data);
}

TRAINER_CHANGEKIT_EXPORT(TrainerV5Runtime_BuildTrainerPartySetup)
void TrainerV5Runtime_BuildTrainerPartySetup(void)
{
    TrainerChangeKitFinalRuntime_BuildTrainerPartySetup();
}

TRAINER_CHANGEKIT_EXPORT(TrainerV5Runtime_SidecarTable)
const void *TrainerV5Runtime_SidecarTable(void)
{
    return TrainerChangeKitFinalRuntime_SidecarTable();
}

TRAINER_CHANGEKIT_EXPORT(TrainerV5Runtime_RematchTable)
const void *TrainerV5Runtime_RematchTable(void)
{
    return TrainerChangeKitFinalRuntime_RematchTable();
}

TRAINER_CHANGEKIT_EXPORT(TrainerV5Runtime_FlagTable)
const void *TrainerV5Runtime_FlagTable(void)
{
    return TrainerChangeKitFinalRuntime_FlagTable();
}

TRAINER_CHANGEKIT_EXPORT(TrainerV5Runtime_ExactRebindTable)
const void *TrainerV5Runtime_ExactRebindTable(void)
{
    return TrainerChangeKitFinalRuntime_ExactBindingTable();
}
