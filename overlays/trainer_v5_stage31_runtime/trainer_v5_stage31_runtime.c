/*
 * USER-TRAINER-V5-STAGE31-INTEGRATION-FOUNDATION
 *
 * Stage 31 keeps the established 0x20 Trainer / 16-byte party ABI, while this
 * hook layer supplies the V5 fields that ABI cannot represent: exact IV,
 * ability slot, nature, and all six EVs.  Trainer defeat-state translation is
 * restricted to trainer-specific entry points; the global FlagGet/Set/Clear
 * APIs remain byte-identical for every unrelated game subsystem.
 */

#include <stddef.h>
#include <stdint.h>

#include "trainer_v5_stage31_generated.h"

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;

#define PTR(type, address) ((type)(uintptr_t)(address))
#define TRAINER_V5_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))

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

enum {
    TRAINER_V5_FLAG_START = 0x0500,
    TRAINER_V5_OPPONENT_SIDE = 1,
    TRAINER_V5_MAX_PARTY_SIZE = 6,
    TRAINER_V5_MON_SIZE = 100,
    TRAINER_V5_NATURE_MINT_OFFSET = 0x0F,
    TRAINER_V5_SPECIES_OFFSET = 0x20,
    TRAINER_V5_EV_HP_OFFSET = 0x38,
    TRAINER_V5_EV_ATK_OFFSET = 0x39,
    TRAINER_V5_EV_DEF_OFFSET = 0x3A,
    TRAINER_V5_EV_SPEED_OFFSET = 0x3B,
    TRAINER_V5_EV_SPATK_OFFSET = 0x3C,
    TRAINER_V5_EV_SPDEF_OFFSET = 0x3D,
    TRAINER_V5_MET_BITS_OFFSET = 0x46,
    TRAINER_V5_IV_BITS_OFFSET = 0x48,
    TRAINER_V5_HP_OFFSET = 0x56,
    TRAINER_V5_MAX_HP_OFFSET = 0x58,
    TRAINER_V5_HIDDEN_ABILITY_MASK = 0x1000,
    TRAINER_V5_IV_FIELD_MASK = 0x3FFFFFFF,
    TRAINER_V5_ABILITY_NUM_MASK = 0x80000000u,
    TRAINER_V5_PROBE_MAGIC = 0x56353231u /* V521 */
};

enum {
    TRAINER_V5_INITIAL_DOUBLE_DATA_ADDRESS = 0x08E032C1u,
    TRAINER_V5_INITIAL_DOUBLE_KIND = 4u,
    TRAINER_V5_INITIAL_DOUBLE_PHYSICAL_ID = 702u,
    TRAINER_V5_INITIAL_DOUBLE_INSTANCE_ID = 1342u
};

typedef u8 (*FlagFn)(u16 flag);
typedef u16 (*GetTrainerFlagFn)(void);
typedef u16 (*GetRematchFn)(u16 trainer_id);
typedef void (*BuildTrainerPartyFn)(void);
typedef void (*CalculateMonStatsFn)(void *mon);
typedef const u8 *(*ConfigureTrainerBattleFn)(const u8 *data);

#define FN_GET_TRAINER_FLAG PTR(GetTrainerFlagFn, VEGA_GET_TRAINER_FLAG_ADDRESS)
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
#define G_ENEMY_PARTY PTR(u8 *, VEGA_ENEMY_PARTY_ADDRESS)
#define G_TRAINER_OPPONENT_A \
    (*PTR(volatile u16 *, VEGA_TRAINER_OPPONENT_A_ADDRESS))

_Static_assert(sizeof(struct TrainerV5MemberSidecarV1) == 16u,
               "Trainer V5 sidecar ABI must remain 16 bytes");
_Static_assert(sizeof(struct TrainerV5RematchMapV1) == 4u,
               "Trainer V5 rematch map ABI must remain 4 bytes");
_Static_assert(sizeof(struct TrainerV5FlagMapV1) == 4u,
               "Trainer V5 flag map ABI must remain 4 bytes");
_Static_assert(TRAINER_V5_GENERATED_ENCOUNTER_COUNT == 25u,
               "Stage 31 selected scope must remain 25 encounters");
_Static_assert(TRAINER_V5_GENERATED_SIDECAR_COUNT == 71u,
               "Stage 31 selected sidecar count must remain 71");

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

static u16 map_flag(u16 flag)
{
    size_t low = 0u;
    size_t high = TRAINER_V5_GENERATED_FLAG_MAP_COUNT;
    while (low < high) {
        size_t middle = low + ((high - low) >> 1);
        u16 external = gTrainerV5FlagMap[middle].external_flag;
        if (external < flag)
            low = middle + 1u;
        else
            high = middle;
    }
    if (low < TRAINER_V5_GENERATED_FLAG_MAP_COUNT
        && gTrainerV5FlagMap[low].external_flag == flag)
        return gTrainerV5FlagMap[low].physical_flag;
    return flag;
}

static const struct TrainerV5MemberSidecarV1 *find_sidecar(u16 trainer_id,
                                                            u8 side,
                                                            u8 slot)
{
    u32 target = ((u32)trainer_id << 16) | ((u32)side << 8) | slot;
    size_t low = 0u;
    size_t high = TRAINER_V5_GENERATED_SIDECAR_COUNT;
    while (low < high) {
        size_t middle = low + ((high - low) >> 1);
        const struct TrainerV5MemberSidecarV1 *row =
            &gTrainerV5MemberSidecars[middle];
        u32 current = ((u32)row->trainer_id << 16)
            | ((u32)row->side << 8) | row->slot;
        if (current < target)
            low = middle + 1u;
        else
            high = middle;
    }
    if (low >= TRAINER_V5_GENERATED_SIDECAR_COUNT)
        return NULL;
    if (gTrainerV5MemberSidecars[low].trainer_id != trainer_id
        || gTrainerV5MemberSidecars[low].side != side
        || gTrainerV5MemberSidecars[low].slot != slot)
        return NULL;
    return &gTrainerV5MemberSidecars[low];
}

static u32 repeated_iv_bits(u8 iv)
{
    u32 value = (u32)(iv & 31u);
    return value | (value << 5) | (value << 10) | (value << 15)
        | (value << 20) | (value << 25);
}

static void apply_sidecar(u8 *mon,
                          const struct TrainerV5MemberSidecarV1 *row)
{
    u16 met_bits;
    u32 iv_bits;
    u16 max_hp;

    if (read_u16(mon + TRAINER_V5_SPECIES_OFFSET) != row->species_id)
        return;

    /* natureMint stores nature + 1; zero means personality-derived nature. */
    mon[TRAINER_V5_NATURE_MINT_OFFSET] = (u8)(row->nature_id + 1u);

    met_bits = read_u16(mon + TRAINER_V5_MET_BITS_OFFSET);
    met_bits &= (u16)~TRAINER_V5_HIDDEN_ABILITY_MASK;
    if (row->ability_mode == TRAINER_V5_ABILITY_HIDDEN)
        met_bits |= TRAINER_V5_HIDDEN_ABILITY_MASK;
    write_u16(mon + TRAINER_V5_MET_BITS_OFFSET, met_bits);

    iv_bits = read_u32(mon + TRAINER_V5_IV_BITS_OFFSET);
    iv_bits &= ~TRAINER_V5_IV_FIELD_MASK;
    iv_bits |= repeated_iv_bits(row->iv);
    if (row->ability_mode == TRAINER_V5_ABILITY_SECONDARY)
        iv_bits |= TRAINER_V5_ABILITY_NUM_MASK;
    else
        iv_bits &= ~TRAINER_V5_ABILITY_NUM_MASK;
    write_u32(mon + TRAINER_V5_IV_BITS_OFFSET, iv_bits);

    mon[TRAINER_V5_EV_HP_OFFSET] = row->hp_ev;
    mon[TRAINER_V5_EV_ATK_OFFSET] = row->atk_ev;
    mon[TRAINER_V5_EV_DEF_OFFSET] = row->def_ev;
    mon[TRAINER_V5_EV_SPEED_OFFSET] = row->speed_ev;
    mon[TRAINER_V5_EV_SPATK_OFFSET] = row->sp_atk_ev;
    mon[TRAINER_V5_EV_SPDEF_OFFSET] = row->sp_def_ev;

    FN_CALCULATE_MON_STATS(mon);
    max_hp = read_u16(mon + TRAINER_V5_MAX_HP_OFFSET);
    write_u16(mon + TRAINER_V5_HP_OFFSET, max_hp);
}

TRAINER_V5_EXPORT(TrainerV5Runtime_Probe)
u32 TrainerV5Runtime_Probe(u32 selector)
{
    switch (selector) {
    case 0u: return TRAINER_V5_PROBE_MAGIC;
    case 1u: return TRAINER_V5_GENERATED_ENCOUNTER_COUNT;
    case 2u: return TRAINER_V5_GENERATED_SIDECAR_COUNT;
    case 3u: return TRAINER_V5_GENERATED_REMATCH_MAP_COUNT;
    case 4u: return TRAINER_V5_GENERATED_FLAG_MAP_COUNT;
    case 5u: return TRAINER_V5_GENERATED_TRAINER_TABLE_COUNT;
    default: return 0u;
    }
}

TRAINER_V5_EXPORT(TrainerV5Runtime_ScriptFlagGet)
u8 TrainerV5Runtime_ScriptFlagGet(void)
{
    return FN_FLAG_GET(map_flag(FN_GET_TRAINER_FLAG()));
}

TRAINER_V5_EXPORT(TrainerV5Runtime_ScriptFlagSet)
u8 TrainerV5Runtime_ScriptFlagSet(void)
{
    return FN_FLAG_SET(map_flag(FN_GET_TRAINER_FLAG()));
}

TRAINER_V5_EXPORT(TrainerV5Runtime_HasTrainerBeenFought)
u8 TrainerV5Runtime_HasTrainerBeenFought(u16 trainer_id)
{
    return FN_FLAG_GET(map_flag((u16)(TRAINER_V5_FLAG_START + trainer_id)));
}

TRAINER_V5_EXPORT(TrainerV5Runtime_SetTrainerFlag)
u8 TrainerV5Runtime_SetTrainerFlag(u16 trainer_id)
{
    return FN_FLAG_SET(map_flag((u16)(TRAINER_V5_FLAG_START + trainer_id)));
}

TRAINER_V5_EXPORT(TrainerV5Runtime_ClearTrainerFlag)
u8 TrainerV5Runtime_ClearTrainerFlag(u16 trainer_id)
{
    return FN_FLAG_CLEAR(map_flag((u16)(TRAINER_V5_FLAG_START + trainer_id)));
}

TRAINER_V5_EXPORT(TrainerV5Runtime_GetRematchTrainerId)
u16 TrainerV5Runtime_GetRematchTrainerId(u16 trainer_id)
{
    u16 resolved = FN_GET_REMATCH(trainer_id);
    size_t low = 0u;
    size_t high = TRAINER_V5_GENERATED_REMATCH_MAP_COUNT;

    /*
     * The stock selector owns Vs Seeker availability and story-gate logic.
     * A zero result must remain zero; only an actually selected rematch party
     * is replaced by the V5 record bound to this physical trainer.
     */
    if (resolved == 0u)
        return 0u;
    while (low < high) {
        size_t middle = low + ((high - low) >> 1);
        u16 source = gTrainerV5RematchMap[middle].source_trainer_id;
        if (source < trainer_id)
            low = middle + 1u;
        else
            high = middle;
    }
    if (low < TRAINER_V5_GENERATED_REMATCH_MAP_COUNT
        && gTrainerV5RematchMap[low].source_trainer_id == trainer_id)
        return gTrainerV5RematchMap[low].v5_trainer_id;
    return resolved;
}

TRAINER_V5_EXPORT(TrainerV5Runtime_ConfigureTrainerBattle)
const u8 *TrainerV5Runtime_ConfigureTrainerBattle(const u8 *data)
{
    const u8 *next = FN_CONFIGURE_TRAINER_BATTLE(data);

    /* Keep the rooted script on physical trainer 702 so sight/defeat flag
     * checks stay inside the stock save ABI. Rebind only after CFRU consumes
     * the exact kind-4 trainerbattle arguments. */
    if ((uintptr_t)data == TRAINER_V5_INITIAL_DOUBLE_DATA_ADDRESS
        && data[0] == TRAINER_V5_INITIAL_DOUBLE_KIND
        && read_u16(data + 1u) == TRAINER_V5_INITIAL_DOUBLE_PHYSICAL_ID)
        G_TRAINER_OPPONENT_A = TRAINER_V5_INITIAL_DOUBLE_INSTANCE_ID;
    return next;
}

TRAINER_V5_EXPORT(TrainerV5Runtime_BuildTrainerPartySetup)
void TrainerV5Runtime_BuildTrainerPartySetup(void)
{
    u16 trainer_id;
    u8 index;

    FN_BUILD_TRAINER_PARTY();
    trainer_id = G_TRAINER_OPPONENT_A;
    for (index = 0u; index < TRAINER_V5_MAX_PARTY_SIZE; ++index) {
        const struct TrainerV5MemberSidecarV1 *row =
            find_sidecar(trainer_id, TRAINER_V5_OPPONENT_SIDE, index);
        if (row != NULL)
            apply_sidecar(G_ENEMY_PARTY + (u32)index * TRAINER_V5_MON_SIZE, row);
    }
}

/* Exported table anchors make static and exact-ROM audits independent of ELF. */
TRAINER_V5_EXPORT(TrainerV5Runtime_SidecarTable)
const struct TrainerV5MemberSidecarV1 *TrainerV5Runtime_SidecarTable(void)
{
    return gTrainerV5MemberSidecars;
}

TRAINER_V5_EXPORT(TrainerV5Runtime_RematchTable)
const struct TrainerV5RematchMapV1 *TrainerV5Runtime_RematchTable(void)
{
    return gTrainerV5RematchMap;
}

TRAINER_V5_EXPORT(TrainerV5Runtime_FlagTable)
const struct TrainerV5FlagMapV1 *TrainerV5Runtime_FlagTable(void)
{
    return gTrainerV5FlagMap;
}
