#include "acquisition_engine_adapter.h"

/*
 * Deliberately unusable reference adapter.  It is useful for negative tests and prevents
 * a build from silently succeeding before the exact ROM ABI has been bound.  The release
 * build script rejects a probe value other than VEGA_ACQ_ENGINE_ADAPTER_ABI_VERSION.
 */
static VegaAcqPendingTransaction sPending;

uint16_t VegaAcqEngine_AdapterProbe(void) { return 0u; }
VegaAcqPendingTransaction *VegaAcqEngine_GetPending(void) { return &sPending; }
uint8_t VegaAcqEngine_IsUnlockSatisfied(const char *key) { (void)key; return 0u; }
uint8_t VegaAcqEngine_IsEventConditionSatisfied(const VegaAcqEventDef *def) { (void)def; return 0u; }
uint8_t VegaAcqEngine_IsSpeciesRegistered(uint16_t species) { (void)species; return 0u; }
uint8_t VegaAcqEngine_SetSpeciesRegistered(uint16_t species, uint8_t value) { (void)species; (void)value; return 0u; }
uint8_t VegaAcqEngine_GetClaimCount(const VegaAcqEventDef *def) { (void)def; return 0u; }
uint8_t VegaAcqEngine_SetClaimCount(const VegaAcqEventDef *def, uint8_t value) { (void)def; (void)value; return 0u; }
uint16_t VegaAcqEngine_Preflight(const VegaAcqEventDef *def) { (void)def; return VEGA_ACQ_RESULT_ENGINE_REJECTED; }
uint16_t VegaAcqEngine_StartCaptureBattle(const VegaAcqEventDef *def) { (void)def; return VEGA_ACQ_RESULT_ENGINE_REJECTED; }
uint16_t VegaAcqEngine_StageOperation(const VegaAcqEventDef *def, uint32_t *token) { (void)def; if (token) *token = 0u; return VEGA_ACQ_RESULT_ENGINE_REJECTED; }
void VegaAcqEngine_RollbackOperation(const VegaAcqEventDef *def, uint32_t token) { (void)def; (void)token; }
void VegaAcqEngine_FinalizeOperation(const VegaAcqEventDef *def, uint32_t token) { (void)def; (void)token; }
uint8_t VegaAcqEngine_IsOperationDurable(const VegaAcqEventDef *def, uint32_t token) { (void)def; (void)token; return 0u; }
void VegaAcqEngine_FinalizeInMemory(void) {}
uint8_t VegaAcqEngine_PersistAll(void) { return 0u; }
uint16_t VegaAcqEngine_SelectHostEvent(const uint16_t *indices, uint16_t count) { (void)indices; (void)count; return 0xFFFFu; }
void VegaAcqEngine_ShowResult(uint16_t event_index, uint16_t result) { (void)event_index; (void)result; }
