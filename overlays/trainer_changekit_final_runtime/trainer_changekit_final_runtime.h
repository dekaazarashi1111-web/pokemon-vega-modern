#ifndef VEGA_TRAINER_CHANGEKIT_FINAL_RUNTIME_H
#define VEGA_TRAINER_CHANGEKIT_FINAL_RUNTIME_H

#include <stdint.h>

#include "trainer_changekit_final_generated.h"

enum TrainerChangeKitFinalProbeSelector {
    TRAINER_CHANGEKIT_PROBE_MAGIC = 0,
    TRAINER_CHANGEKIT_PROBE_ENCOUNTER_COUNT = 1,
    TRAINER_CHANGEKIT_PROBE_SIDECAR_COUNT = 2,
    TRAINER_CHANGEKIT_PROBE_REMATCH_COUNT = 3,
    TRAINER_CHANGEKIT_PROBE_FLAG_MAP_COUNT = 4,
    TRAINER_CHANGEKIT_PROBE_TRAINER_TABLE_COUNT = 5,
    TRAINER_CHANGEKIT_PROBE_EXACT_BINDING_COUNT = 6,
    TRAINER_CHANGEKIT_PROBE_ARCHIVE_COUNT = 7,
    TRAINER_CHANGEKIT_PROBE_GIMMICK_COUNT = 8,
    TRAINER_CHANGEKIT_PROBE_PHASE = 9,
    TRAINER_CHANGEKIT_PROBE_AMBIGUOUS_BINDINGS = 10,
    TRAINER_CHANGEKIT_PROBE_POLICY_FAILURES = 11,
    TRAINER_CHANGEKIT_PROBE_CURRENT_TRAINER = 12,
    TRAINER_CHANGEKIT_PROBE_CURRENT_DISPATCH = 13
};

enum TrainerChangeKitFinalPhase {
    TRAINER_CHANGEKIT_PHASE_IDLE = 0,
    TRAINER_CHANGEKIT_PHASE_PENDING = 1,
    TRAINER_CHANGEKIT_PHASE_ACTIVE = 2
};

enum TrainerChangeKitFinalMechanic {
    TRAINER_CHANGEKIT_MECHANIC_STANDARD = 0,
    TRAINER_CHANGEKIT_MECHANIC_MEGA = 1,
    TRAINER_CHANGEKIT_MECHANIC_Z_MOVE = 2,
    TRAINER_CHANGEKIT_MECHANIC_DYNAMAX = 3,
    TRAINER_CHANGEKIT_MECHANIC_TERASTAL = 4
};

enum TrainerChangeKitFinalGimmickFlags {
    TRAINER_CHANGEKIT_GIMMICK_CONSUMER = 1u << 0,
    TRAINER_CHANGEKIT_GIMMICK_DOUBLE_OK = 1u << 1,
    TRAINER_CHANGEKIT_GIMMICK_FORCED = 1u << 2
};

enum TrainerChangeKitFinalBattleFormat {
    TRAINER_CHANGEKIT_FORMAT_SINGLE = 0,
    TRAINER_CHANGEKIT_FORMAT_DOUBLE = 1
};

enum TrainerChangeKitFinalCleanupReason {
    TRAINER_CHANGEKIT_CLEANUP_WIN = 0,
    TRAINER_CHANGEKIT_CLEANUP_LOSS = 1,
    TRAINER_CHANGEKIT_CLEANUP_ABORT = 2,
    TRAINER_CHANGEKIT_CLEANUP_SAVE_RELOAD = 3
};

uint32_t TrainerChangeKitFinalRuntime_Probe(uint32_t selector);

uint8_t TrainerChangeKitFinalRuntime_ScriptFlagGet(void);
uint8_t TrainerChangeKitFinalRuntime_ScriptFlagSet(void);
uint8_t TrainerChangeKitFinalRuntime_HasTrainerBeenFought(uint16_t trainer_id);
uint8_t TrainerChangeKitFinalRuntime_SetTrainerFlag(uint16_t trainer_id);
uint8_t TrainerChangeKitFinalRuntime_ClearTrainerFlag(uint16_t trainer_id);

uint16_t TrainerChangeKitFinalRuntime_GetRematchTrainerId(uint16_t trainer_id);
const uint8_t *TrainerChangeKitFinalRuntime_ConfigureTrainerBattle(
    const uint8_t *data);
void TrainerChangeKitFinalRuntime_BuildTrainerPartySetup(void);
void TrainerChangeKitFinalRuntime_LoadProperAbilityBattleDataAdapter(void);

/* Archive selection is one-shot.  It is consumed by the next matching
 * canonical trainerbattle command and is discarded on mismatch. */
uint8_t TrainerChangeKitFinalRuntime_SelectArchive(uint16_t archive_id);
void TrainerChangeKitFinalRuntime_ClearArchiveSelection(void);
const uint8_t *TrainerChangeKitFinalRuntime_DispatchArchive(
    uint16_t archive_id,
    const uint8_t *data);

/* These entry points are deliberately small hook consumers.  The existing
 * CFRU policy owns form, move, HP-ratio, type, and one-use restoration. */
uint8_t TrainerChangeKitFinalRuntime_BattleBegin(void);
void TrainerChangeKitFinalRuntime_BattleEnd(uint8_t cleanup_reason);
void TrainerChangeKitFinalRuntime_BattleAbort(uint8_t cleanup_reason);
void TrainerChangeKitFinalRuntime_SaveReloadCleanup(void);
void TrainerChangeKitFinalRuntime_PartySlotExit(uint8_t side, uint8_t slot);
uint8_t TrainerChangeKitFinalRuntime_ShouldActivate(
    uint16_t trainer_id,
    uint8_t party_slot,
    uint8_t mechanic_mode);
uint8_t TrainerChangeKitFinalRuntime_MarkActivated(
    uint16_t trainer_id,
    uint8_t party_slot,
    uint8_t mechanic_mode);
const struct TrainerChangeKitGimmickV1 *
TrainerChangeKitFinalRuntime_CurrentGimmick(void);

/* Patch the existing CFRU mechanic Can/Mark BL consumers to these adapters. Each
 * adapter delegates unchanged for the player side and for every battle that
 * is not owned by an active generated trainer consumer. */
uint8_t TrainerChangeKitFinalRuntime_CanMegaAdapter(
    uint8_t battler, uint8_t upstream_allowed);
uint8_t TrainerChangeKitFinalRuntime_MarkMegaAdapter(uint8_t battler);
uint8_t TrainerChangeKitFinalRuntime_CanZAdapter(
    uint8_t battler, uint8_t upstream_allowed);
uint8_t TrainerChangeKitFinalRuntime_MarkZAdapter(uint8_t battler);
uint8_t TrainerChangeKitFinalRuntime_CanDynamaxAdapter(
    uint8_t battler, uint8_t upstream_allowed);
uint8_t TrainerChangeKitFinalRuntime_MarkDynamaxAdapter(uint8_t battler);
uint8_t TrainerChangeKitFinalRuntime_CanTeraAdapter(
    uint8_t battler, uint8_t upstream_allowed);
uint8_t TrainerChangeKitFinalRuntime_MarkTeraAdapter(uint8_t battler);

/* Lifetime adapters replace the single existing CFRU Begin/End BL consumers.
 * SaveLoadAdapter wraps Save_LoadGameData through a relocated trampoline. */
uint8_t TrainerChangeKitFinalRuntime_PolicyBeginAdapter(void);
uint8_t TrainerChangeKitFinalRuntime_PolicyEndAdapter(void);
uint8_t TrainerChangeKitFinalRuntime_SaveLoadAdapter(uint8_t save_type);

const struct TrainerChangeKitMemberSidecarV1 *
TrainerChangeKitFinalRuntime_SidecarTable(void);
const struct TrainerChangeKitExactBindingV1 *
TrainerChangeKitFinalRuntime_ExactBindingTable(void);
const struct TrainerChangeKitRematchV2 *
TrainerChangeKitFinalRuntime_RematchTable(void);
const struct TrainerChangeKitArchiveBindingV1 *
TrainerChangeKitFinalRuntime_ArchiveTable(void);
const struct TrainerChangeKitGimmickV1 *
TrainerChangeKitFinalRuntime_GimmickTable(void);
const struct TrainerChangeKitFlagMapV1 *
TrainerChangeKitFinalRuntime_FlagTable(void);
const void *TrainerChangeKitFinalRuntime_TrainerTable(void);

/* Stage 34 hook ABI wrappers.  Existing callers can be redirected without
 * changing their signature while the new table anchors remain discoverable. */
uint32_t TrainerV5Runtime_Probe(uint32_t selector);
uint8_t TrainerV5Runtime_ScriptFlagGet(void);
uint8_t TrainerV5Runtime_ScriptFlagSet(void);
uint8_t TrainerV5Runtime_HasTrainerBeenFought(uint16_t trainer_id);
uint8_t TrainerV5Runtime_SetTrainerFlag(uint16_t trainer_id);
uint8_t TrainerV5Runtime_ClearTrainerFlag(uint16_t trainer_id);
uint16_t TrainerV5Runtime_GetRematchTrainerId(uint16_t trainer_id);
const uint8_t *TrainerV5Runtime_ConfigureTrainerBattle(const uint8_t *data);
void TrainerV5Runtime_BuildTrainerPartySetup(void);
const void *TrainerV5Runtime_SidecarTable(void);
const void *TrainerV5Runtime_RematchTable(void);
const void *TrainerV5Runtime_FlagTable(void);
const void *TrainerV5Runtime_ExactRebindTable(void);

#endif /* VEGA_TRAINER_CHANGEKIT_FINAL_RUNTIME_H */
