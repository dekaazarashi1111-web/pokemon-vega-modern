#ifndef VEGA_CODEX_BATTLE_REWARDS_H
#define VEGA_CODEX_BATTLE_REWARDS_H

#include <stddef.h>
#include <stdint.h>

#include "codex_battle_rewards_generated.h"

#if CODEX_WINDOWS_CATALOG_ENABLED
#include "../windows_battle_catalog/windows_battle_catalog.h"
#endif

enum CodexBattleRewardWindow {
    CODEX_REWARD_WINDOW_CLOSED = 0,
    CODEX_REWARD_WINDOW_OPEN = 1,
};

enum CodexBattleRewardJournalPhase {
    CODEX_REWARD_JOURNAL_NONE = 0,
    CODEX_REWARD_JOURNAL_PREPARED = 1,
    CODEX_REWARD_JOURNAL_STAGED = 2,
    CODEX_REWARD_JOURNAL_COMMITTED = 3,
};

enum CodexBattleRewardCommand {
    CODEX_REWARD_COMMAND_STATUS = 11,
    CODEX_REWARD_COMMAND_ITEM = 12,
    CODEX_REWARD_COMMAND_MON = 13,
    CODEX_REWARD_COMMAND_CLOSE = 14,
#if CODEX_WINDOWS_CATALOG_ENABLED
    CODEX_CATALOG_COMMAND_ITEM = WINDOWS_BATTLE_CATALOG_COMMAND_ITEM,
    CODEX_CATALOG_COMMAND_MON = WINDOWS_BATTLE_CATALOG_COMMAND_MON,
#endif
};

enum CodexBattleRewardError {
    CODEX_REWARD_ERROR_NONE = 0,
    CODEX_REWARD_ERROR_FUTURE_SEQUENCE = 1,
    CODEX_REWARD_ERROR_STALE_SEQUENCE = 2,
    CODEX_REWARD_ERROR_WRONG_NONCE = 3,
    CODEX_REWARD_ERROR_OVERSIZE = 4,
    CODEX_REWARD_ERROR_PAYLOAD_CRC = 5,
    CODEX_REWARD_ERROR_REQUEST_CRC = 6,
    CODEX_REWARD_ERROR_WRONG_PHASE = 7,
    CODEX_REWARD_ERROR_UNKNOWN_COMMAND = 8,
    CODEX_REWARD_ERROR_PAYLOAD_FORMAT = 9,
    CODEX_REWARD_ERROR_FLAGS = 10,
    CODEX_REWARD_ERROR_WRONG_MATCH = 11,
    CODEX_REWARD_ERROR_WRONG_TURN = 12,
    CODEX_REWARD_ERROR_INVALID_MEMBER = 13,
    CODEX_REWARD_ERROR_REGULATION = 14,
    CODEX_REWARD_ERROR_ILLEGAL_ACTION = 15,
    CODEX_REWARD_ERROR_BUSY = 16,
    CODEX_REWARD_ERROR_PRIVATE_BOUNDARY = 17,
    CODEX_REWARD_ERROR_WINDOW_CLOSED = 18,
    CODEX_REWARD_ERROR_SAVE_FAILED = 19,
    CODEX_REWARD_ERROR_STORAGE_FULL = 20,
    CODEX_REWARD_ERROR_INVALID_ITEM = 21,
    CODEX_REWARD_ERROR_INVALID_MON = 22,
    CODEX_REWARD_ERROR_WRONG_HASH = 23,
    CODEX_REWARD_ERROR_TRANSACTION_CONFLICT = 24,
};

enum CodexBattleRewardPresence {
    CODEX_REWARD_PRESENCE_ITEM = 1,
    CODEX_REWARD_PRESENCE_MOVES = 2,
    CODEX_REWARD_PRESENCE_ABILITY = 4,
    CODEX_REWARD_PRESENCE_NATURE = 8,
    CODEX_REWARD_PRESENCE_IVS = 16,
    CODEX_REWARD_PRESENCE_EVS = 32,
    CODEX_REWARD_PRESENCE_SHINY = 64,
    CODEX_REWARD_PRESENCE_TERA = 128,
};

typedef struct __attribute__((packed)) CodexBattleRewardMonV1 {
    uint16_t species_id;
    uint8_t level;
    uint8_t ability_slot;
    uint16_t held_item_id;
    uint16_t moves[4];
    uint8_t nature_id;
    uint8_t ivs[6];
    uint8_t evs[6];
    uint8_t shiny;
    uint8_t tera_type;
    uint8_t presence;
    uint16_t ball_item_id;
} CodexBattleRewardMonV1;

/* Independent sector-31 owner with a field-lifetime EWRAM cache.  The
 * authoritative image is deliberately outside the legacy/T08 2 KiB ledger
 * so neither owner's validator or CRC aliases the other.  PC Storage may
 * clear the EWRAM cache; stable-field input reloads the independently
 * checksummed image.  Every multi-byte access is byte-safe through the
 * packed ABI. */
typedef struct __attribute__((packed)) CodexBattleRewardOwnerV1 {
    uint32_t magic;
    uint32_t magic_inverse;
    uint16_t version;
    uint16_t struct_size;
    uint32_t crc32;
    uint32_t generation;
    uint8_t window;
    uint8_t journal_phase;
    uint8_t result_kind;
    uint8_t last_command;
    uint32_t session_nonce;
    uint32_t match_id;
    uint32_t last_request_sequence;
    uint32_t last_payload_hash;
    uint32_t pending_sequence;
    uint32_t pending_payload_hash;
    uint32_t transaction_id;
    uint32_t destination_token;
    uint32_t personality;
    uint32_t ot_id;
    uint16_t item_id;
    uint16_t quantity;
    uint16_t bag_quantity_before;
    uint16_t species_id;
    uint16_t held_item_id;
    uint16_t ball_item_id;
    uint16_t moves[4];
    uint8_t level;
    uint8_t ability_slot;
    uint8_t nature_id;
    uint8_t presence;
    uint8_t ivs[6];
    uint8_t evs[6];
    uint8_t shiny;
    uint8_t tera_type;
    uint16_t last_result;
    uint16_t committed_count;
    uint16_t error_count;
    uint16_t reset_recovery_count;
    uint16_t flags;
    uint8_t destination_kind;
    uint8_t destination_box;
    uint8_t destination_slot;
    uint8_t reserved0;
    uint32_t delivery_fingerprint;
    uint8_t reserved[8];
} CodexBattleRewardOwnerV1;

_Static_assert(sizeof(CodexBattleRewardMonV1) == 32u,
               "reward mon request ABI differs");
_Static_assert(sizeof(CodexBattleRewardOwnerV1) == 128u,
               "reward save owner ABI differs");
_Static_assert(offsetof(CodexBattleRewardOwnerV1, crc32) == 12u,
               "reward owner CRC offset differs");
_Static_assert(offsetof(CodexBattleRewardOwnerV1, delivery_fingerprint) == 116u,
               "reward owner fingerprint offset differs");

#define gCodexBattleRewardOwner \
    ((volatile CodexBattleRewardOwnerV1 *)(uintptr_t)CODEX_REWARD_OWNER_ADDRESS)

#endif
