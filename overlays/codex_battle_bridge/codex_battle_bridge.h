#ifndef VEGA_CODEX_BATTLE_BRIDGE_H
#define VEGA_CODEX_BATTLE_BRIDGE_H

#include <stddef.h>
#include <stdint.h>

#include "codex_battle_bridge_generated.h"

enum CodexBattleBridgeCapability {
    CODEX_BATTLE_CAP_STATUS = 1u << 0,
    CODEX_BATTLE_CAP_PING = 1u << 1,
    CODEX_BATTLE_CAP_NCI_CORE_MEMORY = 1u << 2,
};

enum CodexBattleBridgePhase {
    CODEX_BATTLE_PHASE_IDLE = 1u,
};

enum CodexBattleBridgeCommand {
    CODEX_BATTLE_COMMAND_NONE = 0u,
    CODEX_BATTLE_COMMAND_PING = 1u,
};

enum CodexBattleBridgeStatus {
    CODEX_BATTLE_STATUS_NONE = 0u,
    CODEX_BATTLE_STATUS_READY = 1u,
    CODEX_BATTLE_STATUS_PONG = 2u,
    CODEX_BATTLE_STATUS_ERROR = 3u,
};

enum CodexBattleBridgeError {
    CODEX_BATTLE_ERROR_NONE = 0u,
    CODEX_BATTLE_ERROR_FUTURE_SEQUENCE = 1u,
    CODEX_BATTLE_ERROR_STALE_SEQUENCE = 2u,
    CODEX_BATTLE_ERROR_WRONG_NONCE = 3u,
    CODEX_BATTLE_ERROR_OVERSIZE = 4u,
    CODEX_BATTLE_ERROR_PAYLOAD_CRC = 5u,
    CODEX_BATTLE_ERROR_REQUEST_CRC = 6u,
    CODEX_BATTLE_ERROR_WRONG_PHASE = 7u,
    CODEX_BATTLE_ERROR_UNKNOWN_COMMAND = 8u,
    CODEX_BATTLE_ERROR_PAYLOAD_FORMAT = 9u,
    CODEX_BATTLE_ERROR_FLAGS = 10u,
};

enum CodexBattleBridgeProbe {
    CODEX_BATTLE_PROBE_ABI = 0u,
    CODEX_BATTLE_PROBE_ADDRESS = 1u,
    CODEX_BATTLE_PROBE_STRUCT_SIZE = 2u,
    CODEX_BATTLE_PROBE_RESERVED_SIZE = 3u,
    CODEX_BATTLE_PROBE_CAPABILITIES = 4u,
    CODEX_BATTLE_PROBE_STAGE = 5u,
    CODEX_BATTLE_PROBE_IDENTITY = 6u,
    CODEX_BATTLE_PROBE_NONCE = 7u,
    CODEX_BATTLE_PROBE_SNAPSHOT_SEQUENCE = 8u,
    CODEX_BATTLE_PROBE_REQUEST_SEQUENCE = 9u,
    CODEX_BATTLE_PROBE_RESPONSE_STATUS = 10u,
    CODEX_BATTLE_PROBE_RESPONSE_ERROR = 11u,
    CODEX_BATTLE_PROBE_REJECTED_COUNT = 12u,
};

typedef struct __attribute__((packed)) CodexBattleMailbox {
    /* Immutable/versioned header: 0x00..0x3F. */
    uint32_t magic;
    uint16_t protocol_major;
    uint16_t protocol_minor;
    uint16_t struct_size;
    uint16_t header_size;
    uint16_t request_offset;
    uint16_t request_size;
    uint16_t snapshot_offset;
    uint16_t snapshot_size;
    uint32_t capabilities;
    uint16_t stage_number;
    uint16_t phase;
    uint32_t stage_identity;
    uint32_t base_rom_crc32;
    uint32_t build_identity;
    uint32_t session_nonce;
    uint32_t session_nonce_inverse;
    uint32_t ram_address;
    uint32_t reserved_size;
    uint16_t request_payload_max;
    uint16_t command_count;
    uint32_t header_flags;

    /* ROM-owned snapshot commit: payload/CRC -> inverse -> sequence. */
    uint32_t snapshot_sequence;
    uint32_t snapshot_sequence_inverse;
    uint16_t snapshot_payload_size;
    uint16_t current_status;
    uint32_t snapshot_crc32;

    /* ROM-owned response/snapshot payload: 0x50..0x7F. */
    uint32_t response_sequence;
    uint32_t response_sequence_inverse;
    uint16_t response_status;
    uint16_t response_error;
    uint16_t response_payload_size;
    uint16_t last_command;
    uint32_t pong_token;
    uint32_t pong_token_inverse;
    uint32_t pong_magic;
    uint32_t accepted_request_crc32;
    uint32_t last_accepted_sequence;
    uint32_t last_rejected_sequence;
    uint32_t last_rejected_fingerprint;
    uint32_t rejected_count;

    /* Host-owned request span: exactly 0x80..0xBF. */
    uint32_t request_session_nonce;
    uint16_t request_command;
    uint16_t request_expected_phase;
    uint16_t request_payload_size;
    uint16_t request_flags;
    uint32_t request_payload_crc32;
    uint8_t request_payload[32];
    uint32_t request_crc32;
    uint32_t request_reserved;
    uint32_t request_sequence_inverse;
    uint32_t request_sequence;

    uint8_t future_protocol[64];
} CodexBattleMailbox;

_Static_assert(sizeof(CodexBattleMailbox) == CODEX_BATTLE_MAILBOX_SIZE,
               "Codex Battle mailbox size differs");
_Static_assert(offsetof(CodexBattleMailbox, snapshot_sequence) == 0x40u,
               "Codex Battle snapshot commit offset differs");
_Static_assert(offsetof(CodexBattleMailbox, response_sequence) == 0x50u,
               "Codex Battle snapshot payload offset differs");
_Static_assert(offsetof(CodexBattleMailbox, request_session_nonce) == 0x80u,
               "Codex Battle request offset differs");
_Static_assert(offsetof(CodexBattleMailbox, request_sequence_inverse) == 0xB8u,
               "Codex Battle request inverse offset differs");
_Static_assert(offsetof(CodexBattleMailbox, request_sequence) == 0xBCu,
               "Codex Battle request commit offset differs");

#define gCodexBattleMailbox \
    ((volatile CodexBattleMailbox *)(uintptr_t)CODEX_BATTLE_MAILBOX_ADDRESS)

uint32_t CodexBattleBridge_Probe(uint32_t selector);
void CodexBattleBridge_Initialize(void);
void CodexBattleBridge_InitializeWithNonce(uint32_t nonce);
void CodexBattleBridge_Poll(void);
void CodexBattleBridge_ReadKeysAdapter(void);

#endif /* VEGA_CODEX_BATTLE_BRIDGE_H */
