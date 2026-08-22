#ifndef VEGA_CODEX_BATTLE_RUNTIME_H
#define VEGA_CODEX_BATTLE_RUNTIME_H

#include <stddef.h>
#include <stdint.h>

#include "codex_battle_runtime_generated.h"

enum CodexBattleRuntimePhase {
    CODEX_RUNTIME_PHASE_IDLE = 1,
    CODEX_RUNTIME_PHASE_CONFIGURING = 2,
    CODEX_RUNTIME_PHASE_TEAM_PREVIEW = 3,
    CODEX_RUNTIME_PHASE_AWAITING_PLAYER_SELECTION = 4,
    CODEX_RUNTIME_PHASE_AWAITING_CODEX_SELECTION = 5,
    CODEX_RUNTIME_PHASE_BATTLE_AWAITING_ACTION = 6,
    CODEX_RUNTIME_PHASE_BATTLE_AWAITING_MOVE = 7,
    CODEX_RUNTIME_PHASE_BATTLE_AWAITING_SWITCH = 8,
    CODEX_RUNTIME_PHASE_BATTLE_RESOLVING = 9,
    CODEX_RUNTIME_PHASE_RESULT = 10,
    CODEX_RUNTIME_PHASE_DISCONNECTED = 11,
    CODEX_RUNTIME_PHASE_ABORTED = 12,
};

enum CodexBattleRuntimeCommand {
    CODEX_RUNTIME_COMMAND_CONFIGURE = 1,
    CODEX_RUNTIME_COMMAND_UPLOAD_MEMBER = 2,
    CODEX_RUNTIME_COMMAND_COMMIT_TEAM = 3,
    CODEX_RUNTIME_COMMAND_CHOOSE_TEAM = 4,
    CODEX_RUNTIME_COMMAND_MOVE = 5,
    CODEX_RUNTIME_COMMAND_SWITCH = 6,
    CODEX_RUNTIME_COMMAND_FORFEIT = 7,
    CODEX_RUNTIME_COMMAND_DISCONNECT_CPU = 8,
    CODEX_RUNTIME_COMMAND_DISCONNECT_FORFEIT = 9,
    CODEX_RUNTIME_COMMAND_ABORT = 10,
};

enum CodexBattleRuntimeError {
    CODEX_RUNTIME_ERROR_NONE = 0,
    CODEX_RUNTIME_ERROR_FUTURE_SEQUENCE = 1,
    CODEX_RUNTIME_ERROR_STALE_SEQUENCE = 2,
    CODEX_RUNTIME_ERROR_WRONG_NONCE = 3,
    CODEX_RUNTIME_ERROR_OVERSIZE = 4,
    CODEX_RUNTIME_ERROR_PAYLOAD_CRC = 5,
    CODEX_RUNTIME_ERROR_REQUEST_CRC = 6,
    CODEX_RUNTIME_ERROR_WRONG_PHASE = 7,
    CODEX_RUNTIME_ERROR_UNKNOWN_COMMAND = 8,
    CODEX_RUNTIME_ERROR_PAYLOAD_FORMAT = 9,
    CODEX_RUNTIME_ERROR_FLAGS = 10,
    CODEX_RUNTIME_ERROR_WRONG_MATCH = 11,
    CODEX_RUNTIME_ERROR_WRONG_TURN = 12,
    CODEX_RUNTIME_ERROR_INVALID_MEMBER = 13,
    CODEX_RUNTIME_ERROR_REGULATION = 14,
    CODEX_RUNTIME_ERROR_ILLEGAL_ACTION = 15,
    CODEX_RUNTIME_ERROR_BUSY = 16,
    CODEX_RUNTIME_ERROR_PRIVATE_BOUNDARY = 17,
};

typedef struct __attribute__((packed)) CodexBattleTeamMemberV1 {
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
    uint16_t reserved;
} CodexBattleTeamMemberV1;

typedef struct __attribute__((packed)) CodexBattleRuntimeSnapshotV2 {
    uint32_t crc32;
    uint16_t payload_size;
    uint16_t current_status;
    uint32_t response_sequence;
    uint32_t response_sequence_inverse;
    uint16_t response_status;
    uint16_t response_error;
    uint16_t last_command;
    uint16_t response_payload_size;
    uint32_t last_accepted_sequence;
    uint32_t rejected_count;
    uint16_t action_mask;
    uint16_t turn;
    uint8_t legal_switch_mask;
    uint8_t legal_move_mask;
    uint16_t phase_echo;
    uint8_t legal_gimmicks[4];
    /* Before battle: six preview species.  While battle_flags.live is set:
     * five live combat stats followed by packed public appearance flags and
     * an opaque first-appearance identity for the active player Pokemon. */
    uint16_t codex_preview_species[6];
    uint16_t player_preview_species[6];
    /* Live: own exact HP.  Pre-battle: these 12 bytes carry the six public
     * player levels plus packed gender/shiny team-preview details. */
    uint16_t own_current_hp[3];
    uint16_t own_max_hp[3];
    uint16_t own_live_moves[4];
    uint8_t own_live_pp[4];
    uint16_t public_player_species;
    uint8_t public_player_hp_percent;
    uint8_t battle_flags;
} CodexBattleRuntimeSnapshotV2;

/* A compact copy of screen-public battle messages and explicit ability
 * pop-ups.  Private choice commands are never admitted to this ring. */
typedef struct __attribute__((packed)) CodexBattlePublicEventV2 {
    uint8_t packed[11];
} CodexBattlePublicEventV2;

/* Owner-safe public state living in the final 180 bytes of the private
 * runtime allocation.  The protocol exposes this exact bounded subrange,
 * never the surrounding owner/private match state. */
typedef struct __attribute__((packed)) CodexBattlePublicStateV2 {
    uint32_t crc32;
    uint16_t struct_size;
    uint8_t version;
    uint8_t event_capacity;
    uint32_t sequence;
    uint32_t sequence_inverse;
    uint16_t event_sequence;
    uint8_t event_head;
    uint8_t event_count;
    uint16_t own_active_species;
    uint8_t own_status;
    uint8_t own_status_detail;
    uint8_t player_status;
    uint8_t player_status_detail;
    uint8_t stat_stages_packed[7];
    uint32_t status2[2];
    uint32_t status3[2];
    uint16_t own_item_id;
    uint16_t own_ability_id;
    uint16_t player_revealed_item_id;
    uint16_t player_revealed_ability_id;
    uint16_t player_revealed_moves[4];
    uint8_t types_packed[4];
    uint16_t weather;
    uint8_t weather_duration;
    uint8_t terrain;
    uint8_t terrain_timer;
    uint8_t field_timers[8];
    uint16_t side_statuses[2];
    uint8_t classic_side_timers_packed[4];
    uint8_t entry_hazards[2];
    uint8_t modern_side_timers_packed[11];
    uint8_t mechanic_used_mask;
    uint8_t native_gimmick_flags;
    uint8_t player_level;
    uint8_t move_locks_packed[6];
    uint8_t personal_effects_packed[16];
    uint8_t own_party_status_packed[2];
    uint8_t wish_future_packed[4];
    uint8_t player_item_knowledge;
    uint8_t own_level;
    CodexBattlePublicEventV2 events[4];
} CodexBattlePublicStateV2;

typedef struct __attribute__((packed)) CodexBattleRuntimeRequestV2 {
    uint32_t session_nonce;
    uint32_t match_id;
    uint16_t expected_phase;
    uint16_t command;
    uint16_t expected_turn;
    uint16_t payload_size;
    uint32_t payload_crc32;
    uint8_t payload[64];
    uint32_t request_crc32;
    uint32_t request_sequence_inverse;
    uint32_t request_sequence;
} CodexBattleRuntimeRequestV2;

typedef struct __attribute__((packed)) CodexBattleRuntimeMailboxV2 {
    uint32_t magic;
    uint16_t protocol_major;
    uint16_t protocol_minor;
    uint16_t struct_size;
    uint16_t header_size;
    uint16_t snapshot_offset;
    uint16_t snapshot_size;
    uint16_t request_offset;
    uint16_t request_size;
    uint16_t request_payload_max;
    uint16_t stage_number;
    uint32_t capabilities;
    uint32_t stage_identity;
    uint32_t build_identity;
    uint32_t session_nonce;
    uint32_t session_nonce_inverse;
    uint16_t phase;
    uint16_t status;
    uint32_t match_id;
    uint16_t turn;
    uint16_t reserved0;
    uint32_t snapshot_sequence;
    uint32_t snapshot_sequence_inverse;
    CodexBattleRuntimeSnapshotV2 snapshot;
    CodexBattleRuntimeRequestV2 request;
} CodexBattleRuntimeMailboxV2;

typedef struct __attribute__((packed)) CodexBattleRuntimeState {
    uint32_t magic;
    uint32_t magic_inverse;
    uint32_t session_nonce;
    uint32_t match_id;
    uint16_t phase;
    uint16_t status;
    uint8_t active;
    uint8_t configured;
    uint8_t upload_mask;
    uint8_t team_valid;
    uint8_t level_mode;
    uint8_t switch_context;
    uint8_t codex_selection_valid;
    uint8_t player_selection_valid;
    uint16_t turn;
    /* Set until the reception script has returned from trainerbattle and
     * closed its terminal message.  A newer match must not overwrite state
     * while an older field script can still run a cleanup callback. */
    uint16_t field_completion_pending;
    uint8_t player_selected[3];
    uint8_t codex_selected[3];
    uint8_t player_count_before;
    uint8_t enemy_count_before;
    uint8_t action_kind;
    uint8_t action_move;
    uint8_t action_target;
    uint8_t action_gimmick;
    uint8_t action_switch;
    uint8_t disconnect_mode;
    uint8_t private_player_committed;
    uint8_t controller_installed;
    uint32_t battle_flags_before;
    uint32_t rng_before;
    uint32_t party_hash_before;
    uint32_t save_hash_before;
    uint32_t opponent_delegate;
    uint32_t last_request_sequence;
    uint32_t rejected_count;
    uint32_t private_seal_crc32;
    uint16_t private_seal_length;
    uint16_t cleanup_reason;
    uint8_t selected_order_before[6];
    uint16_t player_preview_species[6];
    uint8_t revealed_player_mask;
    uint8_t public_flags;
    uint8_t legal_move_mask;
    uint8_t legal_switch_mask;
    uint8_t legal_gimmicks[4];
    uint8_t player_choice_observed;
    uint8_t mechanic_used_mask;
    CodexBattleTeamMemberV1 team[6];
    uint8_t player_party_backup[600];
    uint16_t facility_vars_before[5];
    uint8_t facility_flag_before;
    uint8_t public_event_active_mask;
    uint32_t last_rejected_sequence;
    uint32_t last_rejected_request_crc32;
    uint32_t current_request_crc32;
    uint32_t money_before;
    uint8_t disable_bag_flag_before;
    uint8_t trainer_flag_before;
    uint8_t save1_dex_seen_before[150];
    uint32_t game_stats_before[64];
    uint8_t save2_pokedex_before[16];
    CodexBattlePublicStateV2 public_state;
} CodexBattleRuntimeState;

_Static_assert(sizeof(CodexBattleTeamMemberV1) == 32u,
               "Codex member ABI differs");
_Static_assert(sizeof(CodexBattleRuntimeSnapshotV2) == 96u,
               "Codex snapshot ABI differs");
_Static_assert(sizeof(CodexBattlePublicEventV2) == 11u,
               "Codex public event ABI differs");
_Static_assert(sizeof(CodexBattlePublicStateV2) == 180u,
               "Codex public state ABI differs");
_Static_assert(sizeof(CodexBattleRuntimeRequestV2) == 96u,
               "Codex request ABI differs");
_Static_assert(sizeof(CodexBattleRuntimeMailboxV2) == 256u,
               "Codex runtime mailbox ABI differs");
_Static_assert(sizeof(CodexBattleRuntimeState) == CODEX_RUNTIME_STATE_SIZE,
               "Codex runtime state ABI differs");
_Static_assert(offsetof(CodexBattleRuntimeState, public_state)
                   == CODEX_RUNTIME_PUBLIC_STATE_OFFSET,
               "Codex public state offset differs");

#define gCodexBattleRuntimeMailbox \
    ((volatile CodexBattleRuntimeMailboxV2 *)(uintptr_t)CODEX_RUNTIME_MAILBOX_ADDRESS)
#define gCodexBattleRuntimeState \
    ((volatile CodexBattleRuntimeState *)(uintptr_t)CODEX_RUNTIME_STATE_ADDRESS)

#endif
