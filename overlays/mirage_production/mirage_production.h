#ifndef VEGA_MIRAGE_PRODUCTION_H
#define VEGA_MIRAGE_PRODUCTION_H

#include <stdint.h>

#define MIRAGE_PRODUCTION_ABI_VERSION 0x4D500002u
#define MIRAGE_PRODUCTION_STATE_ADDRESS 0x0203EE00u
#define MIRAGE_PRODUCTION_STATE_SIZE 664u
#define MIRAGE_PRODUCTION_PARTY_SIZE 6u
#define MIRAGE_PRODUCTION_SELECTED_SIZE 3u
#define MIRAGE_PRODUCTION_MON_SIZE 100u

typedef enum MirageProductionStatus {
    MIRAGE_STATUS_OK = 1,
    MIRAGE_STATUS_CANCELLED = 2,
    MIRAGE_STATUS_NOT_UNLOCKED = 3,
    MIRAGE_STATUS_INVALID_SELECTION = 4,
    MIRAGE_STATUS_SAVE_INVALID = 5,
    MIRAGE_STATUS_PERSIST_FAILED = 6,
    MIRAGE_STATUS_NOT_ACTIVE = 7,
    MIRAGE_STATUS_CONFIG_FAILED = 8,
    MIRAGE_STATUS_BATTLE_CONTINUE = 9,
    MIRAGE_STATUS_ROUND_COMPLETE = 10,
    MIRAGE_STATUS_CHALLENGE_COMPLETE = 11,
    MIRAGE_STATUS_LOST = 12,
    MIRAGE_STATUS_BAD_ARGUMENT = 13,
    MIRAGE_STATUS_RECOVERED = 14
} MirageProductionStatus;

typedef enum MirageProductionProbeSelector {
    MIRAGE_PROBE_ABI_VERSION = 0x00,
    MIRAGE_PROBE_STATE_VALID = 0x01,
    MIRAGE_PROBE_ACTIVE = 0x02,
    MIRAGE_PROBE_ROUND = 0x03,
    MIRAGE_PROBE_BATTLE_IN_ROUND = 0x04,
    MIRAGE_PROBE_GIMMICK = 0x05,
    MIRAGE_PROBE_BADGE_SNAPSHOT = 0x06,
    MIRAGE_PROBE_SELECTED_PACKED = 0x07,
    MIRAGE_PROBE_LAST_STATUS = 0x08,
    MIRAGE_PROBE_VIRTUAL_PACKED = 0x09,
    MIRAGE_PROBE_PENDING_CONFIGURED = 0x0A,
    MIRAGE_PROBE_RNG_STATE = 0x0B,
    MIRAGE_PROBE_OPPONENT_PACKED = 0x0C,
    MIRAGE_PROBE_CLAIM_BITS = 0x0D,
    MIRAGE_PROBE_TRANSACTION_ID = 0x0E,
    MIRAGE_PROBE_JOURNAL_MARKER_PAIR = 0x0F,
    MIRAGE_PROBE_JOURNAL_PAYLOAD_PAIR = 0x10,

    MIRAGE_PROBE_CURRENT_RECORD_0 = 0x20,
    MIRAGE_PROBE_CURRENT_RECORD_3 = 0x23,
    MIRAGE_PROBE_BEST_RECORD_0 = 0x30,
    MIRAGE_PROBE_BEST_RECORD_3 = 0x33,
    MIRAGE_PROBE_SELECTED_SLOT_0 = 0x40,
    MIRAGE_PROBE_SELECTED_SLOT_2 = 0x42,
    MIRAGE_PROBE_VIRTUAL_ITEM_0 = 0x50,
    MIRAGE_PROBE_VIRTUAL_ITEM_2 = 0x52,
    MIRAGE_PROBE_FACTORY_SENTINEL_HASH = 0x60,
    MIRAGE_PROBE_UPSTREAM_SENTINEL_HASH = 0x61,
    MIRAGE_PROBE_BATTLE_LOCAL_ACTIVE_COUNT = 0x62,
    MIRAGE_PROBE_BADGE_CURRENT_MASK = 0x63
} MirageProductionProbeSelector;

/*
 * Public EWRAM ABI used by the exact-ROM runner.  Header offsets remain fixed;
 * party_snapshot ends at 0x298 so initialization never touches neighboring
 * engine UI state.
 */
typedef struct MirageProductionState {
    uint32_t magic;                         /* 0x000 */
    uint32_t magic_inverse;                 /* 0x004 */
    uint32_t rng_before;                    /* 0x008 */
    uint32_t rng_after;                     /* 0x00C */
    uint32_t party_hash_before;             /* 0x010 */
    uint32_t party_hash_after;              /* 0x014 */
    uint32_t last_transaction;              /* 0x018 */
    uint16_t last_status;                   /* 0x01C */
    uint16_t trainer_id;                    /* 0x01E */
    uint16_t total_wins;                    /* 0x020 */
    uint16_t virtual_items[3];              /* 0x022 */
    uint8_t active;                         /* 0x028 */
    uint8_t round;                          /* 0x029 */
    uint8_t battle_in_round;                /* 0x02A */
    uint8_t gimmick;                        /* 0x02B */
    uint8_t badge_snapshot;                 /* 0x02C */
    uint8_t badge_snapshot_valid;           /* 0x02D */
    uint8_t selected_count;                 /* 0x02E */
    uint8_t selected_slots[3];              /* 0x02F */
    uint8_t opponent_slots[3];              /* 0x032 */
    uint8_t virtual_tier;                   /* 0x035; 0xFF means none */
    uint8_t pending_configured;              /* 0x036 */
    uint8_t cleanup_reason;                 /* 0x037 */
    uint8_t fault_mode;                     /* 0x038 */
    uint8_t fault_armed;                    /* 0x039 */
    uint8_t commit_phase;                   /* 0x03A */
    uint8_t party_snapshot_valid;           /* 0x03B */
    uint8_t original_party_count;           /* 0x03C */
    uint8_t battle_local_active;             /* 0x03D */
    uint8_t phase;                          /* 0x03E */
    uint8_t reserved_header;                /* 0x03F */
    uint8_t party_snapshot[600];             /* 0x040 */
} MirageProductionState;

#define gMirageProductionState \
    ((MirageProductionState *)(uintptr_t)MIRAGE_PRODUCTION_STATE_ADDRESS)

uint32_t MirageProduction_Probe(uint32_t selector);
uint16_t MirageProduction_FieldEnter(void);
uint16_t MirageProduction_CommitSelection(void);
uint16_t MirageProduction_CommitRound4Mechanic(void);
uint16_t MirageProduction_PrepareBattle(void);
uint16_t MirageProduction_FinalizeBattleCopy(void);
uint16_t MirageProduction_AfterBattle(void);
uint16_t MirageProduction_Complete(void);
uint16_t MirageProduction_Abort(void);
uint16_t MirageProduction_Recover(void);
uint16_t MirageProduction_MapTransitionRecover(void);
uint8_t MirageProduction_SaveLoadAdapter(uint8_t save_type);
void MirageProduction_BuildTrainerPartyAdapter(void);
void MirageProduction_LoadProperAbilityBattleDataAdapter(void);
uint16_t MirageProduction_TestInjectPersistenceFault(uint8_t mode);
uint16_t MirageProduction_TestWarpToReception(void);

#endif /* VEGA_MIRAGE_PRODUCTION_H */
