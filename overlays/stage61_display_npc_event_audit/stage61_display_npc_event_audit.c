/*
 * USER-20260830-STAGE60-DISPLAY-NPC-PLACEMENT-AUDIT
 *
 * Imported Kanto uses project map-section IDs 0..52. They must never enter
 * a FireRed/Vega table that assumes the stock 88..196 namespace. This
 * runtime owns the display, Town Map, Fly and persistent-visit boundaries;
 * every non-Kanto path either delegates to an exact relocated stock
 * trampoline or uses the same source-identity table in a shared C owner.
 */

#include <stddef.h>
#include <stdint.h>

#include "../factory_high_modes_v2/factory_high_modes_v2.h"

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;
typedef int8_t s8;
typedef int16_t s16;
typedef int32_t s32;

#define PTR(type, address) ((type)(uintptr_t)(address))
#define STAGE61_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))
#define STAGE61_NAKED_EXPORT(name) \
    __attribute__((section(".text." #name), used, naked, externally_visible))
/*
 * The public adapter deliberately keeps the Factory operation name so the
 * interaction ABI can alias it to PrepareBattle.  Its symbol therefore does
 * not begin with Stage61; keep the section under the Stage61 linker prefix so
 * --gc-sections cannot discard the physical script target.
 */
#define STAGE61_FACTORY_ADAPTER_EXPORT(name) \
    __attribute__((section(".text.Stage61FactoryAdapter." #name), used, \
                   noinline, externally_visible))

#ifndef STAGE61_KANTO_NAME_TABLE
#define STAGE61_KANTO_NAME_TABLE 0u
#endif
#ifndef STAGE61_KANTO_REGION_GRID
#define STAGE61_KANTO_REGION_GRID 0u
#endif
#ifndef STAGE61_KANTO_POSITION_TABLE
#define STAGE61_KANTO_POSITION_TABLE 0u
#endif
#ifndef STAGE61_KANTO_FLY_RECORDS
#define STAGE61_KANTO_FLY_RECORDS 0u
#endif
#ifndef STAGE61_KANTO_FLY_TABLE
#define STAGE61_KANTO_FLY_TABLE 0u
#endif
#ifndef STAGE61_KANTO_VISIT_FLAGS
#define STAGE61_KANTO_VISIT_FLAGS 0u
#endif
#ifndef STAGE61_KANTO_SOURCE_SECTION_IDS
#define STAGE61_KANTO_SOURCE_SECTION_IDS 0u
#endif
#ifndef STAGE61_KANTO_REGION_GFX
#define STAGE61_KANTO_REGION_GFX 0u
#endif
#ifndef STAGE61_KANTO_REGION_TILEMAP
#define STAGE61_KANTO_REGION_TILEMAP 0u
#endif
#ifndef STAGE61_STOCK_GET_MAPSEC_TYPE
#define STAGE61_STOCK_GET_MAPSEC_TYPE 0u
#endif
#ifndef STAGE61_STOCK_GET_DUNGEON_MAPSEC_TYPE
#define STAGE61_STOCK_GET_DUNGEON_MAPSEC_TYPE 0u
#endif
#ifndef STAGE61_STOCK_GET_PLAYER_POSITION
#define STAGE61_STOCK_GET_PLAYER_POSITION 0u
#endif
#ifndef STAGE61_STOCK_GET_SELECTED_MAP_SECTION
#define STAGE61_STOCK_GET_SELECTED_MAP_SECTION 0u
#endif
#ifndef STAGE61_STOCK_GET_MAP_PREVIEW_SCREEN_IDX
#define STAGE61_STOCK_GET_MAP_PREVIEW_SCREEN_IDX 0u
#endif
#ifndef STAGE61_STOCK_GET_DUNGEON_FLAVOR_TEXT
#define STAGE61_STOCK_GET_DUNGEON_FLAVOR_TEXT 0u
#endif
#ifndef STAGE61_STOCK_GET_DUNGEON_NAME
#define STAGE61_STOCK_GET_DUNGEON_NAME 0u
#endif
#ifndef STAGE61_STOCK_HANDLE_SAVING_DATA
#define STAGE61_STOCK_HANDLE_SAVING_DATA 0u
#endif
#ifndef STAGE61_QUEST_LOG_PROJECT_PAIRS
#define STAGE61_QUEST_LOG_PROJECT_PAIRS 0u
#endif
#ifndef STAGE61_QUEST_LOG_SOURCE_PAIRS
#define STAGE61_QUEST_LOG_SOURCE_PAIRS 0u
#endif
#ifndef STAGE61_TRAINER_REMATCH_ALIAS_TABLE
#error "STAGE61_TRAINER_REMATCH_ALIAS_TABLE is required"
#endif
#ifndef STAGE61_TRAINER_REMATCH_ALIAS_COUNT
#error "STAGE61_TRAINER_REMATCH_ALIAS_COUNT is required"
#endif
#ifndef STAGE61_CHANGEKIT_GET_REMATCH
#error "STAGE61_CHANGEKIT_GET_REMATCH is required"
#endif

enum {
    STAGE61_ABI_VERSION = 0x31365344u,
    STAGE61_KANTO_SECTION_COUNT = 53u,
    STAGE61_KANTO_CITY_COUNT = 11u,
    STAGE61_KANTO_DUNGEON_START = 36u,
    STAGE61_STOCK_SECTION_START = 88u,
    STAGE61_STOCK_SECTION_COUNT = 109u,
    STAGE61_MAPSEC_NONE = 197u,
    STAGE61_DEFAULT_NAME_FILL = 18u,
    STAGE61_CHAR_SPACE = 0x00u,
    STAGE61_EOS = 0xFFu,
    STAGE61_REGION_KANTO = 0u,
    STAGE61_LAYER_COUNT = 2u,
    STAGE61_MAP_WIDTH = 22u,
    STAGE61_MAP_HEIGHT = 15u,
    STAGE61_MAPSECTYPE_NONE = 0u,
    STAGE61_MAPSECTYPE_ROUTE = 1u,
    STAGE61_MAPSECTYPE_VISITED = 2u,
    STAGE61_MAPSECTYPE_NOT_VISITED = 3u,
    STAGE61_SAVE_SLOT_SECTORS = 14u,
    STAGE61_SAVE_SECTION_SIZE = 0x1000u,
    STAGE61_SAVE_TAIL_END = 0xFF0u,
    STAGE61_SAVE_ID_OFFSET = 0xFF4u,
    STAGE61_SAVE_CHECKSUM_OFFSET = 0xFF6u,
    STAGE61_SAVE_SIGNATURE_OFFSET = 0xFF8u,
    STAGE61_SAVE_COUNTER_OFFSET = 0xFFCu,
    STAGE61_SAVE_SIGNATURE = 0x08012025u,
    STAGE61_SAVE_FULL_MASK = 0x3FFFu,
    STAGE61_SAVE_STATUS_EMPTY = 0u,
    STAGE61_SAVE_STATUS_OK = 1u,
    STAGE61_SAVE_STATUS_INVALID = 2u,
    STAGE61_SAVE_STATUS_ERROR = 0xFFu,
    STAGE61_SAVE_TYPE_NORMAL = 0u,
    STAGE61_SAVE_TYPE_LINK = 1u,
    STAGE61_EWRAM_START = 0x02000000u,
    STAGE61_EWRAM_END = 0x02040000u,
    STAGE61_SAVE_BLOCK2_SIZE = 0x0F24u,
    STAGE61_SAVE_BLOCK1_SIZE = 0x3D40u,
    STAGE61_POKEMON_STORAGE_SIZE = 0x83D0u,
    STAGE61_STATE_MAGIC = 0x45313653u, /* "S61E", little endian. */
    STAGE61_STATE_VERSION = 1u,
    STAGE61_STATE_HEADER_SIZE = 16u,
    STAGE61_STATE_FLAGS_SIZE = 0x200u,
    STAGE61_STATE_VARS_SIZE = 0x400u,
    STAGE61_STATE_LAST_BALL_SIZE = 2u,
    STAGE61_STATE_COINS_SIZE = 4u,
    STAGE61_STATE_PAYLOAD_SIZE = 0x606u,
    STAGE61_STATE_RECORD_SIZE = 0x616u,
    STAGE61_PREVIEW_COUNT = 28u,
    STAGE61_PREVIEW_ROW_SIZE = 16u,
    STAGE61_PREVIEW_TYPE_CAVE = 0u,
    STAGE61_QUEST_LOG_PAIR_COUNT = 51u,
    STAGE61_QUEST_LOG_PAIR_SIZE = 6u,
    STAGE61_VAR_QL_ENTRANCE = 0x404Du,
    STAGE61_FLAG_SYS_QL_DEPARTED = 0x0808u,
    STAGE61_QL_EVENT_DEPARTED = 35u,
    STAGE61_QL_GAME_CORNER = 32u,
    STAGE61_QL_ROCKET_HIDEOUT = 35u,
    STAGE61_MAP_PREVIEW_NAME_RETURN = 0x080F93D4u,
    STAGE61_RAID_FLAG_BASE = 0x15C0u,
    STAGE61_RAID_FLAG_END = 0x162Cu,
    STAGE61_LEGACY_RAID_FLAG_BASE = 0x1800u,
    STAGE61_LEGACY_RAID_FLAG_END = 0x186Cu,
    STAGE61_SOURCE_SEAFOAM_GROUP = 1u,
    STAGE61_PROJECT_SEAFOAM_GROUP = 97u,
    STAGE61_SEAFOAM_B3F_MAP = 86u,
    STAGE61_SEAFOAM_B4F_MAP = 87u,
    STAGE61_FACTORY_STATE_MAGIC = 0x324D4846u, /* "FHM2". */
    STAGE61_FACTORY_PHASE_ACTIVE = 3u,
    STAGE61_FACTORY_STATUS_ERROR = 0u,
    STAGE61_FACTORY_PREPARE_ENTRY = 0x093C3B5Du,
    STAGE61_FACTORY_SPECIAL_RESULT = 0x02037004u,
    STAGE61_FACTORY_FAULT_ARM_0 = 0x53u, /* "S61F" + byte inverses. */
    STAGE61_FACTORY_FAULT_ARM_1 = 0x46u,
};

_Static_assert(sizeof(FactoryHighModesV2State) == 1280u,
               "Factory state size differs");
_Static_assert(offsetof(FactoryHighModesV2State, last_status) == 0x20u,
               "Factory last_status offset differs");
_Static_assert(offsetof(FactoryHighModesV2State, active) == 0x62u,
               "Factory active offset differs");
_Static_assert(offsetof(FactoryHighModesV2State, phase) == 0x6Au,
               "Factory phase offset differs");
_Static_assert(offsetof(FactoryHighModesV2State, reserved_header) == 0x7Du,
               "Factory reserved_header offset differs");

struct Stage61SaveBlockChunk {
    volatile u8 *data;
    u16 size;
    u16 padding;
};

typedef u8 *(*StringCopyFn)(u8 *, const u8 *);
typedef u8 *(*StringFillFn)(u8 *, u8, u16);
typedef u8 (*IsCeladonDeptStoreMapsecFn)(u16);
typedef u8 (*FlagFn)(u16);
typedef void (*MapHeaderRunScriptTypeFn)(u8);
typedef void *(*DecompressBgFn)(u8, const void *, u32, u16, u8);
typedef void (*LzWramFn)(const void *, void *);
typedef u8 (*MapsecTypeFn)(u8);
typedef void (*PlayerPositionFn)(void);
typedef u8 (*SelectedMapSectionFn)(u8, u8, s16, s16);
typedef u8 (*CurrentMapSectionFn)(void);
typedef u8 (*MapPreviewIndexFn)(u8);
typedef const u8 *(*DungeonTextFn)(u16);
typedef const u8 *(*GetMapHeaderFn)(u16, u16);
typedef const u8 *(*GetDestinationMapHeaderFn)(void);
typedef u32 (*GetMonDataFn)(const void *, s32, void *);
typedef void (*SetWarpDestinationToHealLocationFn)(u8);
typedef void (*SetUsedFlyQuestLogEventFn)(const u8 *);
typedef void (*SetWarpDestinationFn)(s8, s8, s8, s8, s8);
typedef void (*SetWarpDestinationToMapWarpFn)(s8, s8, s8);
typedef void (*ReturnToFieldFromFlyMapSelectFn)(void);
typedef u8 (*TryWriteSectorFn)(u8, u8 *);
typedef u8 (*ReadFlashSectionFn)(u8, void *);
typedef u16 (*SaveChecksumFn)(const void *, u16);
typedef u8 (*HandleSavingDataFn)(u8);
typedef void (*SaveVoidFn)(void);
typedef u16 (*EraseFlashSectorFn)(u16);
typedef u16 (*ProgramFlashByteFn)(u16, u32, u8);
typedef void (*SetDamagedSectorBitsFn)(u8, u8);
typedef u8 (*SelectedRegionMapFn)(void);
typedef void (*FadeScreenFn)(u32, s8);
typedef u8 (*MapTransitionFn)(u8, u8);
typedef u8 (*CurrentMapTypeFn)(void);
typedef u8 (*MetatileBehaviorFn)(u8);
typedef u16 (*VarGetFn)(u16);
typedef u8 (*VarSetFn)(u16, u16);
typedef void *(*SetQuestLogEventFn)(u16, const u16 *);
typedef void (*LoadMonIconPalettesFn)(void);
typedef void (*SpriteCallbackFn)(void *);
typedef u8 (*CreateMonIconFn)(
    u16, SpriteCallbackFn, s16, s16, u8, u32, u32);
typedef u16 (*FactoryPrepareBattleFn)(void);
typedef u16 (*GetRematchTrainerIdFn)(u16);

struct Stage61TrainerRematchAlias {
    u32 command_data_address;
    u16 source_trainer_id;
    u16 target_trainer_id;
};

_Static_assert(sizeof(struct Stage61TrainerRematchAlias) == 8u,
               "Trainer rematch alias row size differs");

#define FN_STRING_COPY PTR(StringCopyFn, 0x08008901u)
#define FN_STRING_FILL PTR(StringFillFn, 0x08008D81u)
#define FN_IS_CELADON_DEPT_STORE_MAPSEC \
    PTR(IsCeladonDeptStoreMapsecFn, 0x080C5F25u)
#define FN_FLAG_SET PTR(FlagFn, 0x0806DE75u)
#define FN_FLAG_GET PTR(FlagFn, 0x0806DEC5u)
#define FN_FLAG_CLEAR PTR(FlagFn, 0x0806DE9Du)
#define FN_FACTORY_PREPARE_BATTLE \
    PTR(FactoryPrepareBattleFn, STAGE61_FACTORY_PREPARE_ENTRY)
#define FN_CHANGEKIT_GET_REMATCH \
    PTR(GetRematchTrainerIdFn, STAGE61_CHANGEKIT_GET_REMATCH)
#define TRAINER_REMATCH_ALIASES \
    PTR(const struct Stage61TrainerRematchAlias *, \
        STAGE61_TRAINER_REMATCH_ALIAS_TABLE)
#define G_CHANGEKIT_COMMAND_DATA_ADDRESS \
    PTR(volatile const u32 *, 0x0203EDD8u)
#define G_CHANGEKIT_COMMAND_SOURCE \
    PTR(volatile const u16 *, 0x0203EDDCu)
#define G_FACTORY_SPECIAL_RESULT \
    PTR(volatile u16 *, STAGE61_FACTORY_SPECIAL_RESULT)
#define FN_MAP_HEADER_RUN_SCRIPT_TYPE \
    PTR(MapHeaderRunScriptTypeFn, 0x08069481u)
#define FN_DECOMPRESS_BG PTR(DecompressBgFn, 0x080F78D1u)
#define FN_LZ77_UNCOMP_WRAM PTR(LzWramFn, 0x081C7A91u)
#define FN_STOCK_GET_MAPSEC_TYPE \
    PTR(MapsecTypeFn, STAGE61_STOCK_GET_MAPSEC_TYPE)
#define FN_STOCK_GET_DUNGEON_MAPSEC_TYPE \
    PTR(MapsecTypeFn, STAGE61_STOCK_GET_DUNGEON_MAPSEC_TYPE)
#define FN_STOCK_GET_PLAYER_POSITION \
    PTR(PlayerPositionFn, STAGE61_STOCK_GET_PLAYER_POSITION)
#define FN_STOCK_GET_SELECTED_MAP_SECTION \
    PTR(SelectedMapSectionFn, STAGE61_STOCK_GET_SELECTED_MAP_SECTION)
#define FN_GET_CURRENT_MAP_SECTION PTR(CurrentMapSectionFn, 0x08055B21u)
#define FN_STOCK_GET_MAP_PREVIEW_SCREEN_IDX \
    PTR(MapPreviewIndexFn, STAGE61_STOCK_GET_MAP_PREVIEW_SCREEN_IDX)
#define FN_STOCK_GET_DUNGEON_FLAVOR_TEXT \
    PTR(DungeonTextFn, STAGE61_STOCK_GET_DUNGEON_FLAVOR_TEXT)
#define FN_STOCK_GET_DUNGEON_NAME \
    PTR(DungeonTextFn, STAGE61_STOCK_GET_DUNGEON_NAME)
#define FN_GET_MAP_HEADER PTR(GetMapHeaderFn, 0x08054AF9u)
#define FN_GET_DESTINATION_MAP_HEADER \
    PTR(GetDestinationMapHeaderFn, 0x08054B11u)
#define FN_GET_MON_DATA PTR(GetMonDataFn, 0x0803F355u)
#define FN_SET_WARP_DESTINATION_TO_HEAL_LOCATION \
    PTR(SetWarpDestinationToHealLocationFn, 0x08054D2Du)
#define FN_SET_USED_FLY_QUEST_LOG_EVENT \
    PTR(SetUsedFlyQuestLogEventFn, 0x08125581u)
#define FN_SET_WARP_DESTINATION PTR(SetWarpDestinationFn, 0x08054C4Du)
#define FN_SET_WARP_DESTINATION_TO_MAP_WARP \
    PTR(SetWarpDestinationToMapWarpFn, 0x08054C89u)
#define FN_RETURN_TO_FIELD_FROM_FLY_MAP_SELECT \
    PTR(ReturnToFieldFromFlyMapSelectFn, 0x08083EB5u)
#define FN_TRY_WRITE_SECTOR PTR(TryWriteSectorFn, 0x080DA9C1u)
#define FN_READ_FLASH_SECTION PTR(ReadFlashSectionFn, 0x080DB179u)
#define FN_SAVE_CHECKSUM PTR(SaveChecksumFn, 0x080DB191u)
#define FN_UPDATE_SAVE_ADDRESSES PTR(SaveVoidFn, 0x080DB1BDu)
#define FN_SAVE_SERIALIZED_GAME PTR(SaveVoidFn, 0x0804BAB9u)
#define FN_STOCK_HANDLE_SAVING_DATA \
    PTR(HandleSavingDataFn, STAGE61_STOCK_HANDLE_SAVING_DATA)
#define FN_SET_DAMAGED_SECTOR_BITS \
    PTR(SetDamagedSectorBitsFn, 0x080DA755u)
#define FN_GET_SELECTED_REGION_MAP \
    PTR(SelectedRegionMapFn, 0x080C2005u)
#define FN_GET_SELECTED_MAP_SECTION \
    PTR(SelectedMapSectionFn, 0x080C5349u)
#define FN_FADE_SCREEN PTR(FadeScreenFn, 0x08079F79u)
#define FN_MAP_TRANSITION_IS_ENTER PTR(MapTransitionFn, 0x080CAF49u)
#define FN_GET_CURRENT_MAP_TYPE PTR(CurrentMapTypeFn, 0x08055A49u)
#define FN_METATILE_BEHAVIOR_IS_SURFABLE \
    PTR(MetatileBehaviorFn, 0x08059561u)
#define FN_VAR_GET PTR(VarGetFn, 0x0806DD5Du)
#define FN_VAR_SET PTR(VarSetFn, 0x0806DD79u)
#define FN_SET_QUEST_LOG_EVENT PTR(SetQuestLogEventFn, 0x08114075u)
#define FN_LOAD_MON_ICON_PALETTES \
    PTR(LoadMonIconPalettesFn, 0x08096AA9u)
#define FN_SPRITE_CB_POKE_ICON PTR(SpriteCallbackFn, 0x08096BB9u)
#define FN_CREATE_MON_ICON PTR(CreateMonIconFn, 0x08096845u)

#define STOCK_MAP_NAMES PTR(const u8 *const *, 0x083B8834u)
#define STOCK_CELADON_DEPT_NAME PTR(const u8 *, 0x083B5DBBu)
#define STOCK_FLY_DESTINATIONS PTR(const u8 *, 0x083B9A68u)
#define KANTO_MAP_NAMES PTR(const u8 *const *, STAGE61_KANTO_NAME_TABLE)
#define KANTO_REGION_GRID PTR(const u8 *, STAGE61_KANTO_REGION_GRID)
#define KANTO_POSITIONS PTR(const u8 *, STAGE61_KANTO_POSITION_TABLE)
#define KANTO_FLY_RECORDS PTR(const u8 *, STAGE61_KANTO_FLY_RECORDS)
#define KANTO_FLY_DESTINATIONS PTR(const u8 *, STAGE61_KANTO_FLY_TABLE)
#define KANTO_VISIT_FLAGS PTR(const u16 *, STAGE61_KANTO_VISIT_FLAGS)
#define KANTO_SOURCE_SECTION_IDS \
    PTR(const u8 *, STAGE61_KANTO_SOURCE_SECTION_IDS)
#define KANTO_REGION_GFX PTR(const void *, STAGE61_KANTO_REGION_GFX)
#define KANTO_REGION_TILEMAP PTR(const void *, STAGE61_KANTO_REGION_TILEMAP)
#define QUEST_LOG_PROJECT_PAIRS \
    PTR(const u8 *, STAGE61_QUEST_LOG_PROJECT_PAIRS)
#define QUEST_LOG_SOURCE_PAIRS \
    PTR(const u8 *, STAGE61_QUEST_LOG_SOURCE_PAIRS)
#define STOCK_PREVIEW_ROWS PTR(const u8 *, 0x0840268Cu)
#define STOCK_ROAMER_CORNERS PTR(const u16 *, 0x083B89E8u)
#define STOCK_ROAMER_DIMENSIONS PTR(const u16 *, 0x083B8D00u)

/* Exact Japanese FireRed Rev.0 / Stage60 EWRAM globals. */
#define G_MAP_HEADER PTR(volatile u8 *, 0x02036D30u)
#define G_SAVE_BLOCK1_PTR (*PTR(volatile u8 *volatile *, 0x03005048u))
#define G_SAVE_BLOCK2_PTR (*PTR(volatile u8 *volatile *, 0x0300504Cu))
#define G_POKEMON_STORAGE_PTR \
    (*PTR(volatile u8 *volatile *, 0x03005050u))
#define S_MAP_CURSOR_PTR (*PTR(volatile u8 *volatile *, 0x0203995Cu))
#define S_WARP_DESTINATION PTR(volatile u8 *, 0x0203F01Cu)
#define S_MON_SUMMARY_SCREEN \
    (*PTR(volatile u8 *volatile *, 0x0203B0B4u))
#define G_FIRST_SAVE_SECTOR (*PTR(volatile u16 *, 0x030053D0u))
#define G_SAVE_COUNTER (*PTR(volatile u32 *, 0x030053E0u))
#define G_FAST_SAVE_SECTION \
    (*PTR(volatile u8 *volatile *, 0x030053E4u))
#define G_DAMAGED_SAVE_SECTORS (*PTR(volatile u32 *, 0x030053DCu))
#define G_RAM_SAVE_SECTOR_LOCATIONS \
    PTR(const struct Stage61SaveBlockChunk *, 0x03005400u)
#define G_MAIN_VBLANK_COUNTER1 \
    (*PTR(volatile u32 *volatile *, 0x03003150u))
#define G_EXPANDED_FLAGS PTR(volatile u8 *, 0x0203B0E8u)
#define G_EXPANDED_VARS_BYTES PTR(volatile u8 *, 0x0203B2E8u)
#define G_LAST_USED_BALL_BYTES PTR(volatile u8 *, 0x0203B6ECu)
#define G_PLAYER_COINS_BYTES PTR(volatile u8 *, 0x0203B78Cu)
#define G_PROGRAM_FLASH_BYTE \
    (*PTR(ProgramFlashByteFn volatile *, 0x03007474u))
#define G_ERASE_FLASH_SECTOR \
    (*PTR(EraseFlashSectorFn volatile *, 0x03007480u))
#define G_DONT_FADE_WHITE (*PTR(volatile u8 *, 0x0203C6CEu))
#define G_ROAMERS PTR(volatile u8 *, 0x0203B9A8u)
#define G_SPRITES PTR(volatile u8 *, 0x020205B8u)

static u8 stage61_factory_prepare_fault_is_armed(
    const volatile FactoryHighModesV2State *state)
{
    return (u8)(
        state->reserved_header[0] == STAGE61_FACTORY_FAULT_ARM_0
        && state->reserved_header[1] == STAGE61_FACTORY_FAULT_ARM_1
        && state->reserved_header[2]
            == (u8)~STAGE61_FACTORY_FAULT_ARM_0
        && state->reserved_header[3]
            == (u8)~STAGE61_FACTORY_FAULT_ARM_1
    );
}

static void stage61_factory_prepare_fault_clear(
    volatile FactoryHighModesV2State *state)
{
    state->reserved_header[0] = 0u;
    state->reserved_header[1] = 0u;
    state->reserved_header[2] = 0u;
    state->reserved_header[3] = 0u;
}

/*
 * Validation-only one-shot arming seam.  It is intentionally not installed
 * in any field script and never calls a facility lifecycle function.  The
 * mGBA driver may call it only after the real Factory script has reached the
 * owned ACTIVE phase.  Raw host EWRAM writes therefore cannot stand in for
 * the production FieldReception -> draft -> commit sequence.
 */
STAGE61_EXPORT(Stage61Facility_TestSetFactoryPrepareFault)
u16 Stage61Facility_TestSetFactoryPrepareFault(void)
{
    volatile FactoryHighModesV2State *state =
        PTR(volatile FactoryHighModesV2State *,
            FACTORY_HIGH_MODES_V2_STATE_ADDRESS);
    u8 index;

    if (state->magic != STAGE61_FACTORY_STATE_MAGIC
            || state->magic_inverse != ~(u32)STAGE61_FACTORY_STATE_MAGIC
            || state->active != 1u
            || state->phase != STAGE61_FACTORY_PHASE_ACTIVE)
        return 0u;
    for (index = 0u; index < sizeof(state->reserved_header); ++index) {
        if (state->reserved_header[index] != 0u)
            return 0u;
    }
    state->reserved_header[0] = STAGE61_FACTORY_FAULT_ARM_0;
    state->reserved_header[1] = STAGE61_FACTORY_FAULT_ARM_1;
    state->reserved_header[2] = (u8)~STAGE61_FACTORY_FAULT_ARM_0;
    state->reserved_header[3] = (u8)~STAGE61_FACTORY_FAULT_ARM_1;
    return 1u;
}

/*
 * Physical Factory battle script adapter.  An exact, valid arm is consumed
 * before publishing the synthetic PrepareBattle error.  The existing script
 * then takes its ordinary error branch and invokes the real Abort cleanup.
 * Every unarmed, invalid, stale, or second invocation delegates byte-for-byte
 * to the original Stage42 entry.
 */
STAGE61_FACTORY_ADAPTER_EXPORT(
    FactoryHighModesV2_PrepareBattleStage61Adapter)
u16 FactoryHighModesV2_PrepareBattleStage61Adapter(void)
{
    volatile FactoryHighModesV2State *state =
        PTR(volatile FactoryHighModesV2State *,
            FACTORY_HIGH_MODES_V2_STATE_ADDRESS);
    u8 armed = stage61_factory_prepare_fault_is_armed(state);

    if (armed) {
        /* Zeroize first so an interrupt, stale continuation, or second call
         * can never replay the injected result. */
        stage61_factory_prepare_fault_clear(state);
        if (state->magic == STAGE61_FACTORY_STATE_MAGIC
                && state->magic_inverse
                    == ~(u32)STAGE61_FACTORY_STATE_MAGIC
                && state->active == 1u
                && state->phase == STAGE61_FACTORY_PHASE_ACTIVE) {
            state->last_status = STAGE61_FACTORY_STATUS_ERROR;
            *G_FACTORY_SPECIAL_RESULT = STAGE61_FACTORY_STATUS_ERROR;
            return STAGE61_FACTORY_STATUS_ERROR;
        }
    }
    return FN_FACTORY_PREPARE_BATTLE();
}

/* The stock SetDamagedSectorBits entry is an internal low-ROM helper rather
 * than a public ABI.  Stage61's copy-on-write path used its numeric address,
 * which made extension-only erase/program failures return STATUS_ERROR while
 * leaving gDamagedSaveSectors at zero on the linked Stage60 image.  The bitset
 * itself is the stable save ABI consumed by TrySavingData and boot recovery,
 * so own the one-word update here.  Keep the shift bounded: flash has 32
 * physical sectors and an invalid caller must still produce a deterministic
 * nonzero failure signal without invoking undefined C shift behaviour. */
static void stage61_save_mark_damaged(u16 sector)
{
    u16 bounded = sector < 32u ? sector : 31u;

    G_DAMAGED_SAVE_SECTORS |= (1u << bounded);
}

static void stage61_save_clear_damaged(u16 sector)
{
    if (sector < 32u)
        G_DAMAGED_SAVE_SECTORS &= ~(1u << sector);
}

static u8 stage61_save_fail_with_sector(u16 sector)
{
    stage61_save_mark_damaged(sector);
    return STAGE61_SAVE_STATUS_ERROR;
}

static const u16 sStage61SaveChunkOffsets[STAGE61_SAVE_SLOT_SECTORS] = {
    0x0000u,
    0x0000u, 0x0F80u, 0x1F00u, 0x2E80u,
    0x0000u, 0x0F80u, 0x1F00u, 0x2E80u, 0x3E00u,
    0x4D80u, 0x5D00u, 0x6C80u, 0x7C00u,
};

static const u16 sStage61SaveChunkSizes[STAGE61_SAVE_SLOT_SECTORS] = {
    0x0F24u,
    0x0F80u, 0x0F80u, 0x0F80u, 0x0EC0u,
    0x0F80u, 0x0F80u, 0x0F80u, 0x0F80u, 0x0F80u,
    0x0F80u, 0x0F80u, 0x0F80u, 0x07D0u,
};

struct Stage61SaveSlotValidation {
    u32 counter;
    u16 valid_mask;
    u8 status;
    u8 first_save_sector;
    u8 physical_by_id[STAGE61_SAVE_SLOT_SECTORS];
};

static u8 current_group(void)
{
    volatile u8 *save = G_SAVE_BLOCK1_PTR;
    return save == (volatile u8 *)0 ? 0xFFu : save[4];
}

static u8 current_map(void)
{
    volatile u8 *save = G_SAVE_BLOCK1_PTR;
    return save == (volatile u8 *)0 ? 0xFFu : save[5];
}

static u8 stage61_is_seafoam_current_map(u8 group, u8 map)
{
    if (map != STAGE61_SEAFOAM_B3F_MAP
            && map != STAGE61_SEAFOAM_B4F_MAP)
        return 0u;
    return group == STAGE61_SOURCE_SEAFOAM_GROUP
        || group == STAGE61_PROJECT_SEAFOAM_GROUP;
}

/* Japanese FireRed Rev.0 owns this predicate at 0x080553F8.  Its stock
 * implementation accepts only physical (1, 86/87), so the imported Kanto
 * clone at canonical (97, 86/87) loses both fall-warp Surf state and the
 * initial-avatar fast-current guard.  This export intentionally preserves
 * the original bool8(u16) ABI and the exact stock surfability primitive;
 * only the physical-map identity predicate is widened. */
STAGE61_EXPORT(Stage61DisplayNpcEvent_IsSurfableInSeafoamIslands)
u8 Stage61DisplayNpcEvent_IsSurfableInSeafoamIslands(u16 metatile_behavior)
{
    volatile u8 *save;

    if (FN_METATILE_BEHAVIOR_IS_SURFABLE((u8)metatile_behavior) != 1u)
        return 0u;
    save = G_SAVE_BLOCK1_PTR;
    if (save == (volatile u8 *)0)
        return 0u;
    return stage61_is_seafoam_current_map(save[4], save[5]);
}

static u8 current_warp_id(void)
{
    volatile u8 *save = G_SAVE_BLOCK1_PTR;
    return save == (volatile u8 *)0 ? 0xFFu : save[6];
}

static u8 is_imported_kanto_group(u8 group)
{
    return (u8)(group - 96u) < 3u;
}

static u8 imported_kanto_map_is_valid(u8 group, u8 map)
{
    if (group == 96u)
        return map < 38u;
    if (group == 97u)
        return map < 96u;
    if (group == 98u)
        return map < 122u
            && map != 101u && map != 118u && map != 120u;
    return 0u;
}

static u8 is_imported_kanto_context(void)
{
    return is_imported_kanto_group(current_group());
}

static u8 current_project_section(void)
{
    return G_MAP_HEADER[0x14];
}

static u8 project_section_to_source(u8 mapsec)
{
    if (mapsec < STAGE61_KANTO_SECTION_COUNT)
        return KANTO_SOURCE_SECTION_IDS[mapsec];
    return mapsec;
}

static u8 normalize_section_for_physical_group(u8 group, u8 mapsec)
{
    if (!is_imported_kanto_group(group))
        return mapsec;
    if (mapsec >= STAGE61_KANTO_SECTION_COUNT)
        return STAGE61_MAPSEC_NONE;
    return project_section_to_source(mapsec);
}

static u8 is_project_celadon_department(u16 mapsec)
{
    u8 destination_group;
    u8 destination_map;
    u8 number;

    if (mapsec != 6u)
        return 0u;
    if (current_group() == 98u) {
        number = current_map();
        if (number >= 42u && number <= 48u)
            return 1u;
    }
    destination_group = S_WARP_DESTINATION[0];
    destination_map = S_WARP_DESTINATION[1];
    return destination_group == 98u
        && destination_map >= 42u && destination_map <= 48u;
}

static u16 stage61_read16(const volatile u8 *bytes)
{
    return (u16)bytes[0] | (u16)((u16)bytes[1] << 8);
}

static u32 stage61_read32(const volatile u8 *bytes)
{
    return (u32)bytes[0]
        | ((u32)bytes[1] << 8)
        | ((u32)bytes[2] << 16)
        | ((u32)bytes[3] << 24);
}

static void stage61_write16(volatile u8 *bytes, u16 value)
{
    bytes[0] = (u8)value;
    bytes[1] = (u8)(value >> 8);
}

static void stage61_write32(volatile u8 *bytes, u32 value)
{
    bytes[0] = (u8)value;
    bytes[1] = (u8)(value >> 8);
    bytes[2] = (u8)(value >> 16);
    bytes[3] = (u8)(value >> 24);
}

static u8 stage61_save_range_is_permitted(
    const volatile u8 *base, u32 size)
{
    uintptr_t start = (uintptr_t)base;

    if (base == (const volatile u8 *)0
            || (start & 3u) != 0u
            || start < STAGE61_EWRAM_START
            || start >= STAGE61_EWRAM_END)
        return 0u;
    return size <= STAGE61_EWRAM_END - start;
}

static volatile u8 *stage61_save_expected_chunk_data(u16 id)
{
    volatile u8 *base;
    u32 block_size;

    if (id >= STAGE61_SAVE_SLOT_SECTORS)
        return (volatile u8 *)0;
    if (id == 0u) {
        base = G_SAVE_BLOCK2_PTR;
        block_size = STAGE61_SAVE_BLOCK2_SIZE;
    } else if (id < 5u) {
        base = G_SAVE_BLOCK1_PTR;
        block_size = STAGE61_SAVE_BLOCK1_SIZE;
    } else {
        base = G_POKEMON_STORAGE_PTR;
        block_size = STAGE61_POKEMON_STORAGE_SIZE;
    }
    if (stage61_save_range_is_permitted(base, block_size) == 0u)
        return (volatile u8 *)0;
    return base + sStage61SaveChunkOffsets[id];
}

static u8 stage61_save_chunk_descriptor_is_valid(
    u16 id, const struct Stage61SaveBlockChunk *chunks)
{
    volatile u8 *expected;
    u16 expected_size;

    if (chunks == (const void *)0 || id >= STAGE61_SAVE_SLOT_SECTORS)
        return 0u;
    expected = stage61_save_expected_chunk_data(id);
    expected_size = sStage61SaveChunkSizes[id];
    if (expected == (volatile u8 *)0
            || expected_size > STAGE61_SAVE_TAIL_END
            || chunks[id].size > STAGE61_SAVE_TAIL_END
            || chunks[id].size != expected_size
            || chunks[id].data != expected)
        return 0u;
    return 1u;
}

static u8 stage61_save_all_descriptors_are_valid(
    const struct Stage61SaveBlockChunk *chunks)
{
    u16 id;

    for (id = 0u; id < STAGE61_SAVE_SLOT_SECTORS; ++id) {
        if (stage61_save_chunk_descriptor_is_valid(id, chunks) == 0u)
            return 0u;
    }
    return 1u;
}

/* The stock gRamSaveSectorLocations table is refreshed by
 * UpdateSaveAddresses inside HandleSavingData.  A normal Continue relocates
 * SaveBlock1/2/PokemonStorage before that call, so the table can still point
 * at the previous owners when this wrapper runs its preflight.  Build an
 * owned descriptor snapshot from the live owner pointers instead of trusting
 * that temporally stale stock cache.  Rebuild it after stock returns as well:
 * stock is allowed to refresh or relocate its owners while saving. */
static u8 stage61_save_build_live_descriptors(
    struct Stage61SaveBlockChunk chunks[STAGE61_SAVE_SLOT_SECTORS])
{
    u16 id;

    if (chunks == (void *)0)
        return 0u;
    for (id = 0u; id < STAGE61_SAVE_SLOT_SECTORS; ++id) {
        chunks[id].data = stage61_save_expected_chunk_data(id);
        chunks[id].size = sStage61SaveChunkSizes[id];
        chunks[id].padding = 0u;
    }
    return stage61_save_all_descriptors_are_valid(chunks);
}

static void stage61_save_validate_slot(
    u8 physical_base,
    const struct Stage61SaveBlockChunk *chunks,
    struct Stage61SaveSlotValidation *result)
{
    volatile u8 *section = G_FAST_SAVE_SECTION;
    u16 claimed_mask = 0u;
    u8 saw_signature = 0u;
    u8 saw_counter = 0u;
    u8 malformed = 0u;
    u8 index;

    result->counter = 0u;
    result->valid_mask = 0u;
    result->status = STAGE61_SAVE_STATUS_ERROR;
    result->first_save_sector = 0u;
    for (index = 0u; index < STAGE61_SAVE_SLOT_SECTORS; ++index)
        result->physical_by_id[index] = 0xFFu;

    if (section == (volatile u8 *)0
            || stage61_save_all_descriptors_are_valid(chunks) == 0u)
        return;

    for (index = 0u; index < STAGE61_SAVE_SLOT_SECTORS; ++index) {
        u32 counter;
        u16 id;
        u16 bit;
        u16 size;

        (void)FN_READ_FLASH_SECTION(
            (u8)(physical_base + index), (void *)section
        );
        if (stage61_read32(section + STAGE61_SAVE_SIGNATURE_OFFSET)
                != STAGE61_SAVE_SIGNATURE)
            continue;

        saw_signature = 1u;
        counter = stage61_read32(section + STAGE61_SAVE_COUNTER_OFFSET);
        if (saw_counter == 0u) {
            result->counter = counter;
            saw_counter = 1u;
        } else if (counter != result->counter) {
            malformed = 1u;
        }
        if ((u8)(STAGE61_SAVE_SLOT_SECTORS * (counter & 1u))
                != physical_base)
            malformed = 1u;

        /* The footer is untrusted flash data.  Bound id before either the
         * descriptor arrays or chunks[id] can be touched. */
        id = stage61_read16(section + STAGE61_SAVE_ID_OFFSET);
        if (id >= STAGE61_SAVE_SLOT_SECTORS) {
            malformed = 1u;
            continue;
        }
        if (stage61_save_chunk_descriptor_is_valid(id, chunks) == 0u) {
            malformed = 1u;
            continue;
        }
        bit = (u16)(1u << id);
        if ((claimed_mask & bit) != 0u) {
            malformed = 1u;
            continue;
        }
        claimed_mask |= bit;

        size = sStage61SaveChunkSizes[id];
        if (stage61_read16(section + STAGE61_SAVE_CHECKSUM_OFFSET)
                != FN_SAVE_CHECKSUM((const void *)section, size)) {
            malformed = 1u;
            continue;
        }
        result->valid_mask |= bit;
        result->physical_by_id[id] = index;
        if (id == 0u)
            result->first_save_sector = index;
    }

    /* A stock generation is not merely a set of fourteen valid logical IDs.
     * Their physical order is a rotation anchored by logical id 0.  Accepting
     * a checksum-valid permutation lets a later SAVE_LINK update ids 0..4 at
     * the stock rotation positions and overwrite unrelated logical sectors.
     * Reject the whole bank before selection/copy when any relative position
     * differs, so a sound older bank can be selected instead. */
    if (malformed == 0u
            && result->valid_mask == STAGE61_SAVE_FULL_MASK) {
        for (index = 0u; index < STAGE61_SAVE_SLOT_SECTORS; ++index) {
            if (result->physical_by_id[index]
                    != (u8)((result->first_save_sector + index)
                        % STAGE61_SAVE_SLOT_SECTORS)) {
                malformed = 1u;
                break;
            }
        }
    }

    if (saw_signature == 0u)
        result->status = STAGE61_SAVE_STATUS_EMPTY;
    else if (malformed == 0u
            && result->valid_mask == STAGE61_SAVE_FULL_MASK)
        result->status = STAGE61_SAVE_STATUS_OK;
}

static u8 stage61_save_validations_match(
    const struct Stage61SaveSlotValidation *first,
    const struct Stage61SaveSlotValidation *second)
{
    u8 id;

    if (first->status != STAGE61_SAVE_STATUS_OK
            || second->status != STAGE61_SAVE_STATUS_OK
            || first->counter != second->counter
            || first->valid_mask != STAGE61_SAVE_FULL_MASK
            || second->valid_mask != STAGE61_SAVE_FULL_MASK
            || first->first_save_sector != second->first_save_sector)
        return 0u;
    for (id = 0u; id < STAGE61_SAVE_SLOT_SECTORS; ++id) {
        if (first->physical_by_id[id] != second->physical_by_id[id])
            return 0u;
    }
    return 1u;
}

static u8 stage61_save_second_counter_is_newer(u32 first, u32 second)
{
    u32 delta = second - first;

    /* Serial-number arithmetic across every u32 wrap, not only FFFFFFFF/0.
     * Equal counters and the exactly-half-range ambiguous pair retain the
     * first complete slot deterministically. */
    return (u8)(delta != 0u && delta < 0x80000000u);
}

static u8 stage61_save_select_generation(
    const struct Stage61SaveBlockChunk *chunks, u8 *selected_base)
{
    struct Stage61SaveSlotValidation first;
    struct Stage61SaveSlotValidation second;

    stage61_save_validate_slot(0u, chunks, &first);
    stage61_save_validate_slot(
        STAGE61_SAVE_SLOT_SECTORS, chunks, &second
    );
    *selected_base = 0xFFu;

    if (first.status == STAGE61_SAVE_STATUS_OK
            && second.status == STAGE61_SAVE_STATUS_OK) {
        if (stage61_save_second_counter_is_newer(
                first.counter, second.counter)) {
            G_SAVE_COUNTER = second.counter;
            *selected_base = STAGE61_SAVE_SLOT_SECTORS;
        } else {
            G_SAVE_COUNTER = first.counter;
            *selected_base = 0u;
        }
        return STAGE61_SAVE_STATUS_OK;
    }
    if (first.status == STAGE61_SAVE_STATUS_OK) {
        G_SAVE_COUNTER = first.counter;
        *selected_base = 0u;
        return second.status == STAGE61_SAVE_STATUS_ERROR
            ? STAGE61_SAVE_STATUS_ERROR : STAGE61_SAVE_STATUS_OK;
    }
    if (second.status == STAGE61_SAVE_STATUS_OK) {
        G_SAVE_COUNTER = second.counter;
        *selected_base = STAGE61_SAVE_SLOT_SECTORS;
        return first.status == STAGE61_SAVE_STATUS_ERROR
            ? STAGE61_SAVE_STATUS_ERROR : STAGE61_SAVE_STATUS_OK;
    }

    G_SAVE_COUNTER = 0u;
    G_FIRST_SAVE_SECTOR = 0u;
    if (first.status == STAGE61_SAVE_STATUS_EMPTY
            && second.status == STAGE61_SAVE_STATUS_EMPTY)
        return STAGE61_SAVE_STATUS_EMPTY;
    return STAGE61_SAVE_STATUS_INVALID;
}

static void stage61_save_copy_validated_slot(
    u8 physical_base,
    const struct Stage61SaveBlockChunk *chunks,
    const struct Stage61SaveSlotValidation *slot)
{
    volatile u8 *section = G_FAST_SAVE_SECTION;
    u16 id;

    for (id = 0u; id < STAGE61_SAVE_SLOT_SECTORS; ++id) {
        volatile u8 *destination = chunks[id].data;
        u16 size = sStage61SaveChunkSizes[id];
        u32 index;

        (void)FN_READ_FLASH_SECTION(
            (u8)(physical_base + slot->physical_by_id[id]),
            (void *)section
        );
        for (index = 0u; index < size; ++index)
            destination[index] = section[index];
    }
    G_FIRST_SAVE_SECTOR = slot->first_save_sector;
}

static u16 stage61_save_physical_sector_for_id(u16 id)
{
    u16 sector = (u16)((G_FIRST_SAVE_SECTOR + id)
        % STAGE61_SAVE_SLOT_SECTORS);

    return (u16)(sector
        + STAGE61_SAVE_SLOT_SECTORS * (G_SAVE_COUNTER & 1u));
}

static u32 stage61_crc_byte(u32 crc, u8 value)
{
    u32 bit;

    crc ^= value;
    for (bit = 0u; bit < 8u; ++bit) {
        u32 mask = 0u - (crc & 1u);
        crc = (crc >> 1) ^ (0xEDB88320u & mask);
    }
    return crc;
}

static u32 stage61_state_crc(void)
{
    u32 crc = 0xFFFFFFFFu;
    u32 index;

    for (index = 0u; index < STAGE61_STATE_FLAGS_SIZE; ++index)
        crc = stage61_crc_byte(crc, G_EXPANDED_FLAGS[index]);
    for (index = 0u; index < STAGE61_STATE_VARS_SIZE; ++index)
        crc = stage61_crc_byte(crc, G_EXPANDED_VARS_BYTES[index]);
    for (index = 0u; index < STAGE61_STATE_LAST_BALL_SIZE; ++index)
        crc = stage61_crc_byte(crc, G_LAST_USED_BALL_BYTES[index]);
    for (index = 0u; index < STAGE61_STATE_COINS_SIZE; ++index)
        crc = stage61_crc_byte(crc, G_PLAYER_COINS_BYTES[index]);
    return crc ^ 0xFFFFFFFFu;
}

static void stage61_state_clear(void)
{
    u32 index;

    for (index = 0u; index < STAGE61_STATE_FLAGS_SIZE; ++index)
        G_EXPANDED_FLAGS[index] = 0u;
    for (index = 0u; index < STAGE61_STATE_VARS_SIZE; ++index)
        G_EXPANDED_VARS_BYTES[index] = 0u;
    for (index = 0u; index < STAGE61_STATE_LAST_BALL_SIZE; ++index)
        G_LAST_USED_BALL_BYTES[index] = 0u;
    for (index = 0u; index < STAGE61_STATE_COINS_SIZE; ++index)
        G_PLAYER_COINS_BYTES[index] = 0u;
}

static u8 stage61_state_payload_byte(u32 index)
{
    if (index < STAGE61_STATE_FLAGS_SIZE)
        return G_EXPANDED_FLAGS[index];
    index -= STAGE61_STATE_FLAGS_SIZE;
    if (index < STAGE61_STATE_VARS_SIZE)
        return G_EXPANDED_VARS_BYTES[index];
    index -= STAGE61_STATE_VARS_SIZE;
    if (index < STAGE61_STATE_LAST_BALL_SIZE)
        return G_LAST_USED_BALL_BYTES[index];
    index -= STAGE61_STATE_LAST_BALL_SIZE;
    if (index < STAGE61_STATE_COINS_SIZE)
        return G_PLAYER_COINS_BYTES[index];
    return 0u;
}

static u8 stage61_state_record_byte(u32 index, u32 crc)
{
    u32 value;

    if (index < 4u) {
        value = STAGE61_STATE_MAGIC;
        return (u8)(value >> (index * 8u));
    }
    if (index < 6u) {
        value = STAGE61_STATE_VERSION;
        return (u8)(value >> ((index - 4u) * 8u));
    }
    if (index < 8u) {
        value = STAGE61_STATE_PAYLOAD_SIZE;
        return (u8)(value >> ((index - 6u) * 8u));
    }
    if (index < 12u)
        return (u8)(crc >> ((index - 8u) * 8u));
    if (index < STAGE61_STATE_HEADER_SIZE) {
        value = ~crc;
        return (u8)(value >> ((index - 12u) * 8u));
    }
    return stage61_state_payload_byte(index - STAGE61_STATE_HEADER_SIZE);
}

static void stage61_state_store_record_byte(
    u32 index, u8 value, u8 header[STAGE61_STATE_HEADER_SIZE])
{
    if (index < STAGE61_STATE_HEADER_SIZE) {
        header[index] = value;
        return;
    }
    index -= STAGE61_STATE_HEADER_SIZE;
    if (index < STAGE61_STATE_FLAGS_SIZE) {
        G_EXPANDED_FLAGS[index] = value;
        return;
    }
    index -= STAGE61_STATE_FLAGS_SIZE;
    if (index < STAGE61_STATE_VARS_SIZE) {
        G_EXPANDED_VARS_BYTES[index] = value;
        return;
    }
    index -= STAGE61_STATE_VARS_SIZE;
    if (index < STAGE61_STATE_LAST_BALL_SIZE) {
        G_LAST_USED_BALL_BYTES[index] = value;
        return;
    }
    index -= STAGE61_STATE_LAST_BALL_SIZE;
    if (index < STAGE61_STATE_COINS_SIZE)
        G_PLAYER_COINS_BYTES[index] = value;
}

static u8 stage61_state_segment(
    u16 id, u16 size, u32 *record_start, u32 *length)
{
    if (id == 13u && size == 0x7D0u) {
        *record_start = 0u;
        *length = STAGE61_STATE_RECORD_SIZE;
        return 1u;
    }
    return 0u;
}

static void stage61_state_inject_tail(
    volatile u8 *section, u16 id, u16 size)
{
    u32 start;
    u32 length;
    u32 index;
    u32 crc;

    if (stage61_state_segment(id, size, &start, &length) == 0u)
        return;
    crc = stage61_state_crc();
    for (index = 0u; index < length; ++index)
        section[(u32)size + index] =
            stage61_state_record_byte(start + index, crc);
}

/* Reconstruct one prepared sector byte from its authoritative live owners.
 * This deliberately does not trust the flash driver's return value or the
 * staging buffer after ReadFlashSection has overwritten it.  The relation is
 * byte-exact for all 4096 bytes, including the stock-checksum-excluded S61E
 * tail and every footer byte. */
static u8 stage61_save_expected_prepared_byte(
    u16 id,
    u16 size,
    const volatile u8 *data,
    u32 counter,
    u32 record_crc,
    u16 checksum,
    u32 index,
    u8 signature_first_byte)
{
    u32 record_start;
    u32 record_length;
    u32 relative;

    if (index < size)
        return data[index];
    if (stage61_state_segment(
            id, size, &record_start, &record_length) != 0u
            && index >= size && index < (u32)size + record_length) {
        relative = index - size;
        return stage61_state_record_byte(
            record_start + relative, record_crc
        );
    }
    if (index == STAGE61_SAVE_ID_OFFSET)
        return (u8)id;
    if (index == STAGE61_SAVE_ID_OFFSET + 1u)
        return (u8)(id >> 8);
    if (index == STAGE61_SAVE_CHECKSUM_OFFSET)
        return (u8)checksum;
    if (index == STAGE61_SAVE_CHECKSUM_OFFSET + 1u)
        return (u8)(checksum >> 8);
    if (index >= STAGE61_SAVE_SIGNATURE_OFFSET
            && index < STAGE61_SAVE_SIGNATURE_OFFSET + 4u) {
        if (index == STAGE61_SAVE_SIGNATURE_OFFSET)
            return signature_first_byte;
        return (u8)(STAGE61_SAVE_SIGNATURE
            >> ((index - STAGE61_SAVE_SIGNATURE_OFFSET) * 8u));
    }
    if (index >= STAGE61_SAVE_COUNTER_OFFSET
            && index < STAGE61_SAVE_COUNTER_OFFSET + 4u)
        return (u8)(counter
            >> ((index - STAGE61_SAVE_COUNTER_OFFSET) * 8u));
    return 0u;
}

static u8 stage61_save_readback_matches_prepared(
    const volatile u8 *section,
    u16 id,
    u16 size,
    const volatile u8 *data,
    u32 counter,
    u32 record_crc,
    u8 signature_first_byte)
{
    u16 checksum;
    u32 index;

    if (section == (const volatile u8 *)0
            || data == (const volatile u8 *)0)
        return 0u;
    checksum = FN_SAVE_CHECKSUM((const void *)data, size);
    for (index = 0u; index < STAGE61_SAVE_SECTION_SIZE; ++index) {
        if (section[index] != stage61_save_expected_prepared_byte(
                id, size, data, counter, record_crc, checksum, index,
                signature_first_byte))
            return 0u;
    }
    return 1u;
}

static u8 stage61_state_tail_matches_live_crc(
    const volatile u8 *section, u16 id, u16 size, u32 crc)
{
    u32 start;
    u32 length;
    u32 index;

    if (section == (const volatile u8 *)0
            || stage61_state_segment(id, size, &start, &length) == 0u)
        return 0u;
    for (index = 0u; index < length; ++index) {
        if (section[(u32)size + index]
                != stage61_state_record_byte(start + index, crc))
            return 0u;
    }
    return 1u;
}

static u32 stage61_save_section_crc32(const volatile u8 *section)
{
    u32 crc = 0xFFFFFFFFu;
    u32 index;

    for (index = 0u; index < STAGE61_SAVE_SECTION_SIZE; ++index)
        crc = stage61_crc_byte(crc, section[index]);
    return crc ^ 0xFFFFFFFFu;
}

/* A callback can report success while the flash byte differs.  Merely setting
 * gDamagedSaveSectors is not persistent and therefore cannot stop a fresh
 * boot from selecting a checksum-valid generation whose reserved tail was
 * silently corrupted.  Make the inactive target generation physically
 * incomplete before returning an error.  Erase is preferred; programming a
 * zero signature byte is a second best-effort invalidation if erase itself
 * reports failure. */
static u8 stage61_save_reject_written_target_sector(
    EraseFlashSectorFn erase_sector,
    ProgramFlashByteFn program_byte,
    u8 target_sector)
{
    volatile u8 *section = G_FAST_SAVE_SECTION;

    stage61_save_mark_damaged(target_sector);
    if (section == (volatile u8 *)0)
        return STAGE61_SAVE_STATUS_ERROR;
    if (erase_sector != (EraseFlashSectorFn)0)
        (void)erase_sector(target_sector);
    (void)FN_READ_FLASH_SECTION(target_sector, (void *)section);
    if (stage61_read32(section + STAGE61_SAVE_SIGNATURE_OFFSET)
            != STAGE61_SAVE_SIGNATURE)
        return STAGE61_SAVE_STATUS_OK;
    if (program_byte != (ProgramFlashByteFn)0) {
        (void)program_byte(
            target_sector, STAGE61_SAVE_SIGNATURE_OFFSET, 0u
        );
        (void)FN_READ_FLASH_SECTION(target_sector, (void *)section);
    }
    return stage61_read32(section + STAGE61_SAVE_SIGNATURE_OFFSET)
            != STAGE61_SAVE_SIGNATURE
        ? STAGE61_SAVE_STATUS_OK : STAGE61_SAVE_STATUS_ERROR;
}

static void stage61_state_load_compatible_record(
    const struct Stage61SaveBlockChunk *chunks)
{
    u8 header[STAGE61_STATE_HEADER_SIZE];
    volatile u8 *section = G_FAST_SAVE_SECTION;
    u32 mask = 0u;
    u32 index;
    u8 physical;

    stage61_state_clear();
    for (index = 0u; index < STAGE61_STATE_HEADER_SIZE; ++index)
        header[index] = 0u;
    if (section == (volatile u8 *)0 || chunks == (const void *)0)
        return;

    physical = (u8)(STAGE61_SAVE_SLOT_SECTORS * (G_SAVE_COUNTER & 1u));
    for (index = 0u; index < STAGE61_SAVE_SLOT_SECTORS; ++index) {
        u16 id;
        u16 size;
        u32 start;
        u32 length;
        u32 copy_index;
        u8 bit;

        FN_READ_FLASH_SECTION((u8)(physical + index), (void *)section);
        id = stage61_read16(section + STAGE61_SAVE_ID_OFFSET);
        if (id >= STAGE61_SAVE_SLOT_SECTORS)
            continue;
        if (stage61_save_chunk_descriptor_is_valid(id, chunks) == 0u)
            continue;
        size = chunks[id].size;
        bit = stage61_state_segment(id, size, &start, &length);
        if (bit == 0u)
            continue;
        if (stage61_read32(section + STAGE61_SAVE_SIGNATURE_OFFSET)
                != STAGE61_SAVE_SIGNATURE
                || stage61_read32(section + STAGE61_SAVE_COUNTER_OFFSET)
                    != G_SAVE_COUNTER
                || stage61_read16(section + STAGE61_SAVE_CHECKSUM_OFFSET)
                    != FN_SAVE_CHECKSUM((const void *)section, size))
            continue;
        for (copy_index = 0u; copy_index < length; ++copy_index) {
            stage61_state_store_record_byte(
                start + copy_index,
                section[(u32)size + copy_index],
                header
            );
        }
        mask |= bit;
    }

    if (mask != 1u
            || stage61_read32(header) != STAGE61_STATE_MAGIC
            || stage61_read16(header + 4u) != STAGE61_STATE_VERSION
            || stage61_read16(header + 6u) != STAGE61_STATE_PAYLOAD_SIZE
            || stage61_read32(header + 12u) != ~stage61_read32(header + 8u)
            || stage61_state_crc() != stage61_read32(header + 8u))
        stage61_state_clear();
}

STAGE61_EXPORT(Stage61State_HandleWriteSector)
u8 Stage61State_HandleWriteSector(
    u16 id, const struct Stage61SaveBlockChunk *chunks)
{
    volatile u8 *section = G_FAST_SAVE_SECTION;
    volatile u8 *data;
    u16 size;
    u16 sector;
    u32 index;

    if (id >= STAGE61_SAVE_SLOT_SECTORS)
        return 0xFFu;
    sector = stage61_save_physical_sector_for_id(id);
    if (section == (volatile u8 *)0
            || chunks == (const void *)0
            || stage61_save_chunk_descriptor_is_valid(id, chunks) == 0u) {
        stage61_save_mark_damaged(sector);
        return 0xFFu;
    }
    data = chunks[id].data;
    size = chunks[id].size;
    if (data == (volatile u8 *)0 || size > STAGE61_SAVE_TAIL_END) {
        stage61_save_mark_damaged(sector);
        return 0xFFu;
    }

    for (index = 0u; index < STAGE61_SAVE_SECTION_SIZE; ++index)
        section[index] = 0u;
    stage61_write16(section + STAGE61_SAVE_ID_OFFSET, id);
    stage61_write32(
        section + STAGE61_SAVE_SIGNATURE_OFFSET, STAGE61_SAVE_SIGNATURE
    );
    stage61_write32(
        section + STAGE61_SAVE_COUNTER_OFFSET, G_SAVE_COUNTER
    );
    for (index = 0u; index < size; ++index)
        section[index] = data[index];
    stage61_write16(
        section + STAGE61_SAVE_CHECKSUM_OFFSET,
        FN_SAVE_CHECKSUM((const void *)data, size)
    );
    stage61_state_inject_tail(section, id, size);
    return FN_TRY_WRITE_SECTOR((u8)sector, (u8 *)section);
}

/* LinkFullSave deliberately rewrites logical chunk 13 without programming
 * the first signature byte until every peer reaches the commit barrier.  Keep
 * that atomicity contract while adding the Stage61 record to the same image;
 * calling TryWriteSector here would make the sector valid too early. */
STAGE61_EXPORT(Stage61State_HandleReplaceSector)
u8 Stage61State_HandleReplaceSector(
    u16 id, const struct Stage61SaveBlockChunk *chunks)
{
    volatile u8 *section = G_FAST_SAVE_SECTION;
    volatile u8 *data;
    EraseFlashSectorFn erase_sector = G_ERASE_FLASH_SECTOR;
    ProgramFlashByteFn program_byte = G_PROGRAM_FLASH_BYTE;
    u16 size;
    u16 sector;
    u32 record_crc;
    u32 index;

    if (id >= STAGE61_SAVE_SLOT_SECTORS)
        return 0xFFu;
    sector = stage61_save_physical_sector_for_id(id);
    if (section == (volatile u8 *)0
            || chunks == (const void *)0
            || erase_sector == (EraseFlashSectorFn)0
            || program_byte == (ProgramFlashByteFn)0
            || stage61_save_chunk_descriptor_is_valid(id, chunks) == 0u) {
        stage61_save_mark_damaged(sector);
        return 0xFFu;
    }
    data = chunks[id].data;
    size = chunks[id].size;
    if (data == (volatile u8 *)0 || size > STAGE61_SAVE_TAIL_END) {
        stage61_save_mark_damaged(sector);
        return 0xFFu;
    }

    for (index = 0u; index < STAGE61_SAVE_SECTION_SIZE; ++index)
        section[index] = 0u;
    stage61_write16(section + STAGE61_SAVE_ID_OFFSET, id);
    stage61_write32(
        section + STAGE61_SAVE_SIGNATURE_OFFSET, STAGE61_SAVE_SIGNATURE
    );
    stage61_write32(
        section + STAGE61_SAVE_COUNTER_OFFSET, G_SAVE_COUNTER
    );
    for (index = 0u; index < size; ++index)
        section[index] = data[index];
    stage61_write16(
        section + STAGE61_SAVE_CHECKSUM_OFFSET,
        FN_SAVE_CHECKSUM((const void *)data, size)
    );
    record_crc = stage61_state_crc();
    stage61_state_inject_tail(section, id, size);

    if (erase_sector(sector) != 0u) {
        stage61_save_mark_damaged(sector);
        return 0xFFu;
    }
    for (index = 0u; index < STAGE61_SAVE_SIGNATURE_OFFSET; ++index) {
        if (program_byte(sector, index, section[index]) != 0u) {
            stage61_save_mark_damaged(sector);
            return 0xFFu;
        }
    }
    for (index = STAGE61_SAVE_SIGNATURE_OFFSET + 1u;
         index < STAGE61_SAVE_SECTION_SIZE; ++index) {
        if (program_byte(sector, index, section[index]) != 0u) {
            stage61_save_mark_damaged(sector);
            return 0xFFu;
        }
    }
    /* LinkFull commits signature byte 0 in a later barrier.  Until then, the
     * exact prepared image must be present with only that byte erased.  A
     * callback's zero return is never treated as evidence of persistence. */
    (void)FN_READ_FLASH_SECTION((u8)sector, (void *)section);
    if (stage61_save_readback_matches_prepared(
            section, id, size, data, G_SAVE_COUNTER, record_crc, 0xFFu)
            == 0u) {
        (void)stage61_save_reject_written_target_sector(
            erase_sector, program_byte, (u8)sector
        );
        return 0xFFu;
    }
    stage61_save_clear_damaged(sector);
    return 1u;
}

/* Stock CommitSectorSignatureByte trusts ProgramFlashByte's u16 return and
 * clears gDamagedSaveSectors without reading media.  Replace that barrier so
 * the complete 4096-byte image is reconstructed from the live chunk owner and
 * compared after signature commit.  ``one_based_id`` is the stock ABI used by
 * HandleReplaceSector's callers. */
STAGE61_EXPORT(Stage61State_CommitSignatureByte)
u8 Stage61State_CommitSignatureByte(
    u16 one_based_id, const struct Stage61SaveBlockChunk *chunks)
{
    volatile u8 *section = G_FAST_SAVE_SECTION;
    ProgramFlashByteFn program_byte = G_PROGRAM_FLASH_BYTE;
    EraseFlashSectorFn erase_sector = G_ERASE_FLASH_SECTOR;
    u16 id;
    u16 size;
    u16 sector;
    u32 record_crc;

    if (one_based_id == 0u || one_based_id > STAGE61_SAVE_SLOT_SECTORS
            || section == (volatile u8 *)0
            || program_byte == (ProgramFlashByteFn)0
            || erase_sector == (EraseFlashSectorFn)0)
        return stage61_save_fail_with_sector(
            stage61_save_physical_sector_for_id(13u)
        );
    id = (u16)(one_based_id - 1u);
    sector = stage61_save_physical_sector_for_id(id);
    if (stage61_save_chunk_descriptor_is_valid(id, chunks) == 0u)
        return stage61_save_fail_with_sector(sector);
    size = chunks[id].size;
    record_crc = stage61_state_crc();

    stage61_save_mark_damaged(sector);
    if (program_byte(
            sector, STAGE61_SAVE_SIGNATURE_OFFSET,
            (u8)STAGE61_SAVE_SIGNATURE) != 0u)
        return STAGE61_SAVE_STATUS_ERROR;
    (void)FN_READ_FLASH_SECTION((u8)sector, (void *)section);
    if (stage61_save_readback_matches_prepared(
            section, id, size, chunks[id].data, G_SAVE_COUNTER,
            record_crc, (u8)STAGE61_SAVE_SIGNATURE) == 0u) {
        (void)stage61_save_reject_written_target_sector(
            erase_sector, program_byte, (u8)sector
        );
        return STAGE61_SAVE_STATUS_ERROR;
    }
    stage61_save_clear_damaged(sector);
    return STAGE61_SAVE_STATUS_OK;
}

/* Copy one exact sector from the selected generation into the inactive slot.
 * The target footer uses the next counter, and its first signature byte is
 * programmed only after every other byte.  A torn target sector is therefore
 * never accepted as part of the new generation.  The source sector is only
 * read and is never erased by this transaction.
 */
static u8 stage61_save_clone_record_sector(
    const struct Stage61SaveBlockChunk *chunks,
    const struct Stage61SaveSlotValidation *selected,
    u16 id,
    u8 source_base,
    u8 target_base,
    u32 target_counter,
    u8 inject_record,
    u32 *expected_crc_out,
    u8 *expected_live_record_out)
{
    volatile u8 *section = G_FAST_SAVE_SECTION;
    EraseFlashSectorFn erase_sector = G_ERASE_FLASH_SECTOR;
    ProgramFlashByteFn program_byte = G_PROGRAM_FLASH_BYTE;
    u8 source_sector;
    u8 target_sector;
    u16 size;
    u32 expected_section_crc;
    u32 live_record_crc;
    u8 expected_live_record;
    u32 index;

    if (section == (volatile u8 *)0
            || erase_sector == (EraseFlashSectorFn)0
            || program_byte == (ProgramFlashByteFn)0
            || selected == (const void *)0
            || id >= STAGE61_SAVE_SLOT_SECTORS
            || selected->physical_by_id[id] >= STAGE61_SAVE_SLOT_SECTORS
            || stage61_save_chunk_descriptor_is_valid(id, chunks) == 0u
            || expected_crc_out == (u32 *)0
            || expected_live_record_out == (u8 *)0)
        return STAGE61_SAVE_STATUS_ERROR;

    source_sector = (u8)(source_base + selected->physical_by_id[id]);
    target_sector = (u8)(target_base + selected->physical_by_id[id]);
    if (source_base == target_base || source_sector == target_sector) {
        stage61_save_mark_damaged(target_sector);
        return STAGE61_SAVE_STATUS_ERROR;
    }

    (void)FN_READ_FLASH_SECTION(source_sector, (void *)section);
    size = sStage61SaveChunkSizes[id];
    if (stage61_read16(section + STAGE61_SAVE_ID_OFFSET) != id
            || stage61_read32(section + STAGE61_SAVE_SIGNATURE_OFFSET)
                != STAGE61_SAVE_SIGNATURE
            || stage61_read32(section + STAGE61_SAVE_COUNTER_OFFSET)
                != selected->counter
            || stage61_read16(section + STAGE61_SAVE_CHECKSUM_OFFSET)
                != FN_SAVE_CHECKSUM((const void *)section, size)) {
        stage61_save_mark_damaged(target_sector);
        return STAGE61_SAVE_STATUS_ERROR;
    }

    stage61_write32(
        section + STAGE61_SAVE_COUNTER_OFFSET, target_counter
    );
    if (inject_record != 0u && id == 13u)
        stage61_state_inject_tail(section, id, size);
    live_record_crc = stage61_state_crc();
    expected_live_record = (u8)(id == 13u
        && stage61_state_tail_matches_live_crc(
            section, id, size, live_record_crc) != 0u);
    expected_section_crc = stage61_save_section_crc32(section);

    if (erase_sector(target_sector) != 0u) {
        stage61_save_mark_damaged(target_sector);
        return STAGE61_SAVE_STATUS_ERROR;
    }
    for (index = 0u; index < STAGE61_SAVE_SIGNATURE_OFFSET; ++index) {
        if (program_byte(target_sector, index, section[index]) != 0u) {
            stage61_save_mark_damaged(target_sector);
            return STAGE61_SAVE_STATUS_ERROR;
        }
    }
    for (index = STAGE61_SAVE_SIGNATURE_OFFSET + 1u;
         index < STAGE61_SAVE_SECTION_SIZE; ++index) {
        if (program_byte(target_sector, index, section[index]) != 0u) {
            stage61_save_mark_damaged(target_sector);
            return STAGE61_SAVE_STATUS_ERROR;
        }
    }
    if (program_byte(
            target_sector,
            STAGE61_SAVE_SIGNATURE_OFFSET,
            section[STAGE61_SAVE_SIGNATURE_OFFSET]) != 0u) {
        stage61_save_mark_damaged(target_sector);
        return STAGE61_SAVE_STATUS_ERROR;
    }

    /* Signature-last is a commit protocol only when the committed bytes are
     * actually what was prepared.  Re-read the whole 4096-byte sector before
     * clearing the damaged bit; stock checksum alone excludes the reserved
     * tail that owns S61E. */
    (void)FN_READ_FLASH_SECTION(target_sector, (void *)section);
    if (stage61_save_section_crc32(section) != expected_section_crc
            || stage61_read16(section + STAGE61_SAVE_ID_OFFSET) != id
            || stage61_read32(section + STAGE61_SAVE_SIGNATURE_OFFSET)
                != STAGE61_SAVE_SIGNATURE
            || stage61_read32(section + STAGE61_SAVE_COUNTER_OFFSET)
                != target_counter
            || stage61_read16(section + STAGE61_SAVE_CHECKSUM_OFFSET)
                != FN_SAVE_CHECKSUM((const void *)section, size)
            || (expected_live_record != 0u
                && stage61_state_tail_matches_live_crc(
                    section, id, size, live_record_crc) == 0u)) {
        (void)stage61_save_reject_written_target_sector(
            erase_sector, program_byte, target_sector
        );
        return STAGE61_SAVE_STATUS_ERROR;
    }
    *expected_crc_out = expected_section_crc;
    *expected_live_record_out = expected_live_record;
    stage61_save_clear_damaged(target_sector);
    return STAGE61_SAVE_STATUS_OK;
}

/* Materialize and read-validate a complete alternate generation before the
 * caller is allowed to promote it.  The source remains the sole authority
 * until all fourteen target signatures and the full-mask validation pass. */
static u8 stage61_save_clone_complete_generation(
    const struct Stage61SaveBlockChunk *chunks,
    const struct Stage61SaveSlotValidation *selected,
    u8 source_base,
    u8 target_base,
    u32 target_counter,
    u8 inject_record)
{
    struct Stage61SaveSlotValidation written;
    u32 expected_crc[STAGE61_SAVE_SLOT_SECTORS];
    u8 expected_live_record[STAGE61_SAVE_SLOT_SECTORS];
    volatile u8 *section = G_FAST_SAVE_SECTION;
    EraseFlashSectorFn erase_sector = G_ERASE_FLASH_SECTOR;
    ProgramFlashByteFn program_byte = G_PROGRAM_FLASH_BYTE;
    u16 id;

    if (selected == (const void *)0
            || selected->status != STAGE61_SAVE_STATUS_OK
            || selected->valid_mask != STAGE61_SAVE_FULL_MASK
            || selected->counter + 1u != target_counter
            || source_base == target_base
            || target_base != (u8)(
                STAGE61_SAVE_SLOT_SECTORS * (target_counter & 1u))
            || section == (volatile u8 *)0
            || erase_sector == (EraseFlashSectorFn)0
            || program_byte == (ProgramFlashByteFn)0)
        return STAGE61_SAVE_STATUS_ERROR;

    /* id13 is deliberately final: a complete target generation can never
     * exist without its copied/updated S61E record-bearing sector. */
    for (id = 0u; id < STAGE61_SAVE_SLOT_SECTORS; ++id) {
        if (stage61_save_clone_record_sector(
                chunks, selected, id, source_base, target_base,
                target_counter, inject_record,
                &expected_crc[id], &expected_live_record[id])
                != STAGE61_SAVE_STATUS_OK)
            return STAGE61_SAVE_STATUS_ERROR;
    }
    stage61_save_validate_slot(target_base, chunks, &written);
    if (written.status != STAGE61_SAVE_STATUS_OK
            || written.counter != target_counter
            || written.valid_mask != STAGE61_SAVE_FULL_MASK
            || written.first_save_sector != selected->first_save_sector) {
        (void)stage61_save_reject_written_target_sector(
            erase_sector, program_byte,
            (u8)(target_base + selected->physical_by_id[13])
        );
        return STAGE61_SAVE_STATUS_ERROR;
    }

    /* A later callback must not be able to corrupt a sector that was already
     * individually verified.  Re-read all fourteen target sectors after the
     * complete-generation validator, bind each full image to the CRC prepared
     * from its source, and explicitly re-check a live S61E record. */
    for (id = 0u; id < STAGE61_SAVE_SLOT_SECTORS; ++id) {
        u8 target_sector = (u8)(
            target_base + written.physical_by_id[id]
        );
        u16 size = sStage61SaveChunkSizes[id];

        if (written.physical_by_id[id] != selected->physical_by_id[id]) {
            (void)stage61_save_reject_written_target_sector(
                erase_sector, program_byte, target_sector
            );
            return STAGE61_SAVE_STATUS_ERROR;
        }
        (void)FN_READ_FLASH_SECTION(target_sector, (void *)section);
        if (stage61_save_section_crc32(section) != expected_crc[id]
                || stage61_read16(section + STAGE61_SAVE_ID_OFFSET) != id
                || stage61_read32(section + STAGE61_SAVE_SIGNATURE_OFFSET)
                    != STAGE61_SAVE_SIGNATURE
                || stage61_read32(section + STAGE61_SAVE_COUNTER_OFFSET)
                    != target_counter
                || stage61_read16(section + STAGE61_SAVE_CHECKSUM_OFFSET)
                    != FN_SAVE_CHECKSUM((const void *)section, size)
                || (expected_live_record[id] != 0u
                    && stage61_state_tail_matches_live_crc(
                        section, id, size, stage61_state_crc()) == 0u)) {
            (void)stage61_save_reject_written_target_sector(
                erase_sector, program_byte, target_sector
            );
            return STAGE61_SAVE_STATUS_ERROR;
        }
    }
    return STAGE61_SAVE_STATUS_OK;
}

/* Resolve a protected complete generation without mutating the live selector.
 * A normal save writes only the opposite physical bank, so even a callback
 * failure after a real erase can never enter FireRed's bad-sector replacement
 * path and consume a sector from this authority.  With no complete generation
 * (a genuinely new or already-corrupt file), the caller may still create the
 * first complete generation, but there is necessarily no old state to retain.
 */
static u8 stage61_save_choose_protected_generation(
    const struct Stage61SaveBlockChunk *chunks,
    struct Stage61SaveSlotValidation *selected,
    u8 *selected_base)
{
    struct Stage61SaveSlotValidation first;
    struct Stage61SaveSlotValidation second;

    if (selected == (void *)0 || selected_base == (void *)0)
        return 0u;
    stage61_save_validate_slot(0u, chunks, &first);
    stage61_save_validate_slot(
        STAGE61_SAVE_SLOT_SECTORS, chunks, &second
    );
    *selected_base = 0xFFu;
    if (first.status == STAGE61_SAVE_STATUS_OK
            && second.status == STAGE61_SAVE_STATUS_OK) {
        *selected_base = stage61_save_second_counter_is_newer(
                first.counter, second.counter)
            ? STAGE61_SAVE_SLOT_SECTORS : 0u;
    } else if (first.status == STAGE61_SAVE_STATUS_OK) {
        *selected_base = 0u;
    } else if (second.status == STAGE61_SAVE_STATUS_OK) {
        *selected_base = STAGE61_SAVE_SLOT_SECTORS;
    } else {
        return 0u;
    }
    /* Re-read the selected bank rather than copying a stack struct.  This also
     * binds the decision to the flash image immediately before the first
     * destructive target-bank callback. */
    stage61_save_validate_slot(*selected_base, chunks, selected);
    return (u8)(selected->status == STAGE61_SAVE_STATUS_OK
        && selected->valid_mask == STAGE61_SAVE_FULL_MASK);
}

/* Remove the record-bearing sector from the target generation before any
 * other sector is touched.  Keep its damaged bit set until id13 is committed
 * last.  Unlike the generic best-effort reject helper, a callback-reported
 * failure is still an operation failure even when the physical erase happened;
 * this is required for the real SaveFailed UI and its retry transaction.
 */
static u8 stage61_save_invalidate_normal_target_record(u8 target_sector)
{
    volatile u8 *section = G_FAST_SAVE_SECTION;
    EraseFlashSectorFn erase_sector = G_ERASE_FLASH_SECTOR;
    ProgramFlashByteFn program_byte = G_PROGRAM_FLASH_BYTE;
    u16 erase_status;
    u16 program_status = 0u;

    stage61_save_mark_damaged(target_sector);
    if (section == (volatile u8 *)0
            || erase_sector == (EraseFlashSectorFn)0
            || program_byte == (ProgramFlashByteFn)0)
        return STAGE61_SAVE_STATUS_ERROR;
    erase_status = erase_sector(target_sector);
    (void)FN_READ_FLASH_SECTION(target_sector, (void *)section);
    if (stage61_read32(section + STAGE61_SAVE_SIGNATURE_OFFSET)
            == STAGE61_SAVE_SIGNATURE) {
        program_status = program_byte(
            target_sector, STAGE61_SAVE_SIGNATURE_OFFSET, 0u
        );
        (void)FN_READ_FLASH_SECTION(target_sector, (void *)section);
    }
    if (erase_status != 0u || program_status != 0u
            || stage61_read32(section + STAGE61_SAVE_SIGNATURE_OFFSET)
                == STAGE61_SAVE_SIGNATURE)
        return STAGE61_SAVE_STATUS_ERROR;
    return STAGE61_SAVE_STATUS_OK;
}

/* Build one normal-save sector from the live SaveBlock owners and commit its
 * first signature byte last.  No stock TryWriteSector call is made: its error
 * fallback can erase a sector in the protected bank.  Every successful return
 * is instead based on a full 4096-byte readback, including the checksum-
 * excluded S61E tail and footer.
 */
static u8 stage61_save_write_normal_live_sector(
    const struct Stage61SaveBlockChunk *chunks,
    u16 id,
    u8 target_base,
    u8 target_first_sector,
    u32 target_counter)
{
    volatile u8 *section = G_FAST_SAVE_SECTION;
    volatile u8 *data;
    EraseFlashSectorFn erase_sector = G_ERASE_FLASH_SECTOR;
    ProgramFlashByteFn program_byte = G_PROGRAM_FLASH_BYTE;
    u8 target_sector;
    u16 size;
    u16 checksum;
    u32 record_crc;
    u32 index;

    if (id >= STAGE61_SAVE_SLOT_SECTORS)
        return STAGE61_SAVE_STATUS_ERROR;
    target_sector = (u8)(target_base
        + (u8)((target_first_sector + id) % STAGE61_SAVE_SLOT_SECTORS));
    if (section == (volatile u8 *)0
            || erase_sector == (EraseFlashSectorFn)0
            || program_byte == (ProgramFlashByteFn)0
            || stage61_save_chunk_descriptor_is_valid(id, chunks) == 0u) {
        stage61_save_mark_damaged(target_sector);
        return STAGE61_SAVE_STATUS_ERROR;
    }
    data = chunks[id].data;
    size = chunks[id].size;
    checksum = FN_SAVE_CHECKSUM((const void *)data, size);
    record_crc = stage61_state_crc();

    for (index = 0u; index < STAGE61_SAVE_SECTION_SIZE; ++index)
        section[index] = 0u;
    for (index = 0u; index < size; ++index)
        section[index] = data[index];
    stage61_write16(section + STAGE61_SAVE_ID_OFFSET, id);
    stage61_write16(section + STAGE61_SAVE_CHECKSUM_OFFSET, checksum);
    stage61_write32(
        section + STAGE61_SAVE_SIGNATURE_OFFSET, STAGE61_SAVE_SIGNATURE
    );
    stage61_write32(
        section + STAGE61_SAVE_COUNTER_OFFSET, target_counter
    );
    stage61_state_inject_tail(section, id, size);

    stage61_save_mark_damaged(target_sector);
    if (erase_sector(target_sector) != 0u)
        return STAGE61_SAVE_STATUS_ERROR;
    for (index = 0u; index < STAGE61_SAVE_SIGNATURE_OFFSET; ++index) {
        if (program_byte(target_sector, index, section[index]) != 0u)
            return STAGE61_SAVE_STATUS_ERROR;
    }
    for (index = STAGE61_SAVE_SIGNATURE_OFFSET + 1u;
         index < STAGE61_SAVE_SECTION_SIZE; ++index) {
        if (program_byte(target_sector, index, section[index]) != 0u)
            return STAGE61_SAVE_STATUS_ERROR;
    }
    if (program_byte(
            target_sector,
            STAGE61_SAVE_SIGNATURE_OFFSET,
            (u8)STAGE61_SAVE_SIGNATURE) != 0u) {
        (void)stage61_save_reject_written_target_sector(
            erase_sector, program_byte, target_sector
        );
        return STAGE61_SAVE_STATUS_ERROR;
    }

    (void)FN_READ_FLASH_SECTION(target_sector, (void *)section);
    if (stage61_save_readback_matches_prepared(
            section, id, size, data, target_counter, record_crc,
            (u8)STAGE61_SAVE_SIGNATURE) == 0u) {
        (void)stage61_save_reject_written_target_sector(
            erase_sector, program_byte, target_sector
        );
        return STAGE61_SAVE_STATUS_ERROR;
    }
    stage61_save_clear_damaged(target_sector);
    return STAGE61_SAVE_STATUS_OK;
}

/* SAVE_NORMAL copy-on-write transaction.  UpdateSaveAddresses and
 * SaveSerializedGame retain the exact stock pre-write semantics, but the
 * destructive writer is owned here.  id13 is the pre-invalidated final commit
 * sector; selector globals advance only after all fourteen full images and
 * their rotation have been independently re-read.
 */
static __attribute__((noinline))
u8 stage61_save_normal_copy_on_write(void)
{
    struct Stage61SaveBlockChunk live_chunks[STAGE61_SAVE_SLOT_SECTORS];
    struct Stage61SaveSlotValidation protected;
    struct Stage61SaveSlotValidation written;
    volatile u8 *section = G_FAST_SAVE_SECTION;
    EraseFlashSectorFn erase_sector = G_ERASE_FLASH_SECTOR;
    ProgramFlashByteFn program_byte = G_PROGRAM_FLASH_BYTE;
    u8 protected_base;
    u8 target_base;
    u8 target_first_sector;
    u8 target_record_sector;
    u8 has_protected;
    u16 original_first_sector;
    u16 rollback_first_sector;
    u16 source_first_sector;
    u16 id;
    u32 original_counter;
    u32 rollback_counter;
    u32 source_counter;
    u32 target_counter;
    u32 record_crc;

    original_counter = G_SAVE_COUNTER;
    original_first_sector = G_FIRST_SAVE_SECTOR;
    FN_UPDATE_SAVE_ADDRESSES();
    FN_SAVE_SERIALIZED_GAME();
    if (section == (volatile u8 *)0
            || stage61_save_range_is_permitted(
                section, STAGE61_SAVE_SECTION_SIZE) == 0u
            || erase_sector == (EraseFlashSectorFn)0
            || program_byte == (ProgramFlashByteFn)0
            || stage61_save_build_live_descriptors(live_chunks) == 0u)
        return stage61_save_fail_with_sector(
            (u16)(STAGE61_SAVE_SLOT_SECTORS
                * ((G_SAVE_COUNTER + 1u) & 1u))
        );

    has_protected = stage61_save_choose_protected_generation(
        live_chunks, &protected, &protected_base
    );
    if (has_protected != 0u) {
        source_counter = protected.counter;
        source_first_sector = protected.first_save_sector;
        rollback_counter = protected.counter;
        rollback_first_sector = protected.first_save_sector;
    } else {
        source_counter = original_counter;
        source_first_sector = (u16)(
            original_first_sector % STAGE61_SAVE_SLOT_SECTORS
        );
        rollback_counter = original_counter;
        rollback_first_sector = original_first_sector;
    }
    target_counter = source_counter + 1u;
    target_base = (u8)(
        STAGE61_SAVE_SLOT_SECTORS * (target_counter & 1u)
    );
    target_first_sector = (u8)(
        (source_first_sector + 1u) % STAGE61_SAVE_SLOT_SECTORS
    );
    target_record_sector = (u8)(target_base
        + (u8)((target_first_sector + 13u)
            % STAGE61_SAVE_SLOT_SECTORS));
    if (has_protected != 0u && target_base == protected_base) {
        G_SAVE_COUNTER = rollback_counter;
        G_FIRST_SAVE_SECTOR = rollback_first_sector;
        return stage61_save_fail_with_sector(target_record_sector);
    }

    if (stage61_save_invalidate_normal_target_record(
            target_record_sector) != STAGE61_SAVE_STATUS_OK) {
        G_SAVE_COUNTER = rollback_counter;
        G_FIRST_SAVE_SECTOR = rollback_first_sector;
        return STAGE61_SAVE_STATUS_ERROR;
    }
    for (id = 0u; id < STAGE61_SAVE_SLOT_SECTORS; ++id) {
        if (stage61_save_write_normal_live_sector(
                live_chunks, id, target_base, target_first_sector,
                target_counter) != STAGE61_SAVE_STATUS_OK) {
            (void)stage61_save_reject_written_target_sector(
                erase_sector, program_byte, target_record_sector
            );
            G_SAVE_COUNTER = rollback_counter;
            G_FIRST_SAVE_SECTOR = rollback_first_sector;
            return STAGE61_SAVE_STATUS_ERROR;
        }
    }

    stage61_save_validate_slot(target_base, live_chunks, &written);
    if (written.status != STAGE61_SAVE_STATUS_OK
            || written.counter != target_counter
            || written.valid_mask != STAGE61_SAVE_FULL_MASK
            || written.first_save_sector != target_first_sector) {
        (void)stage61_save_reject_written_target_sector(
            erase_sector, program_byte, target_record_sector
        );
        G_SAVE_COUNTER = rollback_counter;
        G_FIRST_SAVE_SECTOR = rollback_first_sector;
        return STAGE61_SAVE_STATUS_ERROR;
    }

    record_crc = stage61_state_crc();
    for (id = 0u; id < STAGE61_SAVE_SLOT_SECTORS; ++id) {
        u8 physical = (u8)(target_base + written.physical_by_id[id]);
        u16 size = live_chunks[id].size;

        if (written.physical_by_id[id]
                != (u8)((target_first_sector + id)
                    % STAGE61_SAVE_SLOT_SECTORS)) {
            (void)stage61_save_reject_written_target_sector(
                erase_sector, program_byte, target_record_sector
            );
            G_SAVE_COUNTER = rollback_counter;
            G_FIRST_SAVE_SECTOR = rollback_first_sector;
            return STAGE61_SAVE_STATUS_ERROR;
        }
        (void)FN_READ_FLASH_SECTION(physical, (void *)section);
        if (stage61_save_readback_matches_prepared(
                section, id, size, live_chunks[id].data,
                target_counter, record_crc,
                (u8)STAGE61_SAVE_SIGNATURE) == 0u) {
            (void)stage61_save_reject_written_target_sector(
                erase_sector, program_byte, target_record_sector
            );
            G_SAVE_COUNTER = rollback_counter;
            G_FIRST_SAVE_SECTOR = rollback_first_sector;
            return STAGE61_SAVE_STATUS_ERROR;
        }
    }

    G_SAVE_COUNTER = target_counter;
    G_FIRST_SAVE_SECTOR = target_first_sector;
    return STAGE61_SAVE_STATUS_OK;
}

/* SAVE_LINK's stock implementation updates logical ids 0..4 in place.  A
 * system with only one complete generation would therefore lose every valid
 * save if power failed during the first erase.  Resolve the newest complete
 * flash generation first (also recovering an immediate retry after a torn
 * stock phase), then always refresh the opposite bank as counter+1 exact old
 * data before entering stock.
 *
 * Deliberately do NOT promote G_SAVE_COUNTER here.  Stock must update the
 * selected counter-c source in place while the counter-c+1 exact old clone is
 * the boot selector's protected generation.  A power loss after any stock
 * callback therefore loads the entirely old backup, never a mixed source.
 * No current RAM extension record is injected during this safety clone. */
STAGE61_EXPORT(Stage61State_EnsureBackupGeneration)
u8 Stage61State_EnsureBackupGeneration(
    const struct Stage61SaveBlockChunk *chunks)
{
    struct Stage61SaveSlotValidation source;
    u8 source_base;
    u8 backup_base;
    u8 selection_status;
    u32 source_counter;
    u32 backup_counter;
    u8 failure_sector = (u8)(
        STAGE61_SAVE_SLOT_SECTORS * ((G_SAVE_COUNTER + 1u) & 1u)
    );

    if (stage61_save_all_descriptors_are_valid(chunks) == 0u)
        return stage61_save_fail_with_sector(failure_sector);
    selection_status = stage61_save_select_generation(chunks, &source_base);
    /* With one valid and one malformed bank the public stock-compatible
     * status is ERROR, but selected_base still identifies the fully validated
     * authority.  It is safe and necessary to rebuild the malformed bank. */
    if (source_base == 0xFFu
            || (selection_status != STAGE61_SAVE_STATUS_OK
                && selection_status != STAGE61_SAVE_STATUS_ERROR))
        return stage61_save_fail_with_sector(failure_sector);
    source_counter = G_SAVE_COUNTER;
    backup_counter = source_counter + 1u;
    backup_base = (u8)(
        STAGE61_SAVE_SLOT_SECTORS * (backup_counter & 1u)
    );
    if (source_base == backup_base)
        return stage61_save_fail_with_sector(backup_base);
    stage61_save_validate_slot(source_base, chunks, &source);
    if (source.status != STAGE61_SAVE_STATUS_OK
            || source.counter != source_counter
            || source.valid_mask != STAGE61_SAVE_FULL_MASK)
        return stage61_save_fail_with_sector(backup_base);

    if (stage61_save_clone_complete_generation(
            chunks, &source, source_base, backup_base,
            backup_counter, 0u) != STAGE61_SAVE_STATUS_OK)
        return stage61_save_fail_with_sector(backup_base);
    /* Keep source_counter authoritative in RAM.  The c+1 clone is intentionally
     * newer only to a fresh boot selector while stock mutates source c. */
    G_SAVE_COUNTER = source_counter;
    G_FIRST_SAVE_SECTOR = source.first_save_sector;
    return STAGE61_SAVE_STATUS_OK;
}

/* Keep the 112-byte live descriptor snapshot out of the stock save call's
 * stack lifetime.  This helper returns before HandleSavingData starts its own
 * deep flash-programming call chain. */
static __attribute__((noinline))
u8 stage61_save_ensure_live_backup_generation(void)
{
    struct Stage61SaveBlockChunk live_chunks[STAGE61_SAVE_SLOT_SECTORS];

    if (stage61_save_build_live_descriptors(live_chunks) == 0u)
        return STAGE61_SAVE_STATUS_ERROR;
    return Stage61State_EnsureBackupGeneration(live_chunks);
}

/* Before post-stock copy-on-write, make the protected old c+1 bank impossible
 * to validate as a temporarily mixed generation.  Erasing only its id13
 * record-bearing sector removes the full-mask generation.  The source c bank
 * is already a complete stock result, so every interruption from this point
 * selects source c until id13 is committed last by the full clone. */
static u8 stage61_save_invalidate_target_record_sector(
    const struct Stage61SaveSlotValidation *selected,
    u8 source_base,
    u8 target_base)
{
    EraseFlashSectorFn erase_sector = G_ERASE_FLASH_SECTOR;
    ProgramFlashByteFn program_byte = G_PROGRAM_FLASH_BYTE;
    u8 target_sector;

    if (erase_sector == (EraseFlashSectorFn)0
            || program_byte == (ProgramFlashByteFn)0
            || selected == (const void *)0
            || selected->status != STAGE61_SAVE_STATUS_OK
            || selected->physical_by_id[13] >= STAGE61_SAVE_SLOT_SECTORS
            || source_base == target_base)
        return STAGE61_SAVE_STATUS_ERROR;
    target_sector = (u8)(target_base + selected->physical_by_id[13]);
    /* A flash driver may report erase success without changing media.  The
     * full-generation clone must not start until the newer old target can no
     * longer validate, so use the same physical readback and signature-byte
     * fallback as every other rejected target sector. */
    return stage61_save_reject_written_target_sector(
        erase_sector, program_byte, target_sector
    );
}

/* Stock SAVE_LINK has already committed ids 0..4 in source generation c,
 * while id13 still contains the exact-old S61E tail.  Do not build id13 from
 * current PokemonStorage RAM: that would silently turn SAVE_LINK into a full
 * storage save.  Read the source flash sector, preserve all stock and reserved
 * bytes, replace only its checksum-excluded S61E record, then commit the first
 * signature byte last.  The exact-old c+1 backup remains complete throughout
 * this in-place rewrite, so every injected failure selects a coherent old
 * generation rather than the stock-new/S61E-old hybrid source.
 *
 * A full-sector CRC readback proves the reserved tail and stock payload were
 * retained; the stock checksum/footer and every live S61E byte are checked
 * independently before the old backup may be invalidated. */
static u8 stage61_save_rewrite_source_record_sector(
    const struct Stage61SaveBlockChunk *chunks,
    const struct Stage61SaveSlotValidation *selected,
    u8 source_base)
{
    volatile u8 *section = G_FAST_SAVE_SECTION;
    EraseFlashSectorFn erase_sector = G_ERASE_FLASH_SECTOR;
    ProgramFlashByteFn program_byte = G_PROGRAM_FLASH_BYTE;
    u8 source_sector;
    u16 size;
    u32 record_crc;
    u32 expected_section_crc;
    u32 index;

    if (section == (volatile u8 *)0
            || erase_sector == (EraseFlashSectorFn)0
            || program_byte == (ProgramFlashByteFn)0
            || selected == (const void *)0
            || selected->status != STAGE61_SAVE_STATUS_OK
            || selected->counter != G_SAVE_COUNTER
            || selected->valid_mask != STAGE61_SAVE_FULL_MASK
            || selected->physical_by_id[13] >= STAGE61_SAVE_SLOT_SECTORS
            || stage61_save_chunk_descriptor_is_valid(13u, chunks) == 0u)
        return STAGE61_SAVE_STATUS_ERROR;

    source_sector = (u8)(source_base + selected->physical_by_id[13]);
    size = sStage61SaveChunkSizes[13];
    (void)FN_READ_FLASH_SECTION(source_sector, (void *)section);
    if (stage61_read16(section + STAGE61_SAVE_ID_OFFSET) != 13u
            || stage61_read32(section + STAGE61_SAVE_SIGNATURE_OFFSET)
                != STAGE61_SAVE_SIGNATURE
            || stage61_read32(section + STAGE61_SAVE_COUNTER_OFFSET)
                != selected->counter
            || stage61_read16(section + STAGE61_SAVE_CHECKSUM_OFFSET)
                != FN_SAVE_CHECKSUM((const void *)section, size)) {
        stage61_save_mark_damaged(source_sector);
        return STAGE61_SAVE_STATUS_ERROR;
    }

    record_crc = stage61_state_crc();
    stage61_state_inject_tail(section, 13u, size);
    if (stage61_state_tail_matches_live_crc(
            section, 13u, size, record_crc) == 0u) {
        stage61_save_mark_damaged(source_sector);
        return STAGE61_SAVE_STATUS_ERROR;
    }
    expected_section_crc = stage61_save_section_crc32(section);

    stage61_save_mark_damaged(source_sector);
    if (erase_sector(source_sector) != 0u)
        return STAGE61_SAVE_STATUS_ERROR;
    for (index = 0u; index < STAGE61_SAVE_SIGNATURE_OFFSET; ++index) {
        if (program_byte(source_sector, index, section[index]) != 0u)
            return STAGE61_SAVE_STATUS_ERROR;
    }
    for (index = STAGE61_SAVE_SIGNATURE_OFFSET + 1u;
         index < STAGE61_SAVE_SECTION_SIZE; ++index) {
        if (program_byte(source_sector, index, section[index]) != 0u)
            return STAGE61_SAVE_STATUS_ERROR;
    }
    if (program_byte(
            source_sector,
            STAGE61_SAVE_SIGNATURE_OFFSET,
            section[STAGE61_SAVE_SIGNATURE_OFFSET]) != 0u)
        return STAGE61_SAVE_STATUS_ERROR;

    (void)FN_READ_FLASH_SECTION(source_sector, (void *)section);
    if (stage61_save_section_crc32(section) != expected_section_crc
            || stage61_read16(section + STAGE61_SAVE_ID_OFFSET) != 13u
            || stage61_read32(section + STAGE61_SAVE_SIGNATURE_OFFSET)
                != STAGE61_SAVE_SIGNATURE
            || stage61_read32(section + STAGE61_SAVE_COUNTER_OFFSET)
                != selected->counter
            || stage61_read16(section + STAGE61_SAVE_CHECKSUM_OFFSET)
                != FN_SAVE_CHECKSUM((const void *)section, size)
            || stage61_state_tail_matches_live_crc(
                section, 13u, size, record_crc) == 0u)
        return STAGE61_SAVE_STATUS_ERROR;

    stage61_save_clear_damaged(source_sector);
    return STAGE61_SAVE_STATUS_OK;
}

/* Partial link saves intentionally keep the current PokemonStorage
 * generation.  Rewriting logical chunk 13 from RAM would mix a new 0x7D0
 * storage fragment into that old generation.  An in-place id13 rewrite is
 * also unsafe when the other slot is EMPTY or malformed: power loss after
 * erasing id13 would destroy the only complete generation.
 *
 * The preflight exact-old c+1 bank makes a source-id13 signature-last rewrite
 * safe.  Commit and read-validate that S61E-only source update first; only then
 * invalidate the old backup and clone the exact-new source into c+1.  Thus a
 * fresh selector can observe only exact old before the source commit, or exact
 * new after it—never stock-new data with an old extension record.  Every
 * target sector also commits its signature byte last, and globals switch only
 * after all fourteen target sectors are committed.
 */
STAGE61_EXPORT(Stage61State_UpdateRecordOnly)
u8 Stage61State_UpdateRecordOnly(
    const struct Stage61SaveBlockChunk *chunks)
{
    struct Stage61SaveSlotValidation selected;
    struct Stage61SaveSlotValidation committed_source;
    u8 source_base;
    u8 target_base;
    u32 target_counter;

    source_base = (u8)(
        STAGE61_SAVE_SLOT_SECTORS * (G_SAVE_COUNTER & 1u)
    );
    target_counter = G_SAVE_COUNTER + 1u;
    target_base = (u8)(
        STAGE61_SAVE_SLOT_SECTORS * (target_counter & 1u)
    );
    if (source_base == target_base
            || stage61_save_all_descriptors_are_valid(chunks) == 0u) {
        stage61_save_mark_damaged(
            stage61_save_physical_sector_for_id(13u)
        );
        return STAGE61_SAVE_STATUS_ERROR;
    }

    stage61_save_validate_slot(source_base, chunks, &selected);
    if (selected.status != STAGE61_SAVE_STATUS_OK
            || selected.counter != G_SAVE_COUNTER
            || selected.valid_mask != STAGE61_SAVE_FULL_MASK
            || selected.physical_by_id[13] == 0xFFu) {
        stage61_save_mark_damaged(
            stage61_save_physical_sector_for_id(13u)
        );
        return STAGE61_SAVE_STATUS_ERROR;
    }

    if (stage61_save_rewrite_source_record_sector(
            chunks, &selected, source_base) != STAGE61_SAVE_STATUS_OK) {
        stage61_save_mark_damaged(
            (u16)(source_base + selected.physical_by_id[13])
        );
        return STAGE61_SAVE_STATUS_ERROR;
    }
    stage61_save_validate_slot(source_base, chunks, &committed_source);
    if (stage61_save_validations_match(
            &selected, &committed_source) == 0u) {
        stage61_save_mark_damaged(
            (u16)(source_base + selected.physical_by_id[13])
        );
        return STAGE61_SAVE_STATUS_ERROR;
    }

    /* Do not run the global selector here: the exact-old c+1 backup is still
     * deliberately newer. Source c has just been read-validated as the exact
     * stock+S61E result and is the authority for the remaining transaction.
     * Consume committed_source directly: assigning this struct made GCC emit
     * a freestanding memcpy reference at link time. */
    if (stage61_save_invalidate_target_record_sector(
            &committed_source, source_base, target_base)
            != STAGE61_SAVE_STATUS_OK) {
        /* TrySavingData ignores this wrapper's return value and consults only
         * gDamagedSaveSectors.  The invalidator's early ABI guards can fail
         * before it marks anything, so the caller must always publish the
         * exact target-bank record sector on a non-OK result. */
        stage61_save_mark_damaged(
            (u16)(target_base + committed_source.physical_by_id[13])
        );
        return STAGE61_SAVE_STATUS_ERROR;
    }

    if (stage61_save_clone_complete_generation(
            chunks, &committed_source, source_base, target_base,
            target_counter, 0u) != STAGE61_SAVE_STATUS_OK) {
        stage61_save_mark_damaged(
            (u16)(target_base + committed_source.physical_by_id[13])
        );
        return STAGE61_SAVE_STATUS_ERROR;
    }

    G_SAVE_COUNTER = target_counter;
    G_FIRST_SAVE_SECTOR = committed_source.first_save_sector;
    return STAGE61_SAVE_STATUS_OK;
}

/* Re-snapshot after stock returns; neither descriptor addresses nor their
 * owner pointers are assumed stable across the delegated save operation. */
static __attribute__((noinline))
u8 stage61_save_update_live_record_only(void)
{
    struct Stage61SaveBlockChunk live_chunks[STAGE61_SAVE_SLOT_SECTORS];

    if (stage61_save_build_live_descriptors(live_chunks) == 0u) {
        stage61_save_mark_damaged(
            stage61_save_physical_sector_for_id(13u)
        );
        return STAGE61_SAVE_STATUS_ERROR;
    }
    return Stage61State_UpdateRecordOnly(live_chunks);
}

/* SAVE_NORMAL is an owned full-bank copy-on-write transaction: delegating it
 * to stock lets TryWriteSector replace a failed target sector with a physical
 * sector from the protected bank.  Generic SAVE_LINK remains the sole stock
 * partial path whose contract includes SaveBlock1 state, so after all five
 * stock sectors commit it also commits the extension record.  SAVE_EREADER
 * intentionally remains id0-only, and the production post-link and LinkFull
 * paths retain their existing owners.
 */
STAGE61_EXPORT(Stage61State_HandleSavingData)
u8 Stage61State_HandleSavingData(u8 save_type)
{
    u8 result;

    if (save_type == STAGE61_SAVE_TYPE_NORMAL) {
        volatile u32 *backup_counter = G_MAIN_VBLANK_COUNTER1;

        G_MAIN_VBLANK_COUNTER1 = (volatile u32 *)0;
        result = stage61_save_normal_copy_on_write();
        G_MAIN_VBLANK_COUNTER1 = backup_counter;
        return result == STAGE61_SAVE_STATUS_OK
            ? 0u : STAGE61_SAVE_STATUS_ERROR;
    }

    if (save_type == STAGE61_SAVE_TYPE_LINK) {
        volatile u32 *backup_counter = G_MAIN_VBLANK_COUNTER1;
        u8 preflight_result;

        /* This gate is intentionally before the first stock flash callback.
         * A failed safety clone must leave the source untouched and must not
         * enter stock's in-place id0..4 partial-save path.  Do not consume
        * the stock descriptor cache here: stock has not yet refreshed it for
         * the live SaveBlock relocation performed by Continue. */
        G_MAIN_VBLANK_COUNTER1 = (volatile u32 *)0;
        preflight_result = stage61_save_ensure_live_backup_generation();
        G_MAIN_VBLANK_COUNTER1 = backup_counter;
        if (preflight_result != STAGE61_SAVE_STATUS_OK) {
            u8 failed_base = (u8)(
                STAGE61_SAVE_SLOT_SECTORS * ((G_SAVE_COUNTER + 1u) & 1u)
            );
            return stage61_save_fail_with_sector(failed_base);
        }
    }

    result = FN_STOCK_HANDLE_SAVING_DATA(save_type);

    /* FireRed's HandleSavingData ABI always returns zero, including after a
     * flash callback marks a sector damaged.  This wrapper has an explicit
     * STATUS_ERROR contract for its own preflight/record failures, so letting
     * the stock zero escape would make the same failed transaction look like
     * success solely according to which phase failed.  Normalize the stock
     * damaged-sector side channel before any extension-record commit.  The
     * stock TrySavingData caller continues to inspect the same bitmask, while
     * direct wrapper callers now receive an unambiguous result as well. */
    if (G_DAMAGED_SAVE_SECTORS != 0u)
        return STAGE61_SAVE_STATUS_ERROR;

    if (save_type == STAGE61_SAVE_TYPE_LINK && result == 0u) {
        volatile u32 *backup_counter = G_MAIN_VBLANK_COUNTER1;
        u8 record_result;

        /* Stock restored this bookkeeping pointer immediately before its
         * return.  Hold it at the same NULL value used during the five stock
         * flash writes while committing the record-only sector, then restore
         * it on every outcome.  Rebuild from the post-stock live owners; the
         * preflight snapshot is deliberately not reused across that call. */
        G_MAIN_VBLANK_COUNTER1 = (volatile u32 *)0;
        record_result = stage61_save_update_live_record_only();
        G_MAIN_VBLANK_COUNTER1 = backup_counter;
        /* Every post phase marks only the non-authoritative bank/sector it
         * actually damaged.  Do not guess another sector here: stock's save
         * failure screen wipes every marked sector before retry, so adding an
         * opposite-bank bit could destroy the sole coherent generation. */
        if (record_result != STAGE61_SAVE_STATUS_OK)
            return STAGE61_SAVE_STATUS_ERROR;
    }
    return result;
}

STAGE61_EXPORT(Stage61State_GetSaveValidStatus)
u8 Stage61State_GetSaveValidStatus(
    const struct Stage61SaveBlockChunk *chunks)
{
    u8 selected_base;

    return stage61_save_select_generation(chunks, &selected_base);
}

STAGE61_EXPORT(Stage61State_HandleLoadSector)
u8 Stage61State_HandleLoadSector(
    u16 argument, const struct Stage61SaveBlockChunk *chunks)
{
    struct Stage61SaveSlotValidation selected;
    struct Stage61SaveSlotValidation confirmed;
    u8 physical_base;

    (void)argument;
    physical_base = (u8)(
        STAGE61_SAVE_SLOT_SECTORS * (G_SAVE_COUNTER & 1u)
    );
    stage61_save_validate_slot(physical_base, chunks, &selected);

    /* GetSaveValidStatus normally selected this generation immediately
     * before the copy.  If this entry is invoked independently, or the
     * selected bank ceased to validate, run the same bounded selector once
     * and still refuse every partial generation. */
    if (selected.status != STAGE61_SAVE_STATUS_OK
            || selected.counter != G_SAVE_COUNTER) {
        if (stage61_save_select_generation(chunks, &physical_base)
                    == STAGE61_SAVE_STATUS_EMPTY
                || physical_base == 0xFFu) {
            stage61_state_clear();
            return STAGE61_SAVE_STATUS_OK;
        }
        stage61_save_validate_slot(physical_base, chunks, &selected);
        if (selected.status != STAGE61_SAVE_STATUS_OK
                || selected.counter != G_SAVE_COUNTER) {
            stage61_state_clear();
            return STAGE61_SAVE_STATUS_OK;
        }
    }

    /* Read and validate the entire chosen generation once more before the
     * first destination byte is touched.  ReadFlashSection has no failure
     * return in the stock ABI and flash cannot mutate concurrently on the
     * single-core GBA; this second full pass detects every torn/mutated image
     * observable between selection and copy without requiring an unsafe
     * 52-KiB temporary RAM image. */
    stage61_save_validate_slot(physical_base, chunks, &confirmed);
    if (stage61_save_validations_match(&selected, &confirmed) == 0u) {
        stage61_state_clear();
        return STAGE61_SAVE_STATUS_OK;
    }
    stage61_save_copy_validated_slot(
        physical_base, chunks, &confirmed
    );
    stage61_state_load_compatible_record(chunks);
    return STAGE61_SAVE_STATUS_OK;
}

static u8 stage61_summary_has_project_name_provenance(u16 mapsec)
{
    volatile u8 *screen = S_MON_SUMMARY_SCREEN;
    const void *mon;
    u32 met_game;

    if (screen == (volatile u8 *)0)
        return 0u;
    mon = (const void *)(uintptr_t)(screen + 0x323Cu);
    if (FN_GET_MON_DATA(mon, 35, (void *)0) != mapsec)
        return 0u;
    met_game = FN_GET_MON_DATA(mon, 37, (void *)0);
    return met_game == 4u || met_game == 5u;
}

static u8 stage61_has_project_name_provenance(
    u16 mapsec, u8 allow_pending_destination
)
{
    u8 destination_group;
    u8 destination_map;
    const u8 *header;

    if (mapsec >= STAGE61_KANTO_SECTION_COUNT)
        return 0u;
    if (imported_kanto_map_is_valid(current_group(), current_map()))
        return 1u;

    /* GetMapName also runs before a physical warp has committed.  Attribute
     * a low destination section only when the pending WarpData resolves to a
     * bounded imported header carrying that exact section. */
    if (allow_pending_destination) {
        destination_group = S_WARP_DESTINATION[0];
        destination_map = S_WARP_DESTINATION[1];
        if (imported_kanto_map_is_valid(destination_group, destination_map)) {
            header = FN_GET_MAP_HEADER(destination_group, destination_map);
            if (header != (const u8 *)0 && header[0x14] == mapsec)
                return 1u;
        }
    }

    /* Pokémon metLocation 0..52 overlaps Hoenn.  Only a matching summary
     * mon whose metGame is FR/LG supplies non-physical project provenance. */
    return stage61_summary_has_project_name_provenance(mapsec);
}

static const u8 *resolve_name_pointer(
    u16 mapsec, u8 allow_pending_destination
)
{
    if (mapsec < STAGE61_KANTO_SECTION_COUNT) {
        if (!stage61_has_project_name_provenance(
                mapsec, allow_pending_destination))
            return (const u8 *)0;
        if (is_project_celadon_department(mapsec))
            return STOCK_CELADON_DEPT_NAME;
        return KANTO_MAP_NAMES[mapsec];
    }
    if ((u16)(mapsec - STAGE61_STOCK_SECTION_START)
            < STAGE61_STOCK_SECTION_COUNT)
        return STOCK_MAP_NAMES[mapsec - STAGE61_STOCK_SECTION_START];
    return (const u8 *)0;
}

STAGE61_EXPORT(Stage61DisplayNpcEvent_GetMapName)
u8 *Stage61DisplayNpcEvent_GetMapName(u8 *destination, u16 mapsec, u16 fill)
{
    const u8 *source;
    u8 *end;
    u16 length;
    uintptr_t caller;
    u8 allow_pending_destination;

    if (destination == (u8 *)0)
        return destination;
    caller = (uintptr_t)__builtin_return_address(0);
    allow_pending_destination =
        (u32)(caller & ~(uintptr_t)1u) == STAGE61_MAP_PREVIEW_NAME_RETURN;
    if (mapsec < STAGE61_KANTO_SECTION_COUNT
            && stage61_has_project_name_provenance(
                mapsec, allow_pending_destination)) {
        source = resolve_name_pointer(mapsec, allow_pending_destination);
    } else if ((u16)(mapsec - STAGE61_STOCK_SECTION_START)
               < STAGE61_STOCK_SECTION_COUNT) {
        source = FN_IS_CELADON_DEPT_STORE_MAPSEC(mapsec)
            ? STOCK_CELADON_DEPT_NAME
            : STOCK_MAP_NAMES[mapsec - STAGE61_STOCK_SECTION_START];
    } else {
        if (fill == 0u)
            fill = STAGE61_DEFAULT_NAME_FILL;
        return FN_STRING_FILL(destination, STAGE61_CHAR_SPACE, fill);
    }

    end = FN_STRING_COPY(destination, source);
    if (fill == 0u)
        return end;
    length = (u16)(end - destination);
    while (length < fill) {
        *end++ = STAGE61_CHAR_SPACE;
        ++length;
    }
    *end = STAGE61_EOS;
    return end;
}

STAGE61_EXPORT(Stage61DisplayNpcEvent_ResolveNamePointer)
const u8 *Stage61DisplayNpcEvent_ResolveNamePointer(u16 mapsec)
{
    return resolve_name_pointer(mapsec, 0u);
}

STAGE61_EXPORT(Stage61RegionMap_DecompressGfx)
void *Stage61RegionMap_DecompressGfx(
    u8 bg, const void *source, u32 size, u16 offset, u8 mode)
{
    if (is_imported_kanto_context())
        source = KANTO_REGION_GFX;
    return FN_DECOMPRESS_BG(bg, source, size, offset, mode);
}

STAGE61_EXPORT(Stage61RegionMap_DecompressTilemap)
void Stage61RegionMap_DecompressTilemap(const void *source, void *destination)
{
    if (is_imported_kanto_context())
        source = KANTO_REGION_TILEMAP;
    FN_LZ77_UNCOMP_WRAM(source, destination);
}

STAGE61_EXPORT(Stage61RegionMap_GetMapsecType)
u8 Stage61RegionMap_GetMapsecType(u8 mapsec)
{
    u16 flag;
    if (mapsec == STAGE61_MAPSEC_NONE)
        return STAGE61_MAPSECTYPE_NONE;
    if (mapsec >= STAGE61_KANTO_SECTION_COUNT)
        return FN_STOCK_GET_MAPSEC_TYPE(mapsec);
    if (mapsec >= STAGE61_KANTO_CITY_COUNT)
        return STAGE61_MAPSECTYPE_ROUTE;
    flag = KANTO_VISIT_FLAGS[mapsec];
    if (flag == 0xFFFFu)
        return STAGE61_MAPSECTYPE_ROUTE;
    return FN_FLAG_GET(flag)
        ? STAGE61_MAPSECTYPE_VISITED : STAGE61_MAPSECTYPE_NOT_VISITED;
}

STAGE61_EXPORT(Stage61RegionMap_GetDungeonMapsecType)
u8 Stage61RegionMap_GetDungeonMapsecType(u8 mapsec)
{
    u16 flag;
    if (mapsec == STAGE61_MAPSEC_NONE)
        return STAGE61_MAPSECTYPE_NONE;
    if (mapsec >= STAGE61_KANTO_SECTION_COUNT)
        return FN_STOCK_GET_DUNGEON_MAPSEC_TYPE(mapsec);
    if (mapsec < STAGE61_KANTO_DUNGEON_START)
        return STAGE61_MAPSECTYPE_ROUTE;
    flag = KANTO_VISIT_FLAGS[mapsec];
    if (flag == 0xFFFFu)
        return STAGE61_MAPSECTYPE_ROUTE;
    return FN_FLAG_GET(flag)
        ? STAGE61_MAPSECTYPE_VISITED : STAGE61_MAPSECTYPE_NOT_VISITED;
}

STAGE61_EXPORT(Stage61RegionMap_GetPlayerPosition)
void Stage61RegionMap_GetPlayerPosition(void)
{
    volatile u8 *cursor;
    const u8 *position;
    u8 section;

    if (!is_imported_kanto_context()) {
        FN_STOCK_GET_PLAYER_POSITION();
        return;
    }
    cursor = S_MAP_CURSOR_PTR;
    if (cursor == (volatile u8 *)0)
        return;
    section = current_project_section();
    if (section >= STAGE61_KANTO_SECTION_COUNT) {
        *(volatile u16 *)(cursor + 0) = 0u;
        *(volatile u16 *)(cursor + 2) = 0u;
        *(volatile u16 *)(cursor + 20) = STAGE61_MAPSEC_NONE;
        return;
    }
    position = KANTO_POSITIONS + (u32)section * 6u;
    *(volatile u16 *)(cursor + 0) = position[4];
    *(volatile u16 *)(cursor + 2) = position[5];
    *(volatile u16 *)(cursor + 20) = section;
}

STAGE61_EXPORT(Stage61RegionMap_GetSelectedMapSection)
u8 Stage61RegionMap_GetSelectedMapSection(u8 which_map, u8 layer, s16 y, s16 x)
{
    u32 index;
    if (!is_imported_kanto_context() || which_map != STAGE61_REGION_KANTO)
        return FN_STOCK_GET_SELECTED_MAP_SECTION(which_map, layer, y, x);
    if (layer >= STAGE61_LAYER_COUNT || y < 0 || y >= STAGE61_MAP_HEIGHT
            || x < 0 || x >= STAGE61_MAP_WIDTH)
        return STAGE61_MAPSEC_NONE;
    index = ((u32)layer * STAGE61_MAP_HEIGHT + (u16)y)
        * STAGE61_MAP_WIDTH + (u16)x;
    return KANTO_REGION_GRID[index];
}

STAGE61_EXPORT(Stage61Visit_RunOnTransitionMapScript)
void Stage61Visit_RunOnTransitionMapScript(void)
{
    u8 section;
    u16 flag;
    if (is_imported_kanto_context()) {
        section = current_project_section();
        if (section < STAGE61_KANTO_SECTION_COUNT) {
            flag = KANTO_VISIT_FLAGS[section];
            if (flag != 0xFFFFu)
                (void)FN_FLAG_SET(flag);
        }
    }
    FN_MAP_HEADER_RUN_SCRIPT_TYPE(3u);
}

STAGE61_EXPORT(Stage61MapSection_GetRaidCompatibleCurrent)
u8 Stage61MapSection_GetRaidCompatibleCurrent(void)
{
    u8 section = FN_GET_CURRENT_MAP_SECTION();

    if (is_imported_kanto_context()) {
        if (section < STAGE61_KANTO_SECTION_COUNT)
            section = project_section_to_source(section);
        else
            return 87u; /* MAPSEC_DYNAMIC: bounded empty Raid row 0. */
    }

    /* CFRU subtracts MAPSEC_DYNAMIC (87) and indexes 109 rows.  Clamp every
     * malformed/non-Kanto section, including Celadon Dept 196, to the empty
     * dynamic row instead of permitting an out-of-bounds row 109+ read. */
    if (section < 87u || section > 195u)
        return 87u;
    return section;
}

static u16 stage61_normalize_raid_flag(u16 flag)
{
    if (flag >= STAGE61_LEGACY_RAID_FLAG_BASE
            && flag <= STAGE61_LEGACY_RAID_FLAG_END)
        return (u16)(STAGE61_RAID_FLAG_BASE
            + flag - STAGE61_LEGACY_RAID_FLAG_BASE);
    return flag;
}

STAGE61_EXPORT(Stage61MapSection_RaidFlagGet)
u8 Stage61MapSection_RaidFlagGet(u16 flag)
{
    flag = stage61_normalize_raid_flag(flag);
    return FN_FLAG_GET(flag);
}

STAGE61_EXPORT(Stage61MapSection_RaidFlagSet)
u8 Stage61MapSection_RaidFlagSet(u16 flag)
{
    flag = stage61_normalize_raid_flag(flag);
    return FN_FLAG_SET(flag);
}

STAGE61_EXPORT(Stage61MapSection_RaidFlagClear)
u8 Stage61MapSection_RaidFlagClear(u16 flag)
{
    flag = stage61_normalize_raid_flag(flag);
    return FN_FLAG_CLEAR(flag);
}

STAGE61_EXPORT(Stage61MapSection_MusicCanOverrideMapMusic)
u32 Stage61MapSection_MusicCanOverrideMapMusic(u16 music)
{
    u8 section;

    if (music != 282u && music != 305u) /* cycling / surf */
        return 1u;
    section = current_project_section();
    if (is_imported_kanto_context()) {
        /* Victory Road, Route 23 and Indigo Plateau in project namespace. */
        if (section == 42u || section == 33u || section == 9u)
            return 0u;
    } else {
        /* Exact FireRed/Stage60 stock constants. */
        if (section == 132u || section == 123u || section == 97u)
            return 0u;
    }
    return 1u;
}

STAGE61_EXPORT(Stage61MapSection_GetMapPreviewScreenIdx)
u8 Stage61MapSection_GetMapPreviewScreenIdx(u8 mapsec)
{
    if (mapsec < STAGE61_KANTO_SECTION_COUNT
            && is_imported_kanto_context())
        mapsec = project_section_to_source(mapsec);
    return FN_STOCK_GET_MAP_PREVIEW_SCREEN_IDX(mapsec);
}

static u8 stage61_map_has_preview(u8 mapsec, u8 type)
{
    u8 index = FN_STOCK_GET_MAP_PREVIEW_SCREEN_IDX(mapsec);

    if (index >= STAGE61_PREVIEW_COUNT)
        return 0u;
    if (type == 2u)
        return 1u;
    return STOCK_PREVIEW_ROWS[(u32)index * STAGE61_PREVIEW_ROW_SIZE + 1u]
        == type;
}

static void stage61_warp_fade_out(u8 cfru_white_guard)
{
    const u8 *destination = FN_GET_DESTINATION_MAP_HEADER();
    u8 current_group_value = current_group();
    u8 destination_group = S_WARP_DESTINATION[0];
    u8 current_imported;
    u8 destination_imported;
    u8 current_section;
    u8 destination_section;
    u8 transition;

    if (destination == (const u8 *)0) {
        FN_FADE_SCREEN(1u, 0);
        return;
    }
    current_imported = is_imported_kanto_group(current_group_value);
    destination_imported = is_imported_kanto_group(destination_group);
    current_section = normalize_section_for_physical_group(
        current_group_value, current_project_section()
    );
    destination_section = normalize_section_for_physical_group(
        destination_group, destination[0x14]
    );

    /* A numeric source ID is not identity across physical namespaces.  A
     * Kanto->Vega warp whose normalized values happen to match is still a
     * location change and must not suppress the destination preview. */
    if ((current_imported != destination_imported
            || current_section != destination_section)
            && stage61_map_has_preview(
                destination_section, STAGE61_PREVIEW_TYPE_CAVE)) {
        FN_FADE_SCREEN(1u, 0);
        return;
    }

    transition = FN_MAP_TRANSITION_IS_ENTER(
        FN_GET_CURRENT_MAP_TYPE(), destination[0x17]
    );
    if (transition == 0u) {
        FN_FADE_SCREEN(1u, 0);
    } else if (transition == 1u) {
        if (cfru_white_guard)
            G_DONT_FADE_WHITE = 1u;
        FN_FADE_SCREEN(3u, 0);
    }
}

STAGE61_EXPORT(Stage61MapSection_WarpFadeOutScreen)
void Stage61MapSection_WarpFadeOutScreen(void)
{
    stage61_warp_fade_out(0u);
}

STAGE61_EXPORT(Stage61MapSection_CfruWarpFadeOutScreen)
void Stage61MapSection_CfruWarpFadeOutScreen(void)
{
    stage61_warp_fade_out(1u);
}

STAGE61_EXPORT(Stage61MapSection_GetDungeonFlavorText)
const u8 *Stage61MapSection_GetDungeonFlavorText(u16 mapsec)
{
    if (is_imported_kanto_context()
            && mapsec < STAGE61_KANTO_SECTION_COUNT)
        mapsec = project_section_to_source((u8)mapsec);
    return FN_STOCK_GET_DUNGEON_FLAVOR_TEXT(mapsec);
}

STAGE61_EXPORT(Stage61MapSection_GetDungeonName)
const u8 *Stage61MapSection_GetDungeonName(u16 mapsec)
{
    if (is_imported_kanto_context()
            && mapsec < STAGE61_KANTO_SECTION_COUNT)
        mapsec = project_section_to_source((u8)mapsec);
    return FN_STOCK_GET_DUNGEON_NAME(mapsec);
}

STAGE61_EXPORT(Stage61MapSection_GetDungeonMapsecUnderCursor)
u16 Stage61MapSection_GetDungeonMapsecUnderCursor(void)
{
    volatile u8 *cursor = S_MAP_CURSOR_PTR;
    s16 x;
    s16 y;
    u8 mapsec;
    u8 cerulean;

    if (cursor == (volatile u8 *)0)
        return STAGE61_MAPSEC_NONE;
    x = *PTR(volatile s16 *, (uintptr_t)cursor);
    y = *PTR(volatile s16 *, (uintptr_t)cursor + 2u);
    if (x < 0 || x >= (s16)STAGE61_MAP_WIDTH
            || y < 0 || y >= (s16)STAGE61_MAP_HEIGHT)
        return STAGE61_MAPSEC_NONE;
    mapsec = FN_GET_SELECTED_MAP_SECTION(
        FN_GET_SELECTED_REGION_MAP(), 1u, y, x
    );
    cerulean = is_imported_kanto_context() ? 51u : 141u;
    if (mapsec == cerulean && !FN_FLAG_GET(0x0844u))
        return STAGE61_MAPSEC_NONE;
    return mapsec;
}

STAGE61_EXPORT(Stage61MapSection_IsDungeonCeruleanUnlocked)
u32 Stage61MapSection_IsDungeonCeruleanUnlocked(void)
{
    return FN_FLAG_GET(0x0844u) != 0u;
}

/* Internal CreateDungeonIcons continuation.  r4 owns the selected mapsec;
 * all loop registers and the original stack frame stay in the stock owner. */
STAGE61_NAKED_EXPORT(Stage61MapSection_CreateDungeonIconsCeruleanGate)
void Stage61MapSection_CreateDungeonIconsCeruleanGate(void)
{
    __asm__ volatile(
        ".syntax unified\n"
        "ldr r1, =0x03005048\n"
        "ldr r1, [r1, #0]\n"
        "cmp r1, #0\n"
        "beq 1f\n"
        "ldrb r1, [r1, #4]\n"
        "subs r1, #96\n"
        "cmp r1, #2\n"
        "bhi 1f\n"
        "movs r1, #51\n"
        "b 2f\n"
        "1:\n"
        "movs r1, #141\n"
        "2:\n"
        "cmp r4, r1\n"
        "bne 3f\n"
        "bl Stage61MapSection_IsDungeonCeruleanUnlocked\n"
        "cmp r0, #0\n"
        "beq 4f\n"
        "3:\n"
        "ldr r3, =0x080C5A25\n"
        "bx r3\n"
        "4:\n"
        "ldr r3, =0x080C5A69\n"
        "bx r3\n"
        :
        :
        : "r0", "r1", "r3", "cc"
    );
}

STAGE61_EXPORT(Stage61MapSection_IsKantoOrSeviiForMemo)
u32 Stage61MapSection_IsKantoOrSeviiForMemo(u8 mapsec)
{
    volatile u8 *screen;
    u32 met_game;

    if ((u8)(mapsec - STAGE61_STOCK_SECTION_START)
            < STAGE61_STOCK_SECTION_COUNT)
        return 1u;
    if (mapsec >= STAGE61_KANTO_SECTION_COUNT)
        return 0u;

    /* Project 0..52 overlaps the Hoenn met-location namespace.  Provenance
     * comes from the stored game version, never from the currently open map. */
    screen = S_MON_SUMMARY_SCREEN;
    if (screen == (volatile u8 *)0)
        return 0u;
    met_game = FN_GET_MON_DATA(
        (const void *)(uintptr_t)(screen + 0x323Cu), 37, (void *)0
    );
    return (met_game == 4u || met_game == 5u) ? 1u : 0u;
}

STAGE61_EXPORT(Stage61MapSection_GetWildHeaderMapSection)
u16 Stage61MapSection_GetWildHeaderMapSection(const u8 *header)
{
    const u8 *map_header;
    u8 group;
    u8 number;
    u8 section;

    if (header == (const u8 *)0)
        return STAGE61_MAPSEC_NONE;
    group = header[0];
    number = header[1];
    map_header = FN_GET_MAP_HEADER(group, number);
    if (map_header == (const u8 *)0)
        return STAGE61_MAPSEC_NONE;
    section = map_header[0x14];
    if (!is_imported_kanto_group(group))
        return section;
    if (section >= STAGE61_KANTO_SECTION_COUNT)
        return STAGE61_MAPSEC_NONE;
    return project_section_to_source(section);
}

/* Internal continuation hook for Quest Log field-move rendering.  At the
 * displaced site r5 points at the record, r4 is the badge index and r2 is
 * the stock gym-section table.  Normalize only the project-local record
 * namespace, replay the exact compare and preserve its condition flags. */
STAGE61_NAKED_EXPORT(Stage61MapSection_QuestLogGymCompare)
void Stage61MapSection_QuestLogGymCompare(void)
{
    __asm__ volatile(
        ".syntax unified\n"
        "ldrb r1, [r5, #0]\n"
        "cmp r1, #53\n"
        "bhs 1f\n"
        "ldr r0, =%c0\n"
        "ldrb r1, [r0, r1]\n"
        "1:\n"
        "adds r0, r4, r2\n"
        "ldrb r0, [r0, #0]\n"
        "cmp r1, r0\n"
        "ldr r3, =0x08115DD1\n"
        "bx r3\n"
        :
        : "i" (STAGE61_KANTO_SOURCE_SECTION_IDS)
        : "r0", "r1", "r3", "cc"
    );
}

/* Quest Log Teleport names Pallet as HOME.  Imported Pallet is project 0;
 * retain stock 88 as an accepted legacy/source record at the same boundary. */
STAGE61_NAKED_EXPORT(Stage61MapSection_QuestLogTeleportHome)
void Stage61MapSection_QuestLogTeleportHome(void)
{
    __asm__ volatile(
        ".syntax unified\n"
        "ldrb r0, [r5, #1]\n"
        "cmp r0, #0\n"
        "beq 1f\n"
        "cmp r0, #88\n"
        "beq 1f\n"
        "ldr r3, =0x08115F85\n"
        "bx r3\n"
        "1:\n"
        "ldr r3, =0x08115F6B\n"
        "bx r3\n"
        :
        :
        : "r0", "r3", "cc"
    );
}

struct Stage61QuestLogComponentExtra {
    u8 location;
    u8 group;
    u8 map;
};

/* Generated-manifest parity is asserted by the focused policy test.  Primary
 * component members live in QUEST_LOG_SOURCE_PAIRS; only path-intermediate
 * members need ROM-resident extras.  Keeping this list narrow makes an
 * unrelated cave warp a stale-token clear, never an accidental narration. */
static const struct Stage61QuestLogComponentExtra
sStage61SourceQuestLogComponentExtras[] = {
    {24u, 12u, 1u},
    {24u, 11u, 8u},
    {35u, 11u, 2u},
    {46u, 11u, 8u},
    {48u, 1u, 39u},
};

/* The exact imported crosswalk has 50 direct exits.  SS Anne is the only
 * multihop row: Corridor -> Exterior -> Vermilion. */
static const struct Stage61QuestLogComponentExtra
sStage61ProjectQuestLogComponentExtras[] = {
    {19u, 97u, 4u},
};

static const u8 *stage61_quest_log_pair_for_namespace(u8 index, u8 imported)
{
    const u8 *table = imported
        ? QUEST_LOG_PROJECT_PAIRS : QUEST_LOG_SOURCE_PAIRS;
    return table + (u32)index * STAGE61_QUEST_LOG_PAIR_SIZE;
}

static u8 stage61_quest_log_pair_is_enabled(const u8 *row)
{
    return row[0] != 0xFFu && row[1] != 0xFFu
        && row[2] != 0xFFu && row[3] != 0xFFu;
}

static u8 stage61_current_matches_pair_side(
    const u8 *row, u8 side_offset
)
{
    return current_group() == row[side_offset]
        && current_map() == row[(u8)(side_offset + 1u)];
}

static u8 stage61_departed_inside_section(const u8 *row, u8 imported)
{
    const u8 *header;

    /* The stock QuestLog_TryRecordDepartedLocation owner does not use a
     * FireRed section constant for the generic and League paths.  It resolves
     * the inside physical map header at runtime, which is significant because
     * Stage60's non-imported maps reuse those physical group/map identities
     * with Vega section IDs.  Imported Kanto has a deliberately separate
     * project namespace and therefore uses the materialized project value. */
    if (imported)
        return row[4];
    header = FN_GET_MAP_HEADER(row[0], row[1]);
    return header == (const u8 *)0 ? STAGE61_MAPSEC_NONE : header[0x14];
}

static void stage61_record_departed(u8 mapsec, u8 location)
{
    u16 data = (u16)mapsec | (u16)((u16)location << 8);
    (void)FN_SET_QUEST_LOG_EVENT(STAGE61_QL_EVENT_DEPARTED, &data);
    FN_FLAG_CLEAR(STAGE61_FLAG_SYS_QL_DEPARTED);
}

static void stage61_quest_log_clear_pending(void)
{
    FN_FLAG_CLEAR(STAGE61_FLAG_SYS_QL_DEPARTED);
}

static void stage61_quest_log_arm_current_source(void)
{
    u8 index;

    if (is_imported_kanto_context()
            || FN_FLAG_GET(STAGE61_FLAG_SYS_QL_DEPARTED))
        return;
    for (index = 0u; index < STAGE61_QUEST_LOG_PAIR_COUNT; ++index) {
        const u8 *row = stage61_quest_log_pair_for_namespace(index, 0u);
        if (!stage61_quest_log_pair_is_enabled(row)
                || !stage61_current_matches_pair_side(row, 0u))
            continue;
        FN_VAR_SET(STAGE61_VAR_QL_ENTRANCE, index);
        FN_FLAG_SET(STAGE61_FLAG_SYS_QL_DEPARTED);
        return;
    }
}

static void stage61_quest_log_arm_current_project(void)
{
    u8 index;

    if (!is_imported_kanto_context()
            || FN_FLAG_GET(STAGE61_FLAG_SYS_QL_DEPARTED))
        return;
    for (index = 0u; index < STAGE61_QUEST_LOG_PAIR_COUNT; ++index) {
        const u8 *row = stage61_quest_log_pair_for_namespace(index, 1u);
        if (!stage61_quest_log_pair_is_enabled(row)
                || !stage61_current_matches_pair_side(row, 0u))
            continue;
        FN_VAR_SET(STAGE61_VAR_QL_ENTRANCE, index);
        FN_FLAG_SET(STAGE61_FLAG_SYS_QL_DEPARTED);
        return;
    }
}

static u8 stage61_current_in_source_component(u8 location)
{
    u32 index;
    const u8 *row = stage61_quest_log_pair_for_namespace(location, 0u);

    if (!stage61_quest_log_pair_is_enabled(row))
        return 0u;
    if (stage61_current_matches_pair_side(row, 0u))
        return 1u;
    for (index = 0u;
            index < sizeof(sStage61SourceQuestLogComponentExtras)
                / sizeof(sStage61SourceQuestLogComponentExtras[0]);
            ++index) {
        const struct Stage61QuestLogComponentExtra *extra =
            &sStage61SourceQuestLogComponentExtras[index];
        if (extra->location == location
                && extra->group == current_group()
                && extra->map == current_map())
            return 1u;
    }
    return 0u;
}

static u8 stage61_current_in_project_component(u8 location)
{
    u32 index;
    const u8 *row = stage61_quest_log_pair_for_namespace(location, 1u);

    if (!stage61_quest_log_pair_is_enabled(row))
        return 0u;
    if (stage61_current_matches_pair_side(row, 0u))
        return 1u;
    for (index = 0u;
            index < sizeof(sStage61ProjectQuestLogComponentExtras)
                / sizeof(sStage61ProjectQuestLogComponentExtras[0]);
            ++index) {
        const struct Stage61QuestLogComponentExtra *extra =
            &sStage61ProjectQuestLogComponentExtras[index];
        if (extra->location == location
                && extra->group == current_group()
                && extra->map == current_map())
            return 1u;
    }
    return 0u;
}

static void stage61_quest_log_finish_source_transition(void)
{
    stage61_quest_log_clear_pending();
    stage61_quest_log_arm_current_source();
}

static u8 stage61_quest_log_record_shared_map_exit(
    u8 first, u8 second, u8 viridian_forest, u8 imported
)
{
    const u8 *row = stage61_quest_log_pair_for_namespace(first, imported);

    if (stage61_current_matches_pair_side(row, 2u)) {
        stage61_record_departed(
            viridian_forest ? row[5]
                : stage61_departed_inside_section(row, imported),
            first
        );
        return 1u;
    }
    row = stage61_quest_log_pair_for_namespace(second, imported);
    if (stage61_current_matches_pair_side(row, 2u)) {
        stage61_record_departed(
            viridian_forest ? row[5]
                : stage61_departed_inside_section(row, imported),
            second
        );
        return 1u;
    }
    return 0u;
}

static u8 stage61_quest_log_record_warp_variant(
    u8 first, u8 imported
)
{
    const u8 *row = stage61_quest_log_pair_for_namespace(first, imported);
    u8 warp_id;

    if (!stage61_current_matches_pair_side(row, 2u))
        return 0u;
    warp_id = current_warp_id();
    if (warp_id > 1u)
        return 0u;
    stage61_record_departed(
        stage61_departed_inside_section(row, imported),
        (u8)(first + warp_id)
    );
    return 1u;
}

static void stage61_quest_log_try_record_project(u8 location)
{
    const u8 *row = stage61_quest_log_pair_for_namespace(location, 1u);
    u8 recorded = 0u;

    if (!stage61_quest_log_pair_is_enabled(row)) {
        stage61_quest_log_clear_pending();
        stage61_quest_log_arm_current_project();
        return;
    }
    if (stage61_current_in_project_component(location))
        return;

    if (location == 5u || location == 6u)
        recorded = stage61_quest_log_record_shared_map_exit(5u, 6u, 1u, 1u);
    else if (location == 3u || location == 4u)
        recorded = stage61_quest_log_record_shared_map_exit(3u, 4u, 0u, 1u);
    else if (location == 22u || location == 23u)
        recorded = stage61_quest_log_record_warp_variant(22u, 1u);
    else if (location == 42u || location == 43u)
        recorded = stage61_quest_log_record_warp_variant(42u, 1u);
    else if (stage61_current_matches_pair_side(row, 2u)) {
        stage61_record_departed(
            stage61_departed_inside_section(row, 1u), location
        );
        recorded = 1u;
    }

    if (!recorded) {
        stage61_quest_log_clear_pending();
        stage61_quest_log_arm_current_project();
        return;
    }
    /* This stock special is valid only after Rocket Hideout was actually
     * recorded on its reviewed Game Corner exit.  Mismatches never rearm it. */
    if (location == STAGE61_QL_ROCKET_HIDEOUT) {
        FN_VAR_SET(STAGE61_VAR_QL_ENTRANCE, STAGE61_QL_GAME_CORNER);
        FN_FLAG_SET(STAGE61_FLAG_SYS_QL_DEPARTED);
        return;
    }
    stage61_quest_log_arm_current_project();
}

static void stage61_quest_log_try_record_source(u8 location)
{
    const u8 *row = stage61_quest_log_pair_for_namespace(location, 0u);
    u8 recorded;

    if (!stage61_quest_log_pair_is_enabled(row)) {
        stage61_quest_log_finish_source_transition();
        return;
    }
    if (stage61_current_in_source_component(location))
        return;

    recorded = 0u;
    if (location == 5u || location == 6u)
        recorded = stage61_quest_log_record_shared_map_exit(5u, 6u, 1u, 0u);
    else if (location == 3u || location == 4u)
        recorded = stage61_quest_log_record_shared_map_exit(3u, 4u, 0u, 0u);
    else if (location == 22u || location == 23u)
        recorded = stage61_quest_log_record_warp_variant(22u, 0u);
    else if (location == 42u || location == 43u)
        recorded = stage61_quest_log_record_warp_variant(42u, 0u);
    else if (stage61_current_matches_pair_side(row, 2u)) {
        stage61_record_departed(
            stage61_departed_inside_section(row, 0u), location
        );
        recorded = 1u;
    }

    /* stage61_record_departed already cleared a successful transition.  A
     * mismatch (including warpId outside 0/1) clears the same pending bit.
     * Either way, entering a different reviewed interior can arm immediately. */
    if (!recorded)
        stage61_quest_log_clear_pending();
    stage61_quest_log_arm_current_source();
}

STAGE61_EXPORT(Stage61MapSection_QuestLog_CheckDepartingIndoorsMap)
void Stage61MapSection_QuestLog_CheckDepartingIndoorsMap(void)
{
    u8 index;
    u8 imported;

    /* A map-load Check must never overwrite a transition already in flight. */
    if (FN_FLAG_GET(STAGE61_FLAG_SYS_QL_DEPARTED))
        return;
    imported = is_imported_kanto_context();
    for (index = 0u; index < STAGE61_QUEST_LOG_PAIR_COUNT; ++index) {
        const u8 *row = stage61_quest_log_pair_for_namespace(index, imported);
        if (!stage61_quest_log_pair_is_enabled(row)
                || !stage61_current_matches_pair_side(row, 0u))
            continue;
        FN_VAR_SET(STAGE61_VAR_QL_ENTRANCE, index);
        FN_FLAG_SET(STAGE61_FLAG_SYS_QL_DEPARTED);
        return;
    }
}

STAGE61_EXPORT(Stage61MapSection_QuestLog_TryRecordDepartedLocation)
void Stage61MapSection_QuestLog_TryRecordDepartedLocation(void)
{
    u16 location_value;
    u8 location;

    if (!FN_FLAG_GET(STAGE61_FLAG_SYS_QL_DEPARTED))
        return;
    location_value = FN_VAR_GET(STAGE61_VAR_QL_ENTRANCE);
    if (location_value >= STAGE61_QUEST_LOG_PAIR_COUNT) {
        stage61_quest_log_clear_pending();
        if (is_imported_kanto_context())
            stage61_quest_log_arm_current_project();
        else
            stage61_quest_log_arm_current_source();
        return;
    }
    location = (u8)location_value;
    if (is_imported_kanto_context())
        stage61_quest_log_try_record_project(location);
    else
        stage61_quest_log_try_record_source(location);
}

STAGE61_EXPORT(Stage61MapSection_CreateTownMapRoamerSprites)
void Stage61MapSection_CreateTownMapRoamerSprites(void)
{
    u32 index;

    if (FN_GET_SELECTED_REGION_MAP() != 0u)
        return;
    for (index = 0u; index < 10u; ++index) {
        volatile u8 *roamer = G_ROAMERS + index * 0x18u;
        const u8 *header;
        u16 species = stage61_read16(roamer + 8u);
        u32 personality;
        u8 group;
        u8 map;
        u8 section;
        u8 table_index;
        u8 sprite_id;
        u16 width;
        u16 height;
        s16 x;
        s16 y;

        if (species == 0u)
            continue;
        group = roamer[0x16u];
        map = roamer[0x17u];
        header = FN_GET_MAP_HEADER(group, map);
        if (header == (const u8 *)0)
            continue;
        section = normalize_section_for_physical_group(group, header[0x14]);
        if (section < 88u || section > 196u)
            continue;
        table_index = (u8)(section - 88u);
        x = (s16)(8u * STOCK_ROAMER_CORNERS[(u32)table_index * 2u]);
        y = (s16)(8u * STOCK_ROAMER_CORNERS[
            (u32)table_index * 2u + 1u
        ]);
        width = STOCK_ROAMER_DIMENSIONS[(u32)table_index * 2u];
        height = STOCK_ROAMER_DIMENSIONS[(u32)table_index * 2u + 1u];
        if (width > 1u)
            x = (s16)(x + (s16)(4u * width));
        if (height > 1u)
            y = (s16)(y + (s16)(4u * height));
        personality = stage61_read32(roamer + 4u);
        FN_LOAD_MON_ICON_PALETTES();
        sprite_id = FN_CREATE_MON_ICON(
            species, FN_SPRITE_CB_POKE_ICON,
            (s16)(x + 36), (s16)(y + 28), 0u, personality, 0u
        );
        if (sprite_id < 64u) {
            volatile u8 *sprite = G_SPRITES + (u32)sprite_id * 68u;
            sprite[5] = (u8)((sprite[5] & (u8)~0x0Cu) | 0x08u);
            sprite[0x3Eu] |= 0x04u;
        }
    }
}

/*
 * Stage35's ChangeKit keys contextual rematches by the trainerbattle command
 * data address.  Stage61 clones each EOS-intro command into separate normal
 * and rematch branches, so those addresses no longer match the immutable
 * Stage35 table.  Resolve only the exact relocated tuples here; every stock,
 * unrelocated, or context-free caller continues through the published
 * ChangeKit wrapper and therefore retains its original progression logic.
 */
STAGE61_EXPORT(Stage61Trainer_GetRematchTrainerId)
u16 Stage61Trainer_GetRematchTrainerId(u16 trainer_id)
{
    u32 address = *G_CHANGEKIT_COMMAND_DATA_ADDRESS;
    u16 source = *G_CHANGEKIT_COMMAND_SOURCE;
    size_t low = 0u;
    size_t high = STAGE61_TRAINER_REMATCH_ALIAS_COUNT;

    if (address != 0u && source == trainer_id) {
        while (low < high) {
            size_t middle = low + ((high - low) >> 1);
            u32 candidate = TRAINER_REMATCH_ALIASES[
                middle
            ].command_data_address;
            if (candidate < address)
                low = middle + 1u;
            else
                high = middle;
        }
        if (low < STAGE61_TRAINER_REMATCH_ALIAS_COUNT
            && TRAINER_REMATCH_ALIASES[low].command_data_address == address
            && TRAINER_REMATCH_ALIASES[low].source_trainer_id == trainer_id)
            return TRAINER_REMATCH_ALIASES[low].target_trainer_id;
    }
    return FN_CHANGEKIT_GET_REMATCH(trainer_id);
}

STAGE61_EXPORT(Stage61DisplayNpcEvent_SetFlyWarpDestination)
void Stage61DisplayNpcEvent_SetFlyWarpDestination(u16 mapsec)
{
    const u8 *row;
    const u8 *legacy;
    u16 index;

    if (mapsec < STAGE61_KANTO_SECTION_COUNT) {
        row = KANTO_FLY_RECORDS + (u32)mapsec * 6u;
        legacy = KANTO_FLY_DESTINATIONS + (u32)mapsec * 3u;
        if ((row[4] & 1u) == 0u) {
            FN_RETURN_TO_FIELD_FROM_FLY_MAP_SELECT();
            return;
        }
        FN_SET_WARP_DESTINATION((s8)row[0], (s8)row[1], -1,
                                (s8)row[2], (s8)row[3]);
        FN_SET_USED_FLY_QUEST_LOG_EVENT(legacy);
        FN_RETURN_TO_FIELD_FROM_FLY_MAP_SELECT();
        return;
    }

    index = (u16)(mapsec - STAGE61_STOCK_SECTION_START);
    if (index >= STAGE61_STOCK_SECTION_COUNT) {
        FN_RETURN_TO_FIELD_FROM_FLY_MAP_SELECT();
        return;
    }
    row = STOCK_FLY_DESTINATIONS + index * 3u;
    if (row[2] != 0u) {
        FN_SET_WARP_DESTINATION_TO_HEAL_LOCATION(row[2]);
        FN_SET_USED_FLY_QUEST_LOG_EVENT(row);
    } else {
        FN_SET_WARP_DESTINATION_TO_MAP_WARP((s8)row[0], (s8)row[1], -1);
    }
    FN_RETURN_TO_FIELD_FROM_FLY_MAP_SELECT();
}

STAGE61_EXPORT(Stage61DisplayNpcEvent_Probe)
u32 Stage61DisplayNpcEvent_Probe(u32 query)
{
    if (query == 0u)
        return STAGE61_ABI_VERSION;
    if (query == 1u)
        return STAGE61_KANTO_SECTION_COUNT;
    if (query == 2u)
        return (u32)STAGE61_KANTO_NAME_TABLE;
    if (query == 3u)
        return (u32)STAGE61_KANTO_FLY_RECORDS;
    if (query == 4u)
        return (u32)STAGE61_KANTO_REGION_GRID;
    if (query == 5u)
        return (u32)STAGE61_KANTO_VISIT_FLAGS;
    return 0u;
}
