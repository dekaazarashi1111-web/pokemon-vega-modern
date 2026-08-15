#ifndef VEGA_ACQUISITION_RUNTIME_H
#define VEGA_ACQUISITION_RUNTIME_H

#include <stdint.h>

#define VEGA_ACQ_RUNTIME_ABI_VERSION 1u
#define VEGA_ACQ_PENDING_MAGIC 0x51545841u /* "AXTQ" little-endian */
#define VEGA_ACQ_ASYNC_SELECTION 0xFFFEu

#define VEGA_ACQ_POLICY_REQUIRE_REGISTERED 0x01u
#define VEGA_ACQ_POLICY_SEED_CLAIM_FROM_REGISTRATION 0x02u
#define VEGA_ACQ_POLICY_DELIVERY_DOES_NOT_REGISTER 0x04u
#define VEGA_ACQ_POLICY_BOUNDED_MULTI_CLAIM 0x08u
#define VEGA_ACQ_POLICY_REPEATABLE_SERVICE 0x10u

typedef enum VegaAcqMode {
    VEGA_ACQ_MODE_CAPTURE = 0,
    VEGA_ACQ_MODE_GIFT = 1,
    VEGA_ACQ_MODE_EGG = 2,
    VEGA_ACQ_MODE_FOSSIL = 3,
    VEGA_ACQ_MODE_EVOLUTION_SUPPORT = 4,
    VEGA_ACQ_MODE_TRADE_EMULATOR = 5,
    VEGA_ACQ_MODE_SERVICE = 6
} VegaAcqMode;

typedef enum VegaAcqResult {
    VEGA_ACQ_RESULT_SUCCESS = 0,
    VEGA_ACQ_RESULT_BATTLE_STARTED = 1,
    VEGA_ACQ_RESULT_CANCELLED = 2,
    VEGA_ACQ_RESULT_LOCKED = 3,
    VEGA_ACQ_RESULT_ALREADY_CLAIMED = 4,
    VEGA_ACQ_RESULT_PARTY_FULL = 5,
    VEGA_ACQ_RESULT_BOX_FULL = 6,
    VEGA_ACQ_RESULT_MISSING_INPUT = 7,
    VEGA_ACQ_RESULT_INVALID_SELECTION = 8,
    VEGA_ACQ_RESULT_BUSY = 9,
    VEGA_ACQ_RESULT_ENGINE_REJECTED = 10,
    VEGA_ACQ_RESULT_PERSIST_FAILED = 11,
    VEGA_ACQ_RESULT_DEFEATED = 12,
    VEGA_ACQ_RESULT_ESCAPED = 13,
    VEGA_ACQ_RESULT_RECOVERED_RETRY = 14,
    VEGA_ACQ_RESULT_RECOVERED_COMMIT = 15,
    VEGA_ACQ_RESULT_CORRUPT_PENDING = 16
} VegaAcqResult;

typedef enum VegaAcqBattleOutcome {
    VEGA_ACQ_BATTLE_CAUGHT = 1,
    VEGA_ACQ_BATTLE_DEFEATED = 2,
    VEGA_ACQ_BATTLE_ESCAPED = 3,
    VEGA_ACQ_BATTLE_ABORTED = 4
} VegaAcqBattleOutcome;

typedef enum VegaAcqPendingPhase {
    VEGA_ACQ_PHASE_NONE = 0,
    VEGA_ACQ_PHASE_PREPARED = 1,
    VEGA_ACQ_PHASE_OPERATION_STAGED = 2,
    VEGA_ACQ_PHASE_CAPTURE_ACTIVE = 3
} VegaAcqPendingPhase;

typedef struct VegaAcqPendingTransaction {
    uint32_t magic;
    uint32_t transaction_token;
    uint16_t event_index;
    uint16_t species_id;
    uint16_t checksum;
    uint8_t mode;
    uint8_t phase;
    uint8_t reserved0;
    uint8_t reserved1;
} VegaAcqPendingTransaction;

uint16_t VegaAcq_OpenHost(uint16_t host_index);
uint16_t VegaAcq_Begin(uint16_t event_index);
uint16_t VegaAcq_ResolveBattle(uint16_t outcome);
uint16_t VegaAcq_RecoverPending(void);
uint16_t VegaAcq_FindEventIndex(const char *event_key);
uint16_t VegaAcq_Probe(void);

#endif /* VEGA_ACQUISITION_RUNTIME_H */
