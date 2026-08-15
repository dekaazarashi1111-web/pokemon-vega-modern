#ifndef VEGA_ACQUISITION_ENGINE_ADAPTER_H
#define VEGA_ACQUISITION_ENGINE_ADAPTER_H

#include <stdint.h>

#include "acquisition_runtime.h"
#include "../../generated/acquisition_event_defs.h"

#define VEGA_ACQ_ENGINE_ADAPTER_ABI_VERSION 1u

/*
 * The exact FireRed/CFRU/DPE addresses and save owner are intentionally not guessed.
 * The integration repository must implement every function below using its pinned symbol
 * contract.  VegaAcqEngine_PersistAll must commit the acquisition block together with
 * party/PC/egg-queue state through the repository's checksum/dual-save generation; a
 * reported failure must leave the prior durable generation intact.  The build script
 * rejects the fail-closed adapter and exact-ROM power-loss acceptance is mandatory.
 */
uint16_t VegaAcqEngine_AdapterProbe(void);
VegaAcqPendingTransaction *VegaAcqEngine_GetPending(void);
uint8_t VegaAcqEngine_IsUnlockSatisfied(const char *unlock_key);
uint8_t VegaAcqEngine_IsEventConditionSatisfied(const VegaAcqEventDef *event_def);
uint8_t VegaAcqEngine_IsSpeciesRegistered(uint16_t species_id);
uint8_t VegaAcqEngine_SetSpeciesRegistered(uint16_t species_id, uint8_t registered);
uint8_t VegaAcqEngine_GetClaimCount(const VegaAcqEventDef *event_def);
uint8_t VegaAcqEngine_SetClaimCount(const VegaAcqEventDef *event_def, uint8_t count);
uint16_t VegaAcqEngine_Preflight(const VegaAcqEventDef *event_def);
uint16_t VegaAcqEngine_StartCaptureBattle(const VegaAcqEventDef *event_def);
uint16_t VegaAcqEngine_StageOperation(const VegaAcqEventDef *event_def,
                                      uint32_t *transaction_token);
void VegaAcqEngine_RollbackOperation(const VegaAcqEventDef *event_def,
                                     uint32_t transaction_token);
void VegaAcqEngine_FinalizeOperation(const VegaAcqEventDef *event_def,
                                     uint32_t transaction_token);
uint8_t VegaAcqEngine_IsOperationDurable(const VegaAcqEventDef *event_def,
                                         uint32_t transaction_token);
/* Recompute the in-memory save checksums after restoring state following a
 * failed persistence attempt.  This function must not write durable storage. */
void VegaAcqEngine_FinalizeInMemory(void);
uint8_t VegaAcqEngine_PersistAll(void);
uint16_t VegaAcqEngine_SelectHostEvent(const uint16_t *event_indices,
                                       uint16_t event_count);
void VegaAcqEngine_ShowResult(uint16_t event_index, uint16_t result);

#endif /* VEGA_ACQUISITION_ENGINE_ADAPTER_H */
