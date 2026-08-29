/*
 * USER-20260829-STAGE59-WILD-SPECIES-ROOT-REPAIR
 *
 * BuildTrainerPartySetup is a shared scheduler entrance: trainer battles and
 * every wild-battle producer can reach it.  The Stage35 ChangeKit wrapper used
 * gTrainerBattleOpponent_A without first proving that ChangeKit owned the
 * current battle.  Wild entrances intentionally leave that global untouched,
 * so the preceding trainer ID selected a sidecar and replaced the new wild
 * Pokemon's encrypted Species.
 *
 * This adapter retains the stock party builder for every entrance and invokes
 * the ChangeKit sidecar wrapper only while its packed runtime storage owns the
 * same live trainer.  It has no map or Species special cases.
 */

#include <stdint.h>

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;

#define PTR(type, address) ((type)(uintptr_t)(address))
#define STAGE60_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))

enum {
    STAGE60_ABI_MAGIC = 0x30365357u, /* "WS60" */
    CHANGEKIT_STORAGE_MAGIC = 0x54434653u,
    CHANGEKIT_PHASE_PENDING = 1u,
    CHANGEKIT_PHASE_ACTIVE = 2u,
    BATTLE_TYPE_TRAINER = 0x00000008u,
};

struct __attribute__((packed)) ChangeKitRuntimeState {
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

struct __attribute__((packed)) ChangeKitStorage {
    u32 magic;
    u32 magic_inverse;
    struct ChangeKitRuntimeState state;
    u16 archive_selection;
    u32 command_data_address;
    u16 command_source;
    u16 command_dispatch;
    u8 command_kind;
    u8 party_setup_pending;
    u16 party_setup_trainer_id;
    const void *current_gimmick;
    u32 ambiguous_bindings;
    u32 policy_failures;
};

typedef void (*PartyBuilderFn)(void);
typedef const u8 *(*ConfigureTrainerBattleFn)(const u8 *data);
typedef u8 (*PolicyEndFn)(void);

#define CHANGEKIT_STORAGE \
    PTR(volatile struct ChangeKitStorage *, 0x0203EDC0u)
#define G_TRAINER_OPPONENT_A (*PTR(volatile u16 *, 0x020385E2u))
#define G_BATTLE_TYPE_FLAGS (*PTR(volatile u32 *, 0x02022AACu))
#define FN_STOCK_BUILD_TRAINER_PARTY PTR(PartyBuilderFn, 0x09302D61u)
#define FN_CHANGEKIT_BUILD_TRAINER_PARTY PTR(PartyBuilderFn, 0x09303395u)
#define FN_STAGE59_CONFIGURE_TRAINER_BATTLE \
    PTR(ConfigureTrainerBattleFn, 0x09417631u)
#define FN_CHANGEKIT_POLICY_END PTR(PolicyEndFn, 0x0930373Du)

_Static_assert(sizeof(struct ChangeKitRuntimeState) == 14u,
               "ChangeKit runtime-state ABI changed");
_Static_assert(sizeof(struct ChangeKitStorage) == 48u,
               "ChangeKit storage ABI changed");

static u8 changekit_owns_current_trainer(void)
{
    volatile struct ChangeKitStorage *storage = CHANGEKIT_STORAGE;
    u8 phase;

    if (!storage->party_setup_pending
        || (G_BATTLE_TYPE_FLAGS & BATTLE_TYPE_TRAINER) == 0u
        || storage->magic != CHANGEKIT_STORAGE_MAGIC
        || storage->magic_inverse != (u32)~(u32)CHANGEKIT_STORAGE_MAGIC
        || storage->current_gimmick == (const void *)0)
        return 0u;
    phase = storage->state.phase;
    return (u8)((phase == CHANGEKIT_PHASE_PENDING
                 || phase == CHANGEKIT_PHASE_ACTIVE)
                && storage->party_setup_trainer_id == G_TRAINER_OPPONENT_A
                && storage->state.trainer_id
                    == storage->party_setup_trainer_id);
}

STAGE60_EXPORT(Stage60WildSpeciesRootRepair_ConfigureTrainerBattle)
const u8 *Stage60WildSpeciesRootRepair_ConfigureTrainerBattle(const u8 *data)
{
    volatile struct ChangeKitStorage *storage = CHANGEKIT_STORAGE;
    const u8 *next;

    storage->party_setup_pending = 0u;
    storage->party_setup_trainer_id = 0u;
    next = FN_STAGE59_CONFIGURE_TRAINER_BATTLE(data);
    storage->party_setup_pending = (u8)(
        storage->magic == CHANGEKIT_STORAGE_MAGIC
        && storage->magic_inverse == (u32)~(u32)CHANGEKIT_STORAGE_MAGIC
        && storage->current_gimmick != (const void *)0
        && storage->state.phase == CHANGEKIT_PHASE_PENDING);
    storage->party_setup_trainer_id = storage->party_setup_pending
        ? G_TRAINER_OPPONENT_A : 0u;
    return next;
}

STAGE60_EXPORT(Stage60WildSpeciesRootRepair_PolicyEnd)
u8 Stage60WildSpeciesRootRepair_PolicyEnd(void)
{
    u8 result = FN_CHANGEKIT_POLICY_END();
    volatile struct ChangeKitStorage *storage = CHANGEKIT_STORAGE;

    storage->party_setup_pending = 0u;
    storage->party_setup_trainer_id = 0u;
    return result;
}

STAGE60_EXPORT(Stage60WildSpeciesRootRepair_BuildTrainerPartySetup)
void Stage60WildSpeciesRootRepair_BuildTrainerPartySetup(void)
{
    volatile struct ChangeKitStorage *storage = CHANGEKIT_STORAGE;
    u8 owned = changekit_owns_current_trainer();

    storage->party_setup_pending = 0u;
    storage->party_setup_trainer_id = 0u;
    if (owned)
        FN_CHANGEKIT_BUILD_TRAINER_PARTY();
    else
        FN_STOCK_BUILD_TRAINER_PARTY();
}

STAGE60_EXPORT(Stage60WildSpeciesRootRepair_Probe)
u32 Stage60WildSpeciesRootRepair_Probe(u32 query)
{
    if (query == 0u)
        return STAGE60_ABI_MAGIC;
    if (query == 1u)
        return 0x090DD2A4u;
    if (query == 2u)
        return 0x09302D61u;
    if (query == 3u)
        return 0x09303395u;
    if (query == 4u)
        return 0x0203EDC0u;
    if (query == 5u)
        return 0x09417631u;
    if (query == 6u)
        return 0x0930373Du;
    return 0u;
}
