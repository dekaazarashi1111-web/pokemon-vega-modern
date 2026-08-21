#ifndef VEGA_FACTORY_HIGH_MODES_V2_H
#define VEGA_FACTORY_HIGH_MODES_V2_H

#include <stdint.h>

#define FACTORY_HIGH_MODES_V2_ABI_VERSION 0x46483232u /* "FH22" */
#define FACTORY_HIGH_MODES_V2_STATE_ADDRESS 0x0203F220u
#define FACTORY_HIGH_MODES_V2_STATE_SIZE 1280u
#define FACTORY_HIGH_MODES_V2_MODE_COUNT 24u
#define FACTORY_HIGH_MODES_V2_RENTAL_COUNT 248u
#define FACTORY_HIGH_MODES_V2_PROFILE_COUNT 55u
#define FACTORY_HIGH_MODES_V2_REWARD_COUNT 16u
#define FACTORY_HIGH_MODES_V2_REQUIREMENT_COUNT 28u
#define FACTORY_HIGH_MODES_V2_DIALOGUE_COUNT 28u
#define FACTORY_HIGH_MODES_V2_BATCH_COUNT 7u

typedef enum FactoryHighModesV2Status {
    FACTORY_HIGH_STATUS_ERROR = 0,
    FACTORY_HIGH_STATUS_OK = 1,
    FACTORY_HIGH_STATUS_ROUND = 2,
    FACTORY_HIGH_STATUS_COMPLETE = 3,
    FACTORY_HIGH_STATUS_CANCELLED = 4,
    FACTORY_HIGH_STATUS_LOCKED = 5,
    FACTORY_HIGH_STATUS_PERSIST_FAILED = 6,
    FACTORY_HIGH_STATUS_NOT_ACTIVE = 7,
    FACTORY_HIGH_STATUS_BAG_FULL = 8,
    FACTORY_HIGH_STATUS_RECOVERED = 9,
    FACTORY_HIGH_STATUS_TRIAL_DELEGATE = 10,
    FACTORY_HIGH_STATUS_HIGH_MODE = 11,
    FACTORY_HIGH_STATUS_INVALID = 12,
    FACTORY_HIGH_STATUS_ISOLATION_BUSY = 13
} FactoryHighModesV2Status;

typedef enum FactoryHighModesV2Probe {
    FACTORY_HIGH_PROBE_ABI = 0,
    FACTORY_HIGH_PROBE_STATE_ADDRESS = 1,
    FACTORY_HIGH_PROBE_LEDGER_ADDRESS = 2,
    FACTORY_HIGH_PROBE_MODE_COUNT = 3,
    FACTORY_HIGH_PROBE_RENTAL_COUNT = 4,
    FACTORY_HIGH_PROBE_PROFILE_COUNT = 5,
    FACTORY_HIGH_PROBE_REWARD_COUNT = 6,
    FACTORY_HIGH_PROBE_ACTIVE = 7,
    FACTORY_HIGH_PROBE_MODE = 8,
    FACTORY_HIGH_PROBE_OPTION = 9,
    FACTORY_HIGH_PROBE_BATTLE = 10,
    FACTORY_HIGH_PROBE_SEED = 11,
    FACTORY_HIGH_PROBE_PARTY_HASH = 12,
    FACTORY_HIGH_PROBE_CANDIDATE_HASH = 13,
    FACTORY_HIGH_PROBE_OPPONENT_HASH = 14,
    FACTORY_HIGH_PROBE_GIMMICK_COUNT = 15,
    FACTORY_HIGH_PROBE_CREDIT_HOOK_COUNT = 16,
    FACTORY_HIGH_PROBE_DELEGATE_COUNTS = 17,
    FACTORY_HIGH_PROBE_MARKER_PACKED = 18,
    FACTORY_HIGH_PROBE_REWARD_PENDING_PACKED = 19,
    FACTORY_HIGH_PROBE_CLAIM_BITS = 20,
    FACTORY_HIGH_PROBE_BP = 21,
    FACTORY_HIGH_PROBE_TRANSACTION = 22,
    FACTORY_HIGH_PROBE_CURRENT_STREAK_BASE = 0x40,
    FACTORY_HIGH_PROBE_BEST_STREAK_BASE = 0x60,
    FACTORY_HIGH_PROBE_MODE_ROW_BASE = 0x100,
    FACTORY_HIGH_PROBE_RENTAL_ROW_BASE = 0x200,
    FACTORY_HIGH_PROBE_PROFILE_ROW_BASE = 0x400,
    FACTORY_HIGH_PROBE_REWARD_ROW_BASE = 0x500,
    FACTORY_HIGH_PROBE_DIALOGUE_ROW_BASE = 0x600,
    FACTORY_HIGH_PROBE_REQUIREMENT_ROW_BASE = 0x700,
    FACTORY_HIGH_PROBE_BATCH_ROW_BASE = 0x800
} FactoryHighModesV2Probe;

typedef struct __attribute__((packed)) FactoryHighModesV2State {
    uint32_t magic;
    uint32_t magic_inverse;
    uint32_t seed;
    uint32_t candidate_hash;
    uint32_t opponent_hash;
    uint32_t party_hash_before;
    uint32_t party_hash_after;
    uint32_t last_transaction;
    uint16_t last_status;
    uint16_t candidates[8];
    uint16_t selected[6];
    uint16_t opponent[6];
    uint16_t player_abilities[6];
    uint16_t opponent_abilities[6];
    uint8_t active;
    uint8_t mode;
    uint8_t option;
    uint8_t battle_in_round;
    uint8_t selected_count;
    uint8_t candidate_count;
    uint8_t opponent_count;
    uint8_t player_owned_count;
    uint8_t phase;
    uint8_t test_mode;
    uint8_t persistence_fault;
    uint8_t menu_active;
    uint8_t menu_stage;
    uint8_t menu_page;
    uint8_t menu_cursor;
    uint8_t menu_count;
    uint8_t window_id;
    uint8_t configured_gimmick;
    uint8_t player_gimmick_used;
    uint8_t opponent_gimmick_used;
    uint8_t credit_hook_count;
    uint8_t trainer_delegate_count;
    uint8_t ability_delegate_count;
    uint8_t save_delegate_count;
    uint8_t recovery_count;
    uint8_t reward_item_pending;
    uint8_t profile_index;
    uint8_t reserved_header[4];
    uint8_t menu_codes[10];
    uint8_t menu_text[10][24];
    uint8_t reserved[901];
} FactoryHighModesV2State;

_Static_assert(sizeof(FactoryHighModesV2State)
                   == FACTORY_HIGH_MODES_V2_STATE_SIZE,
               "Factory High Modes V2 RAM ABI differs");

#define gFactoryHighModesV2State \
    ((FactoryHighModesV2State *)(uintptr_t)FACTORY_HIGH_MODES_V2_STATE_ADDRESS)

uint32_t FactoryHighModesV2_Probe(uint32_t selector);
uint16_t FactoryHighModesV2_FieldReception(void);
uint16_t FactoryHighModesV2_FieldDraft(void);
uint16_t FactoryHighModesV2_EnterSelected(void);
uint16_t FactoryHighModesV2_CommitSelection(void);
uint16_t FactoryHighModesV2_PrepareBattle(void);
uint16_t FactoryHighModesV2_AfterBattle(void);
uint16_t FactoryHighModesV2_BeginExchange(void);
uint16_t FactoryHighModesV2_CommitExchange(void);
uint16_t FactoryHighModesV2_SkipExchange(void);
uint16_t FactoryHighModesV2_Retire(void);
uint16_t FactoryHighModesV2_Abort(void);
uint16_t FactoryHighModesV2_Recover(void);
uint16_t FactoryHighModesV2_TrialCompleteAdapter(void);
void FactoryHighModesV2_BuildTrainerPartyAdapter(void);
void FactoryHighModesV2_LoadProperAbilityBattleDataAdapter(void);
uint8_t FactoryHighModesV2_SaveLoadAdapter(uint8_t save_type);

/* exact-ROM smoke API: production state machine with final engine I/O mocked. */
uint16_t FactoryHighModesV2_TestInitialize(void);
uint16_t FactoryHighModesV2_TestSetUnlocks(uint32_t unlock_bits);
uint16_t FactoryHighModesV2_TestEnter(uint16_t mode, uint16_t option,
                                     uint32_t seed);
uint16_t FactoryHighModesV2_TestCommitDraft(uint32_t selection_mask);
uint16_t FactoryHighModesV2_TestBattleResult(uint16_t won);
uint16_t FactoryHighModesV2_TestSetPersistenceFault(uint16_t enabled);
uint16_t FactoryHighModesV2_TestReload(void);
uint16_t FactoryHighModesV2_TestSetStreak(uint16_t mode, uint16_t streak);
uint32_t FactoryHighModesV2_TestGeneratorAudit(uint16_t mode,
                                              uint16_t option,
                                              uint32_t seed);
uint32_t FactoryHighModesV2_TestPartyHash(void);

#endif /* VEGA_FACTORY_HIGH_MODES_V2_H */
