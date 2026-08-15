#include <assert.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>

#include "../overlays/acquisition_runtime/acquisition_runtime.h"
#include "../overlays/acquisition_runtime/acquisition_engine_adapter.h"
#include "../overlays/acquisition_runtime/acquisition_save_migration.h"
#include "../generated/acquisition_event_defs.h"
#include "../generated/acquisition_host_defs.h"

static VegaAcqPendingTransaction sPending;
static uint8_t sRegistered[1621];
static uint8_t sClaims[VEGA_ACQ_EVENT_COUNT];
static uint8_t sUnlock = 1u;
static uint8_t sCondition = 1u;
static uint16_t sPreflight = VEGA_ACQ_RESULT_SUCCESS;
static uint16_t sStage = VEGA_ACQ_RESULT_SUCCESS;
static uint16_t sCapture = VEGA_ACQ_RESULT_BATTLE_STARTED;
static uint16_t sSelected = VEGA_ACQ_NO_INDEX;
static unsigned sPersistCalls;
static unsigned sFailPersistCall;
static unsigned sRollbackCount;
static unsigned sFinalizeCount;
static unsigned sFinalizeMemoryCount;
static unsigned sStageCount;
static uint16_t sLastShownResult;

static uint16_t event_index(const VegaAcqEventDef *def)
{
    return (uint16_t)(def - gVegaAcqEventDefs);
}

static void reset_all(void)
{
    memset(&sPending, 0, sizeof(sPending));
    memset(sRegistered, 0, sizeof(sRegistered));
    memset(sClaims, 0, sizeof(sClaims));
    sUnlock = 1u;
    sCondition = 1u;
    sPreflight = VEGA_ACQ_RESULT_SUCCESS;
    sStage = VEGA_ACQ_RESULT_SUCCESS;
    sCapture = VEGA_ACQ_RESULT_BATTLE_STARTED;
    sSelected = VEGA_ACQ_NO_INDEX;
    sPersistCalls = 0u;
    sFailPersistCall = 0u;
    sRollbackCount = 0u;
    sFinalizeCount = 0u;
    sFinalizeMemoryCount = 0u;
    sStageCount = 0u;
    sLastShownResult = 0u;
}

static void reset_controls(void)
{
    sUnlock = 1u;
    sCondition = 1u;
    sPreflight = VEGA_ACQ_RESULT_SUCCESS;
    sStage = VEGA_ACQ_RESULT_SUCCESS;
    sCapture = VEGA_ACQ_RESULT_BATTLE_STARTED;
    sSelected = VEGA_ACQ_NO_INDEX;
    sPersistCalls = 0u;
    sFailPersistCall = 0u;
    sRollbackCount = 0u;
    sFinalizeCount = 0u;
    sFinalizeMemoryCount = 0u;
    sStageCount = 0u;
}

uint16_t VegaAcqEngine_AdapterProbe(void) { return VEGA_ACQ_ENGINE_ADAPTER_ABI_VERSION; }
VegaAcqPendingTransaction *VegaAcqEngine_GetPending(void) { return &sPending; }
uint8_t VegaAcqEngine_IsUnlockSatisfied(const char *key) { (void)key; return sUnlock; }
uint8_t VegaAcqEngine_IsEventConditionSatisfied(const VegaAcqEventDef *def) { (void)def; return sCondition; }
uint8_t VegaAcqEngine_IsSpeciesRegistered(uint16_t species) { return species < 1621u ? sRegistered[species] : 0u; }
uint8_t VegaAcqEngine_SetSpeciesRegistered(uint16_t species, uint8_t value) { if (species >= 1621u) return 0u; sRegistered[species] = value; return 1u; }
uint8_t VegaAcqEngine_GetClaimCount(const VegaAcqEventDef *def) { return sClaims[event_index(def)]; }
uint8_t VegaAcqEngine_SetClaimCount(const VegaAcqEventDef *def, uint8_t value) { sClaims[event_index(def)] = value; return 1u; }
uint16_t VegaAcqEngine_Preflight(const VegaAcqEventDef *def) { (void)def; return sPreflight; }
uint16_t VegaAcqEngine_StartCaptureBattle(const VegaAcqEventDef *def) { (void)def; return sCapture; }
uint16_t VegaAcqEngine_StageOperation(const VegaAcqEventDef *def, uint32_t *token) { (void)def; ++sStageCount; *token = 0x12345678u; return sStage; }
void VegaAcqEngine_RollbackOperation(const VegaAcqEventDef *def, uint32_t token) { (void)def; (void)token; ++sRollbackCount; }
void VegaAcqEngine_FinalizeOperation(const VegaAcqEventDef *def, uint32_t token) { (void)def; (void)token; ++sFinalizeCount; }
uint8_t VegaAcqEngine_IsOperationDurable(const VegaAcqEventDef *def, uint32_t token) { (void)def; (void)token; return 1u; }
void VegaAcqEngine_FinalizeInMemory(void) { ++sFinalizeMemoryCount; }
uint8_t VegaAcqEngine_PersistAll(void) { ++sPersistCalls; return (uint8_t)(sFailPersistCall == 0u || sPersistCalls != sFailPersistCall); }
uint16_t VegaAcqEngine_SelectHostEvent(const uint16_t *indices, uint16_t count) { (void)indices; (void)count; return sSelected; }
void VegaAcqEngine_ShowResult(uint16_t event, uint16_t result) { (void)event; sLastShownResult = result; }

static uint8_t migration_registered(uint16_t species, void *context)
{
    uint16_t wanted = *(uint16_t *)context;
    return (uint8_t)(species == wanted);
}

static void test_capture_retry_and_commit(void)
{
    uint16_t index = VegaAcq_FindEventIndex("EVENT_SPECIAL_NATIONAL_0144");
    const VegaAcqEventDef *def = &gVegaAcqEventDefs[index];
    assert(index != VEGA_ACQ_NO_INDEX);
    sUnlock = 0u;
    assert(VegaAcq_Begin(index) == VEGA_ACQ_RESULT_LOCKED);
    sUnlock = 1u;
    assert(VegaAcq_Begin(index) == VEGA_ACQ_RESULT_BATTLE_STARTED);
    assert(sPending.magic == VEGA_ACQ_PENDING_MAGIC);
    assert(VegaAcq_ResolveBattle(VEGA_ACQ_BATTLE_ESCAPED) == VEGA_ACQ_RESULT_ESCAPED);
    assert(sPending.magic == 0u && sClaims[index] == 0u);
    reset_controls();
    assert(VegaAcq_Begin(index) == VEGA_ACQ_RESULT_BATTLE_STARTED);
    assert(VegaAcq_ResolveBattle(VEGA_ACQ_BATTLE_CAUGHT) == VEGA_ACQ_RESULT_SUCCESS);
    assert(sClaims[index] == 1u && sRegistered[def->species_id] == 1u);
    assert(sPending.magic == 0u);
    assert(VegaAcq_Begin(index) == VEGA_ACQ_RESULT_ALREADY_CLAIMED);
}

static void test_persist_failure_and_recovery(void)
{
    uint16_t index = VegaAcq_FindEventIndex("EVENT_SPECIAL_NATIONAL_0789");
    const VegaAcqEventDef *def = &gVegaAcqEventDefs[index];
    reset_all();
    /* PREPARED=call 1, durable OPERATION_STAGED=call 2, final commit=call 3. */
    sFailPersistCall = 3u;
    assert(VegaAcq_Begin(index) == VEGA_ACQ_RESULT_PERSIST_FAILED);
    assert(sClaims[index] == 0u && sRegistered[def->species_id] == 0u);
    assert(sPending.magic == VEGA_ACQ_PENDING_MAGIC);
    assert(sPending.phase == VEGA_ACQ_PHASE_OPERATION_STAGED);
    assert(sRollbackCount == 0u);
    assert(sFinalizeMemoryCount == 1u);
    sFailPersistCall = 0u;
    sPersistCalls = 0u;
    assert(VegaAcq_RecoverPending() == VEGA_ACQ_RESULT_RECOVERED_COMMIT);
    assert(sPending.magic == 0u);
    assert(sClaims[index] == 1u && sRegistered[def->species_id] == 1u);
    assert(sFinalizeCount == 1u);
}

static void test_staged_journal_failure_rolls_back(void)
{
    uint16_t index = VegaAcq_FindEventIndex("EVENT_SPECIAL_NATIONAL_0789");
    const VegaAcqEventDef *def = &gVegaAcqEventDefs[index];
    reset_all();
    sFailPersistCall = 2u;
    assert(VegaAcq_Begin(index) == VEGA_ACQ_RESULT_PERSIST_FAILED);
    assert(sPending.magic == 0u);
    assert(sClaims[index] == 0u && sRegistered[def->species_id] == 0u);
    assert(sRollbackCount == 1u);
    assert(sFinalizeMemoryCount == 0u);
}

static void test_egg_and_bounded_claim(void)
{
    uint16_t egg = VegaAcq_FindEventIndex("EVENT_STARTER_LAB_NATIONAL_0653");
    uint16_t cosmog = VegaAcq_FindEventIndex("EVENT_SPECIAL_NATIONAL_0789");
    const VegaAcqEventDef *egg_def = &gVegaAcqEventDefs[egg];
    reset_all();
    assert(egg != VEGA_ACQ_NO_INDEX);
    assert(VegaAcq_Begin(egg) == VEGA_ACQ_RESULT_SUCCESS);
    assert(sClaims[egg] == 1u);
    assert(sRegistered[egg_def->species_id] == 0u);
    reset_all();
    assert(VegaAcq_Begin(cosmog) == VEGA_ACQ_RESULT_SUCCESS);
    assert(sClaims[cosmog] == 1u);
    reset_controls();
    assert(VegaAcq_Begin(cosmog) == VEGA_ACQ_RESULT_SUCCESS);
    assert(sClaims[cosmog] == 2u);
    reset_controls();
    assert(VegaAcq_Begin(cosmog) == VEGA_ACQ_RESULT_ALREADY_CLAIMED);
}

static void test_full_storage_and_capture_recovery(void)
{
    uint16_t fossil = VegaAcq_FindEventIndex("EVENT_FOSSIL_RESTORE_NATIONAL_0138");
    uint16_t capture = VegaAcq_FindEventIndex("EVENT_SPECIAL_NATIONAL_0145");
    const VegaAcqEventDef *capture_def = &gVegaAcqEventDefs[capture];
    reset_all();
    assert(fossil != VEGA_ACQ_NO_INDEX);
    sPreflight = VEGA_ACQ_RESULT_BOX_FULL;
    assert(VegaAcq_Begin(fossil) == VEGA_ACQ_RESULT_BOX_FULL);
    assert(sPending.magic == 0u && sStageCount == 0u);

    /* Reset during an active battle has no durable delivery proof: retry. */
    reset_all();
    assert(VegaAcq_Begin(capture) == VEGA_ACQ_RESULT_BATTLE_STARTED);
    assert(VegaAcq_RecoverPending() == VEGA_ACQ_RESULT_RECOVERED_RETRY);
    assert(sClaims[capture] == 0u && sPending.magic == 0u);

    /* A caught Pokemon and OPERATION_STAGED journal survive final-commit failure. */
    reset_all();
    assert(VegaAcq_Begin(capture) == VEGA_ACQ_RESULT_BATTLE_STARTED);
    sFailPersistCall = 4u;
    assert(VegaAcq_ResolveBattle(VEGA_ACQ_BATTLE_CAUGHT)
           == VEGA_ACQ_RESULT_PERSIST_FAILED);
    assert(sPending.phase == VEGA_ACQ_PHASE_OPERATION_STAGED);
    assert(sClaims[capture] == 0u && sRegistered[capture_def->species_id] == 0u);
    sFailPersistCall = 0u;
    sPersistCalls = 0u;
    assert(VegaAcq_RecoverPending() == VEGA_ACQ_RESULT_RECOVERED_COMMIT);
    assert(sClaims[capture] == 1u);
    assert(sRegistered[capture_def->species_id] == 1u);
    assert(sPending.magic == 0u);
}

static void test_host_membership_and_save_migration(void)
{
    VegaAcqSaveBlock block;
    uint16_t species = 136u;
    reset_all();
    sSelected = 0xFFFEu;
    assert(VegaAcq_OpenHost(0u) == VEGA_ACQ_RESULT_BUSY);
    assert(sLastShownResult == 0u);
    VegaAcqSaveInitialize(&block);
    assert(VegaAcqSaveValidate(&block));
    block.magic = 0u;
    assert(VegaAcqSaveMigrate(&block, migration_registered, &species));
    assert(VegaAcqSaveValidate(&block));
}

int main(void)
{
    reset_all();
    assert(VegaAcq_Probe() == 0xAC51u);
    assert(VegaAcqEngine_AdapterProbe() == VEGA_ACQ_ENGINE_ADAPTER_ABI_VERSION);
    test_capture_retry_and_commit();
    test_persist_failure_and_recovery();
    test_staged_journal_failure_rolls_back();
    test_egg_and_bounded_claim();
    test_full_storage_and_capture_recovery();
    test_host_membership_and_save_migration();
    puts("acquisition runtime host tests: PASS");
    return 0;
}
