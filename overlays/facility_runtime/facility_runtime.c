#include "facility_runtime.h"

#include <stddef.h>
#include <stdint.h>

#include "../save_migration/save_migration.h"

#define FACILITY_PARTY_SIZE 6u
#define FACILITY_SELECTED_SIZE 3u
#define FACILITY_MON_SIZE 100u
#define FACILITY_PROBE_MARKER 0xFA20u
#define FACILITY_EXCHANGE_MAGIC 0x58434846u /* "FHCX" */

#define FACILITY_FLAG 0x0930u
#define FACILITY_NUMBER_VAR 0x403Au
#define FACILITY_PARTY_SIZE_VAR 0x5015u
#define FACILITY_LEVEL_VAR 0x5016u
#define FACILITY_BATTLE_TYPE_VAR 0x5017u
#define FACILITY_TIER_VAR 0x5018u

#define FACILITY_NUMBER_TOWER 0u
#define FACILITY_BATTLE_SINGLE_RANDOM 4u
#define FACILITY_TIER_STANDARD 0u
#define FACILITY_LEVEL 50u
#define FACILITY_BATTLE_OUTCOME_WON 1u
#define FACILITY_REWARD_BP 9u
#define FACILITY_MODE_TRIAL 0u
#define FACILITY_REWARD_TRIAL 0u

#define FACILITY_MON_DATA_SPECIES 11u
#define FACILITY_DEX_SET_SEEN 2u

#define FACILITY_PLAYER_PARTY ((FacilityPokemon *)(uintptr_t)0x020241E4u)
#define FACILITY_ENEMY_PARTY ((FacilityPokemon *)(uintptr_t)0x02023F8Cu)
#define FACILITY_PLAYER_PARTY_COUNT (*(volatile uint8_t *)(uintptr_t)0x02023F89u)
#define FACILITY_BATTLE_OUTCOME (*(volatile uint8_t *)(uintptr_t)0x02023DEAu)
#define FACILITY_SELECTED_ORDER ((volatile uint8_t *)(uintptr_t)0x0203C6C8u)
#define FACILITY_SPECIAL_RESULT (*(volatile uint16_t *)(uintptr_t)0x02037004u)
#define FACILITY_VAR_8000 (*(volatile uint16_t *)(uintptr_t)0x02036FECu)
#define FACILITY_VAR_8001 (*(volatile uint16_t *)(uintptr_t)0x02036FEEu)
#define FACILITY_EXCHANGE_SCRATCH ((FacilityExchangeScratch *)(uintptr_t)VEGA_SAVE_TRANSACTION_SCRATCH_ADDRESS)

#define FACILITY_GET_MON_DATA ((uint32_t (*)(FacilityPokemon *, int, void *))(uintptr_t)0x0803F355u)
#define FACILITY_CALCULATE_PARTY_COUNT ((uint8_t (*)(void))(uintptr_t)0x08040331u)
#define FACILITY_SPECIES_TO_NATIONAL ((uint16_t (*)(uint16_t))(uintptr_t)0x08042989u)
#define FACILITY_GET_SET_DEX ((uint8_t (*)(uint16_t, uint8_t))(uintptr_t)0x08088A51u)
#define FACILITY_RANDOM ((uint16_t (*)(void))(uintptr_t)0x0804448Du)
#define FACILITY_VAR_SET ((uint8_t (*)(uint16_t, uint16_t))(uintptr_t)0x0806DD79u)
#define FACILITY_FLAG_SET ((uint8_t (*)(uint16_t))(uintptr_t)0x0806DE75u)
#define FACILITY_FLAG_CLEAR ((uint8_t (*)(uint16_t))(uintptr_t)0x0806DE9Du)
#define FACILITY_ROM_MEMCPY ((void *(*)(void *, const void *, size_t))(uintptr_t)0x081C9D99u)
#define FACILITY_ROM_MEMSET ((void *(*)(void *, int, size_t))(uintptr_t)0x081C9DF9u)
#define FACILITY_TRY_WRITE_SECTOR ((uint8_t (*)(uint16_t, const void *))(uintptr_t)0x080DA9C1u)
#ifndef VEGA_FACILITY_GENERATE_RENTALS_ADDRESS
#error "VEGA_FACILITY_GENERATE_RENTALS_ADDRESS must come from the linked T06 contract"
#endif
#define FACILITY_GENERATE_RENTALS \
    ((void (*)(void))(uintptr_t)VEGA_FACILITY_GENERATE_RENTALS_ADDRESS)
#ifndef VEGA_FACILITY_GENERATE_TRAINER_ADDRESS
#error "VEGA_FACILITY_GENERATE_TRAINER_ADDRESS must come from the linked T06 contract"
#endif
#define FACILITY_GENERATE_TRAINER \
    ((uint16_t (*)(void))(uintptr_t)VEGA_FACILITY_GENERATE_TRAINER_ADDRESS)
#define FACILITY_HEAL_PLAYER_PARTY ((void (*)(void))(uintptr_t)0x080A1331u)
#ifndef VEGA_FACILITY_CONFIGURE_POLICY_ADDRESS
#error "VEGA_FACILITY_CONFIGURE_POLICY_ADDRESS must come from the linked T06 contract"
#endif
#define FACILITY_CONFIGURE_POLICY \
    ((uint8_t (*)(int, int, int))(uintptr_t)VEGA_FACILITY_CONFIGURE_POLICY_ADDRESS)

#define FACILITY_SAVE_BUFFER ((uint8_t *)(uintptr_t)0x020399B0u)
#define FACILITY_SECTOR31_IMAGE ((const uint8_t *)(uintptr_t)0x0203CF9Cu)
#define FACILITY_SECTOR_DATA_SIZE 0x0FF0u
#define FACILITY_SECTOR_SIZE 0x1000u
#define FACILITY_LEDGER_SECTOR 31u

#if defined(__GNUC__)
#define FACILITY_EXPORT __attribute__((used, externally_visible))
#else
#define FACILITY_EXPORT
#endif

typedef struct FacilityPokemon {
    uint8_t bytes[FACILITY_MON_SIZE];
} FacilityPokemon;

typedef struct FacilityExchangeScratch {
    uint32_t magic;
    FacilityPokemon mon;
    uint8_t reserved[VEGA_SAVE_TRANSACTION_SCRATCH_ADDRESS + 0x100u
                     - VEGA_SAVE_TRANSACTION_SCRATCH_ADDRESS
                     - sizeof(uint32_t) - sizeof(FacilityPokemon)];
} FacilityExchangeScratch;

_Static_assert(sizeof(FacilityPokemon) == VEGA_PARTY_MON_SIZE,
               "facility party ABI changed");
_Static_assert(sizeof(FacilityExchangeScratch) == 0x100u,
               "facility exchange scratch exceeds its reservation");

/* save_migration.c intentionally remains freestanding in the ROM image. */
void *memcpy(void *destination, const void *source, size_t size)
{
    return FACILITY_ROM_MEMCPY(destination, source, size);
}

void *memset(void *destination, int value, size_t size)
{
    return FACILITY_ROM_MEMSET(destination, value, size);
}

static void copy_bytes(void *destination, const void *source, size_t size)
{
    uint8_t *out = (uint8_t *)destination;
    const uint8_t *in = (const uint8_t *)source;
    size_t index;
    for (index = 0; index < size; ++index)
        out[index] = in[index];
}

static void clear_bytes(void *destination, size_t size)
{
    uint8_t *out = (uint8_t *)destination;
    size_t index;
    for (index = 0; index < size; ++index)
        out[index] = 0;
}

static uint8_t reduce_random(uint8_t value, uint8_t count)
{
    if (count <= 1u)
        return 0u;
    if (count == 2u)
        return (uint8_t)(value & 1u);
    if (count == 4u)
        return (uint8_t)(value & 3u);
    while (value >= count)
        value = (uint8_t)(value - count);
    return value;
}

static uint16_t species(const FacilityPokemon *mon)
{
    return (uint16_t)FACILITY_GET_MON_DATA((FacilityPokemon *)mon,
                                           FACILITY_MON_DATA_SPECIES, NULL);
}

static void set_result(uint16_t result)
{
    FACILITY_SPECIAL_RESULT = result;
}

static void normalize_selected_order(uint8_t selected_count)
{
    uint8_t index;
    for (index = 0; index < FACILITY_PARTY_SIZE; ++index)
        FACILITY_SELECTED_ORDER[index] = index < selected_count ? (uint8_t)(index + 1u) : 0u;
}

static void configure_trial_vars(uint8_t selected_count)
{
    FACILITY_VAR_SET(FACILITY_NUMBER_VAR, FACILITY_NUMBER_TOWER);
    FACILITY_VAR_SET(FACILITY_PARTY_SIZE_VAR, selected_count);
    FACILITY_VAR_SET(FACILITY_LEVEL_VAR, FACILITY_LEVEL);
    FACILITY_VAR_SET(FACILITY_BATTLE_TYPE_VAR, FACILITY_BATTLE_SINGLE_RANDOM);
    FACILITY_VAR_SET(FACILITY_TIER_VAR, FACILITY_TIER_STANDARD);
}

static uint8_t save_ledger_sector(void)
{
    FACILITY_ROM_MEMSET(FACILITY_SAVE_BUFFER, 0, FACILITY_SECTOR_SIZE);
    FACILITY_ROM_MEMCPY(FACILITY_SAVE_BUFFER, FACILITY_SECTOR31_IMAGE,
                        FACILITY_SECTOR_DATA_SIZE);
    return (uint8_t)(FACILITY_TRY_WRITE_SECTOR(
        FACILITY_LEDGER_SECTOR, FACILITY_SAVE_BUFFER) == 1u);
}

static int persist_callback(const VegaModernSaveData *data, size_t size, void *context)
{
    (void)data;
    (void)size;
    (void)context;
    return save_ledger_sector();
}

static int accept_callback(const VegaModernSaveData *data, size_t size, void *context)
{
    (void)data;
    (void)size;
    (void)context;
    return 1;
}

static void persist_current(void)
{
    VegaSaveFinalize(gVegaModernSaveData);
    (void)save_ledger_sector();
}

static uint8_t ledger_valid(void)
{
    return (uint8_t)(VegaSaveValidate(gVegaModernSaveData,
                                      VEGA_SAVE_LEDGER_SIZE) == VEGA_SAVE_OK);
}

static void mark_seen(const FacilityPokemon *mon)
{
    uint16_t mon_species = species(mon);
    uint16_t national;
    if (mon_species == 0u)
        return;
    national = FACILITY_SPECIES_TO_NATIONAL(mon_species);
    if (national != 0u && national <= VEGA_NATIONAL_DEX_COUNT)
        (void)FACILITY_GET_SET_DEX(national, FACILITY_DEX_SET_SEEN);
}

static void mark_party_seen(const FacilityPokemon *party)
{
    uint8_t index;
    for (index = 0; index < FACILITY_PARTY_SIZE; ++index)
        mark_seen(&party[index]);
}

static uint8_t unique_full_party(void)
{
    uint16_t observed[FACILITY_PARTY_SIZE];
    uint8_t left;
    uint8_t right;
    for (left = 0; left < FACILITY_PARTY_SIZE; ++left) {
        observed[left] = species(&FACILITY_PLAYER_PARTY[left]);
        if (observed[left] == 0u)
            return 0u;
        for (right = 0; right < left; ++right) {
            if (observed[left] == observed[right])
                return 0u;
        }
    }
    return 1u;
}

static void heal_rental_party(void)
{
    FACILITY_HEAL_PLAYER_PARTY();
}

static void clear_session_runtime(void)
{
    normalize_selected_order(0u);
    FACILITY_EXCHANGE_SCRATCH->magic = 0u;
    FACILITY_FLAG_CLEAR(FACILITY_FLAG);
    configure_trial_vars(FACILITY_SELECTED_SIZE);
}

static void restore_original(uint8_t reset_streak)
{
    uint8_t restored_count = 0u;
    if (!ledger_valid() || !gVegaModernSaveData->factory.snapshot_valid) {
        clear_session_runtime();
        return;
    }
    gVegaModernSaveData->factory.reward_pending = 0u;
    if (reset_streak)
        gVegaModernSaveData->factory.current_streak[FACILITY_MODE_TRIAL] = 0u;
    (void)VegaFactoryRestore(
        gVegaModernSaveData,
        (uint8_t (*)[VEGA_PARTY_MON_SIZE])FACILITY_PLAYER_PARTY,
        &restored_count,
        accept_callback,
        NULL);
    FACILITY_PLAYER_PARTY_COUNT = restored_count;
    clear_session_runtime();
    persist_current();
}

static void initialize_ledger_if_needed(void)
{
    if (!ledger_valid()) {
        VegaSaveInitNew(gVegaModernSaveData, 1u);
        persist_current();
    }
}

static uint8_t cache_random_opponent(void)
{
    uint8_t populated[FACILITY_PARTY_SIZE];
    uint8_t count = 0u;
    uint8_t index;
    for (index = 0; index < FACILITY_PARTY_SIZE; ++index) {
        if (species(&FACILITY_ENEMY_PARTY[index]) != 0u)
            populated[count++] = index;
    }
    if (count == 0u) {
        FACILITY_EXCHANGE_SCRATCH->magic = 0u;
        return 0u;
    }
    index = populated[reduce_random((uint8_t)FACILITY_RANDOM(), count)];
    copy_bytes(&FACILITY_EXCHANGE_SCRATCH->mon,
               &FACILITY_ENEMY_PARTY[index], sizeof(FacilityPokemon));
    mark_seen(&FACILITY_EXCHANGE_SCRATCH->mon);
    FACILITY_EXCHANGE_SCRATCH->magic = FACILITY_EXCHANGE_MAGIC;
    return 1u;
}

FACILITY_EXPORT uint16_t FacilityRuntime_Probe(void)
{
    set_result(FACILITY_PROBE_MARKER);
    return FACILITY_PROBE_MARKER;
}

FACILITY_EXPORT void FacilityRuntime_Recover(void)
{
    if (ledger_valid() && gVegaModernSaveData->factory.snapshot_valid)
        restore_original(1u);
    set_result(1u);
}

FACILITY_EXPORT void FacilityRuntime_Enter(void)
{
    uint8_t attempt;
    uint8_t original_count;

    initialize_ledger_if_needed();
    if (gVegaModernSaveData->factory.snapshot_valid)
        restore_original(1u);
    original_count = FACILITY_CALCULATE_PARTY_COUNT();
    if (VegaFactoryEnter(
            gVegaModernSaveData,
            (const uint8_t (*)[VEGA_PARTY_MON_SIZE])FACILITY_PLAYER_PARTY,
            original_count,
            persist_callback,
            NULL) != VEGA_SAVE_OK) {
        set_result(0u);
        return;
    }

    FACILITY_FLAG_SET(FACILITY_FLAG);
    configure_trial_vars(FACILITY_SELECTED_SIZE);
    FACILITY_VAR_8000 = 0u;
    FACILITY_VAR_8001 = 0u;
    if (!FACILITY_CONFIGURE_POLICY(0, 0, 0)) {
        restore_original(1u);
        set_result(0u);
        return;
    }
    for (attempt = 0; attempt < 4u; ++attempt) {
        FACILITY_GENERATE_RENTALS();
        (void)FACILITY_CALCULATE_PARTY_COUNT();
        if (FACILITY_PLAYER_PARTY_COUNT == FACILITY_PARTY_SIZE && unique_full_party())
            break;
    }
    if (attempt == 4u) {
        restore_original(1u);
        set_result(0u);
        return;
    }
    mark_party_seen(FACILITY_PLAYER_PARTY);
    normalize_selected_order(0u);
    gVegaModernSaveData->factory.reward_pending = 0u;
    FACILITY_EXCHANGE_SCRATCH->magic = 0u;
    persist_current();
    set_result(1u);
}

FACILITY_EXPORT void FacilityRuntime_CommitSelection(void)
{
    FacilityPokemon selected[FACILITY_SELECTED_SIZE];
    uint8_t used_mask = 0u;
    uint8_t index;

    if (!ledger_valid()
        || gVegaModernSaveData->factory.marker != VEGA_FACTORY_SNAPSHOT_COMMITTED
        || !gVegaModernSaveData->factory.snapshot_valid) {
        set_result(0u);
        return;
    }
    for (index = 0; index < FACILITY_SELECTED_SIZE; ++index) {
        uint8_t selected_slot = FACILITY_SELECTED_ORDER[index];
        uint8_t bit;
        if (selected_slot == 0u || selected_slot > FACILITY_PARTY_SIZE) {
            restore_original(1u);
            set_result(0u);
            return;
        }
        bit = (uint8_t)(1u << (selected_slot - 1u));
        if ((used_mask & bit) != 0u) {
            restore_original(1u);
            set_result(0u);
            return;
        }
        used_mask |= bit;
        copy_bytes(&selected[index], &FACILITY_PLAYER_PARTY[selected_slot - 1u],
                   sizeof(FacilityPokemon));
    }
    clear_bytes(FACILITY_PLAYER_PARTY,
                FACILITY_PARTY_SIZE * sizeof(FacilityPokemon));
    for (index = 0; index < FACILITY_SELECTED_SIZE; ++index)
        copy_bytes(&FACILITY_PLAYER_PARTY[index], &selected[index],
                   sizeof(FacilityPokemon));
    FACILITY_PLAYER_PARTY_COUNT = FACILITY_SELECTED_SIZE;
    normalize_selected_order(FACILITY_SELECTED_SIZE);
    heal_rental_party();
    configure_trial_vars(FACILITY_SELECTED_SIZE);
    if (VegaFactorySetBattleActive(gVegaModernSaveData,
                                   persist_callback, NULL) != VEGA_SAVE_OK) {
        restore_original(1u);
        set_result(0u);
        return;
    }
    set_result(1u);
}

FACILITY_EXPORT void FacilityRuntime_PrepareBattle(void)
{
    if (!ledger_valid()
        || gVegaModernSaveData->factory.marker != VEGA_FACTORY_BATTLE_ACTIVE
        || !gVegaModernSaveData->factory.snapshot_valid) {
        set_result(0u);
        return;
    }
    FACILITY_FLAG_SET(FACILITY_FLAG);
    configure_trial_vars(FACILITY_SELECTED_SIZE);
    normalize_selected_order(FACILITY_SELECTED_SIZE);
    heal_rental_party();
    FACILITY_VAR_8000 = 0u;
    FACILITY_VAR_8001 = 0u;
    (void)FACILITY_GENERATE_TRAINER();
    FACILITY_BATTLE_OUTCOME = 0u;
    if (!FACILITY_CONFIGURE_POLICY(0, 0, 0)) {
        restore_original(1u);
        set_result(0u);
        return;
    }
    persist_current();
    set_result(1u);
}

FACILITY_EXPORT void FacilityRuntime_AfterBattle(void)
{
    uint16_t next_streak;
    uint8_t outcome = (uint8_t)(FACILITY_BATTLE_OUTCOME & 0x7Fu);
    if (!ledger_valid() || !gVegaModernSaveData->factory.snapshot_valid) {
        clear_session_runtime();
        set_result(0u);
        return;
    }
    if (outcome != FACILITY_BATTLE_OUTCOME_WON) {
        restore_original(1u);
        set_result(0u);
        return;
    }

    heal_rental_party();
    (void)cache_random_opponent();
    if (gVegaModernSaveData->factory.reward_pending < 3u)
        gVegaModernSaveData->factory.reward_pending++;
    next_streak = gVegaModernSaveData->factory.current_streak[FACILITY_MODE_TRIAL];
    if (next_streak != UINT16_MAX)
        next_streak++;
    gVegaModernSaveData->factory.current_streak[FACILITY_MODE_TRIAL] = next_streak;
    if (gVegaModernSaveData->factory.best_streak[FACILITY_MODE_TRIAL] < next_streak)
        gVegaModernSaveData->factory.best_streak[FACILITY_MODE_TRIAL] = next_streak;
    persist_current();
    set_result(gVegaModernSaveData->factory.reward_pending >= 3u ? 2u : 1u);
}

FACILITY_EXPORT void FacilityRuntime_BeginExchange(void)
{
    if (!ledger_valid() || !gVegaModernSaveData->factory.snapshot_valid
        || FACILITY_EXCHANGE_SCRATCH->magic != FACILITY_EXCHANGE_MAGIC) {
        FacilityRuntime_SkipExchange();
        set_result(0u);
        return;
    }
    configure_trial_vars(1u);
    normalize_selected_order(0u);
    set_result(1u);
}

FACILITY_EXPORT void FacilityRuntime_CommitExchange(void)
{
    uint8_t selected_slot = FACILITY_SELECTED_ORDER[0];
    if (!ledger_valid() || !gVegaModernSaveData->factory.snapshot_valid
        || FACILITY_EXCHANGE_SCRATCH->magic != FACILITY_EXCHANGE_MAGIC
        || selected_slot == 0u || selected_slot > FACILITY_SELECTED_SIZE) {
        FacilityRuntime_SkipExchange();
        set_result(0u);
        return;
    }
    copy_bytes(&FACILITY_PLAYER_PARTY[selected_slot - 1u],
               &FACILITY_EXCHANGE_SCRATCH->mon, sizeof(FacilityPokemon));
    mark_seen(&FACILITY_PLAYER_PARTY[selected_slot - 1u]);
    FACILITY_EXCHANGE_SCRATCH->magic = 0u;
    configure_trial_vars(FACILITY_SELECTED_SIZE);
    normalize_selected_order(FACILITY_SELECTED_SIZE);
    heal_rental_party();
    persist_current();
    set_result(1u);
}

FACILITY_EXPORT void FacilityRuntime_SkipExchange(void)
{
    FACILITY_EXCHANGE_SCRATCH->magic = 0u;
    configure_trial_vars(FACILITY_SELECTED_SIZE);
    normalize_selected_order(FACILITY_SELECTED_SIZE);
    heal_rental_party();
    if (ledger_valid() && gVegaModernSaveData->factory.snapshot_valid)
        persist_current();
    set_result(1u);
}

FACILITY_EXPORT void FacilityRuntime_Complete(void)
{
    VegaSaveStatus status;
    if (!ledger_valid() || !gVegaModernSaveData->factory.snapshot_valid
        || gVegaModernSaveData->factory.reward_pending < 3u) {
        restore_original(1u);
        set_result(0u);
        return;
    }
    if ((gVegaModernSaveData->factory.reward_claim_bits
         & (1u << FACILITY_REWARD_TRIAL)) == 0u) {
        status = VegaFactoryClaimReward(gVegaModernSaveData,
                                        FACILITY_REWARD_TRIAL,
                                        FACILITY_REWARD_BP,
                                        persist_callback, NULL);
    } else {
        status = VegaFactoryAddBattlePoints(gVegaModernSaveData,
                                            FACILITY_REWARD_BP);
        gVegaModernSaveData->factory.reward_pending = 0u;
        persist_current();
    }
    if (status != VEGA_SAVE_OK) {
        restore_original(1u);
        set_result(0u);
        return;
    }
    restore_original(0u);
    set_result(FACILITY_REWARD_BP);
}

FACILITY_EXPORT void FacilityRuntime_Abort(void)
{
    restore_original(1u);
    set_result(1u);
}
