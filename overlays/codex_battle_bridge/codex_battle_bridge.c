/* T26 Stage 43: gameplay-neutral RetroArch NCI mailbox and PING/PONG poller. */

#include "codex_battle_bridge.h"

#include <stdint.h>

#define CODEX_BATTLE_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))
#define PTR(type, address) ((type)(uintptr_t)(address))

typedef void (*VoidFn)(void);

enum {
    CODEX_BATTLE_ABI_ID = 0x43424231u, /* CBB1 */
    CODEX_BATTLE_REQUEST_CRC_SIZE = 48u,
    CODEX_BATTLE_REQUEST_COPY_SIZE = 56u,
    CODEX_BATTLE_PING_PAYLOAD_SIZE = 8u,
    CODEX_BATTLE_PONG_PAYLOAD_SIZE = 12u,
    CODEX_BATTLE_SNAPSHOT_PAYLOAD_SIZE = 48u,
    CODEX_BATTLE_TIMER0 = 0x04000100u,
    CODEX_BATTLE_TIMER1 = 0x04000104u,
    CODEX_BATTLE_VCOUNT = 0x04000006u,
    CODEX_BATTLE_MAIN_COUNTER = 0x03003154u,
    CODEX_BATTLE_GLOBAL_RNG = 0x03005040u,
};

_Static_assert(CODEX_BATTLE_PROTOCOL_MAJOR == 1u,
               "Codex Battle protocol major differs");
_Static_assert(CODEX_BATTLE_PROTOCOL_MINOR == 0u,
               "Codex Battle protocol minor differs");
_Static_assert(CODEX_BATTLE_REQUEST_OFFSET == 0x80u,
               "Codex Battle request ABI differs");
_Static_assert(CODEX_BATTLE_REQUEST_SIZE == 0x40u,
               "Codex Battle request span differs");
_Static_assert(CODEX_BATTLE_SNAPSHOT_OFFSET == 0x50u,
               "Codex Battle snapshot ABI differs");

static void CbbMemoryBarrier(void)
{
    __asm__ volatile("" ::: "memory");
}

static uint32_t CbbCrcByte(uint32_t crc, uint8_t value)
{
    crc ^= value;
    for (uint32_t bit = 0u; bit < 8u; ++bit) {
        uint32_t mask = 0u - (crc & 1u);
        crc = (crc >> 1) ^ (0xEDB88320u & mask);
    }
    return crc;
}

static uint32_t CbbCrcVolatile(uint32_t crc,
                               const volatile uint8_t *bytes,
                               uint32_t size)
{
    for (uint32_t index = 0u; index < size; ++index)
        crc = CbbCrcByte(crc, bytes[index]);
    return crc;
}

static uint32_t CbbCrcLocal(uint32_t crc, const uint8_t *bytes, uint32_t size)
{
    for (uint32_t index = 0u; index < size; ++index)
        crc = CbbCrcByte(crc, bytes[index]);
    return crc;
}

static uint32_t CbbCrc32Local(const uint8_t *bytes, uint32_t size)
{
    return CbbCrcLocal(0xFFFFFFFFu, bytes, size) ^ 0xFFFFFFFFu;
}

static uint16_t CbbRead16(const uint8_t *bytes)
{
    return (uint16_t)((uint16_t)bytes[0]
                      | ((uint16_t)bytes[1] << 8));
}

static uint32_t CbbRead32(const uint8_t *bytes)
{
    return (uint32_t)bytes[0]
        | ((uint32_t)bytes[1] << 8)
        | ((uint32_t)bytes[2] << 16)
        | ((uint32_t)bytes[3] << 24);
}

static uint32_t CbbSnapshotCrc(void)
{
    const volatile uint8_t *base =
        (const volatile uint8_t *)(uintptr_t)CODEX_BATTLE_MAILBOX_ADDRESS;
    uint32_t crc = CbbCrcVolatile(0xFFFFFFFFu, base, 0x40u);
    crc = CbbCrcVolatile(crc, base + CODEX_BATTLE_SNAPSHOT_OFFSET,
                         CODEX_BATTLE_SNAPSHOT_SIZE);
    return crc ^ 0xFFFFFFFFu;
}

static uint32_t CbbNextSequence(uint32_t current)
{
    uint32_t next = current + 1u;
    return next == 0u ? 1u : next;
}

static void CbbPublishSnapshot(uint16_t status)
{
    volatile CodexBattleMailbox *mailbox = gCodexBattleMailbox;
    uint32_t sequence = CbbNextSequence(mailbox->snapshot_sequence);
    mailbox->snapshot_payload_size = CODEX_BATTLE_SNAPSHOT_PAYLOAD_SIZE;
    mailbox->current_status = status;
    mailbox->snapshot_crc32 = CbbSnapshotCrc();
    CbbMemoryBarrier();
    mailbox->snapshot_sequence_inverse = ~sequence;
    CbbMemoryBarrier();
    mailbox->snapshot_sequence = sequence;
}

static uint32_t CbbMixNonce(uint32_t value)
{
    value ^= value << 13;
    value ^= value >> 17;
    value ^= value << 5;
    value ^= CODEX_BATTLE_STAGE_IDENTITY;
    return value != 0u ? value : 0x43425831u;
}

static uint32_t CbbBootNonce(void)
{
    uint32_t seed = *(volatile uint16_t *)(uintptr_t)CODEX_BATTLE_TIMER0;
    seed |= (uint32_t)*(volatile uint16_t *)(uintptr_t)CODEX_BATTLE_TIMER1 << 16;
    seed ^= (uint32_t)*(volatile uint16_t *)(uintptr_t)CODEX_BATTLE_VCOUNT << 8;
    seed ^= *(volatile uint32_t *)(uintptr_t)CODEX_BATTLE_MAIN_COUNTER;
    /* Read only: the game's RNG stream is never advanced or rewritten. */
    seed ^= *(volatile uint32_t *)(uintptr_t)CODEX_BATTLE_GLOBAL_RNG;
    return CbbMixNonce(seed);
}

static int CbbHeaderValid(void)
{
    volatile CodexBattleMailbox *mailbox = gCodexBattleMailbox;
    return mailbox->magic == CODEX_BATTLE_MAGIC
        && mailbox->protocol_major == CODEX_BATTLE_PROTOCOL_MAJOR
        && mailbox->protocol_minor == CODEX_BATTLE_PROTOCOL_MINOR
        && mailbox->struct_size == CODEX_BATTLE_MAILBOX_SIZE
        && mailbox->header_size == CODEX_BATTLE_HEADER_SIZE
        && mailbox->request_offset == CODEX_BATTLE_REQUEST_OFFSET
        && mailbox->request_size == CODEX_BATTLE_REQUEST_SIZE
        && mailbox->snapshot_offset == CODEX_BATTLE_SNAPSHOT_OFFSET
        && mailbox->snapshot_size == CODEX_BATTLE_SNAPSHOT_SIZE
        && mailbox->capabilities == CODEX_BATTLE_CAPABILITIES
        && mailbox->stage_number == CODEX_BATTLE_STAGE_NUMBER
        && mailbox->stage_identity == CODEX_BATTLE_STAGE_IDENTITY
        && mailbox->base_rom_crc32 == CODEX_BATTLE_BASE_ROM_CRC32
        && mailbox->build_identity == CODEX_BATTLE_BUILD_IDENTITY
        && mailbox->ram_address == CODEX_BATTLE_MAILBOX_ADDRESS
        && mailbox->reserved_size == CODEX_BATTLE_RESERVED_SIZE
        && mailbox->request_payload_max == CODEX_BATTLE_REQUEST_PAYLOAD_MAX
        && mailbox->session_nonce != 0u
        && mailbox->session_nonce_inverse == ~mailbox->session_nonce;
}

CODEX_BATTLE_EXPORT(CodexBattleBridge_InitializeWithNonce)
void CodexBattleBridge_InitializeWithNonce(uint32_t nonce)
{
    volatile uint8_t *raw =
        (volatile uint8_t *)(uintptr_t)CODEX_BATTLE_MAILBOX_ADDRESS;
    for (uint32_t index = 0u; index < CODEX_BATTLE_MAILBOX_SIZE; ++index)
        raw[index] = 0u;
    volatile CodexBattleMailbox *mailbox = gCodexBattleMailbox;
    nonce = nonce != 0u ? nonce : 0x43425831u;
    mailbox->magic = CODEX_BATTLE_MAGIC;
    mailbox->protocol_major = CODEX_BATTLE_PROTOCOL_MAJOR;
    mailbox->protocol_minor = CODEX_BATTLE_PROTOCOL_MINOR;
    mailbox->struct_size = CODEX_BATTLE_MAILBOX_SIZE;
    mailbox->header_size = CODEX_BATTLE_HEADER_SIZE;
    mailbox->request_offset = CODEX_BATTLE_REQUEST_OFFSET;
    mailbox->request_size = CODEX_BATTLE_REQUEST_SIZE;
    mailbox->snapshot_offset = CODEX_BATTLE_SNAPSHOT_OFFSET;
    mailbox->snapshot_size = CODEX_BATTLE_SNAPSHOT_SIZE;
    mailbox->capabilities = CODEX_BATTLE_CAPABILITIES;
    mailbox->stage_number = CODEX_BATTLE_STAGE_NUMBER;
    mailbox->phase = CODEX_BATTLE_PHASE_IDLE;
    mailbox->stage_identity = CODEX_BATTLE_STAGE_IDENTITY;
    mailbox->base_rom_crc32 = CODEX_BATTLE_BASE_ROM_CRC32;
    mailbox->build_identity = CODEX_BATTLE_BUILD_IDENTITY;
    mailbox->session_nonce = nonce;
    mailbox->session_nonce_inverse = ~nonce;
    mailbox->ram_address = CODEX_BATTLE_MAILBOX_ADDRESS;
    mailbox->reserved_size = CODEX_BATTLE_RESERVED_SIZE;
    mailbox->request_payload_max = CODEX_BATTLE_REQUEST_PAYLOAD_MAX;
    mailbox->command_count = 1u;
    mailbox->response_status = CODEX_BATTLE_STATUS_READY;
    mailbox->response_error = CODEX_BATTLE_ERROR_NONE;
    mailbox->response_sequence_inverse = ~0u;
    mailbox->pong_token_inverse = ~0u;
    mailbox->pong_magic = CODEX_BATTLE_PONG_MAGIC;
    CbbPublishSnapshot(CODEX_BATTLE_STATUS_READY);
}

CODEX_BATTLE_EXPORT(CodexBattleBridge_Initialize)
void CodexBattleBridge_Initialize(void)
{
    CodexBattleBridge_InitializeWithNonce(CbbBootNonce());
}

static void CbbReject(uint32_t sequence, uint16_t command,
                      uint16_t error, uint32_t fingerprint)
{
    volatile CodexBattleMailbox *mailbox = gCodexBattleMailbox;
    if (mailbox->last_rejected_sequence == sequence
            && mailbox->last_rejected_fingerprint == fingerprint)
        return;
    mailbox->response_sequence = sequence;
    mailbox->response_sequence_inverse = ~sequence;
    mailbox->response_status = CODEX_BATTLE_STATUS_ERROR;
    mailbox->response_error = error;
    mailbox->response_payload_size = 0u;
    mailbox->last_command = command;
    mailbox->pong_token = 0u;
    mailbox->pong_token_inverse = ~0u;
    mailbox->last_rejected_sequence = sequence;
    mailbox->last_rejected_fingerprint = fingerprint;
    mailbox->rejected_count += 1u;
    CbbPublishSnapshot(CODEX_BATTLE_STATUS_ERROR);
}

CODEX_BATTLE_EXPORT(CodexBattleBridge_Poll)
void CodexBattleBridge_Poll(void)
{
    volatile CodexBattleMailbox *mailbox = gCodexBattleMailbox;
    if (!CbbHeaderValid()) {
        CodexBattleBridge_Initialize();
        return;
    }

    uint32_t sequence_before = mailbox->request_sequence;
    uint32_t inverse_before = mailbox->request_sequence_inverse;
    if (sequence_before == 0u || inverse_before != ~sequence_before)
        return; /* Uncommitted/torn host write: do not publish or consume. */

    uint32_t accepted = mailbox->last_accepted_sequence;
    uint32_t expected = CbbNextSequence(accepted);
    if (sequence_before == accepted)
        return; /* Exact duplicate: idempotent and byte-stable. */

    uint8_t request[CODEX_BATTLE_REQUEST_COPY_SIZE];
    const volatile uint8_t *request_source =
        (const volatile uint8_t *)(uintptr_t)(CODEX_BATTLE_MAILBOX_ADDRESS
                                              + CODEX_BATTLE_REQUEST_OFFSET);
    for (uint32_t index = 0u; index < CODEX_BATTLE_REQUEST_COPY_SIZE; ++index)
        request[index] = request_source[index];
    CbbMemoryBarrier();
    uint32_t inverse_after = mailbox->request_sequence_inverse;
    uint32_t sequence_after = mailbox->request_sequence;
    if (sequence_before != sequence_after || inverse_before != inverse_after
            || inverse_after != ~sequence_after)
        return;

    uint32_t nonce = CbbRead32(request + 0u);
    uint16_t command = CbbRead16(request + 4u);
    uint16_t phase = CbbRead16(request + 6u);
    uint16_t payload_size = CbbRead16(request + 8u);
    uint16_t flags = CbbRead16(request + 10u);
    uint32_t payload_crc = CbbRead32(request + 12u);
    uint32_t request_crc = CbbRead32(request + 48u);
    uint32_t reserved = CbbRead32(request + 52u);
    uint32_t fingerprint = request_crc ^ payload_crc ^ nonce ^ sequence_after
        ^ ((uint32_t)command << 16) ^ payload_size;

    if (sequence_after != expected) {
        CbbReject(sequence_after, command,
                  sequence_after < expected
                      ? CODEX_BATTLE_ERROR_STALE_SEQUENCE
                      : CODEX_BATTLE_ERROR_FUTURE_SEQUENCE,
                  fingerprint);
        return;
    }
    if (nonce != mailbox->session_nonce) {
        CbbReject(sequence_after, command, CODEX_BATTLE_ERROR_WRONG_NONCE,
                  fingerprint);
        return;
    }
    if (payload_size > CODEX_BATTLE_REQUEST_PAYLOAD_MAX) {
        CbbReject(sequence_after, command, CODEX_BATTLE_ERROR_OVERSIZE,
                  fingerprint);
        return;
    }
    if (flags != 0u || reserved != 0u) {
        CbbReject(sequence_after, command, CODEX_BATTLE_ERROR_FLAGS,
                  fingerprint);
        return;
    }
    if (CbbCrc32Local(request + 16u, payload_size) != payload_crc) {
        CbbReject(sequence_after, command, CODEX_BATTLE_ERROR_PAYLOAD_CRC,
                  fingerprint);
        return;
    }
    if (CbbCrc32Local(request, CODEX_BATTLE_REQUEST_CRC_SIZE) != request_crc) {
        CbbReject(sequence_after, command, CODEX_BATTLE_ERROR_REQUEST_CRC,
                  fingerprint);
        return;
    }
    if (phase != mailbox->phase) {
        CbbReject(sequence_after, command, CODEX_BATTLE_ERROR_WRONG_PHASE,
                  fingerprint);
        return;
    }
    if (command != CODEX_BATTLE_COMMAND_PING) {
        CbbReject(sequence_after, command, CODEX_BATTLE_ERROR_UNKNOWN_COMMAND,
                  fingerprint);
        return;
    }
    if (payload_size != CODEX_BATTLE_PING_PAYLOAD_SIZE) {
        CbbReject(sequence_after, command, CODEX_BATTLE_ERROR_PAYLOAD_FORMAT,
                  fingerprint);
        return;
    }
    uint32_t token = CbbRead32(request + 16u);
    uint32_t token_inverse = CbbRead32(request + 20u);
    if (token == 0u || token_inverse != ~token) {
        CbbReject(sequence_after, command, CODEX_BATTLE_ERROR_PAYLOAD_FORMAT,
                  fingerprint);
        return;
    }

    mailbox->response_sequence = sequence_after;
    mailbox->response_sequence_inverse = ~sequence_after;
    mailbox->response_status = CODEX_BATTLE_STATUS_PONG;
    mailbox->response_error = CODEX_BATTLE_ERROR_NONE;
    mailbox->response_payload_size = CODEX_BATTLE_PONG_PAYLOAD_SIZE;
    mailbox->last_command = CODEX_BATTLE_COMMAND_PING;
    mailbox->pong_token = token;
    mailbox->pong_token_inverse = ~token;
    mailbox->pong_magic = CODEX_BATTLE_PONG_MAGIC;
    mailbox->accepted_request_crc32 = request_crc;
    mailbox->last_accepted_sequence = sequence_after;
    mailbox->last_rejected_sequence = 0u;
    mailbox->last_rejected_fingerprint = 0u;
    CbbPublishSnapshot(CODEX_BATTLE_STATUS_PONG);
}

CODEX_BATTLE_EXPORT(CodexBattleBridge_ReadKeysAdapter)
void CodexBattleBridge_ReadKeysAdapter(void)
{
    PTR(VoidFn, CODEX_BATTLE_DELEGATE_READ_KEYS)();
    CodexBattleBridge_Poll();
}

CODEX_BATTLE_EXPORT(CodexBattleBridge_Probe)
uint32_t CodexBattleBridge_Probe(uint32_t selector)
{
    volatile CodexBattleMailbox *mailbox = gCodexBattleMailbox;
    switch (selector) {
    case CODEX_BATTLE_PROBE_ABI: return CODEX_BATTLE_ABI_ID;
    case CODEX_BATTLE_PROBE_ADDRESS: return CODEX_BATTLE_MAILBOX_ADDRESS;
    case CODEX_BATTLE_PROBE_STRUCT_SIZE: return CODEX_BATTLE_MAILBOX_SIZE;
    case CODEX_BATTLE_PROBE_RESERVED_SIZE: return CODEX_BATTLE_RESERVED_SIZE;
    case CODEX_BATTLE_PROBE_CAPABILITIES: return CODEX_BATTLE_CAPABILITIES;
    case CODEX_BATTLE_PROBE_STAGE: return CODEX_BATTLE_STAGE_NUMBER;
    case CODEX_BATTLE_PROBE_IDENTITY: return CODEX_BATTLE_STAGE_IDENTITY;
    case CODEX_BATTLE_PROBE_NONCE: return mailbox->session_nonce;
    case CODEX_BATTLE_PROBE_SNAPSHOT_SEQUENCE:
        return mailbox->snapshot_sequence;
    case CODEX_BATTLE_PROBE_REQUEST_SEQUENCE:
        return mailbox->last_accepted_sequence;
    case CODEX_BATTLE_PROBE_RESPONSE_STATUS: return mailbox->response_status;
    case CODEX_BATTLE_PROBE_RESPONSE_ERROR: return mailbox->response_error;
    case CODEX_BATTLE_PROBE_REJECTED_COUNT: return mailbox->rejected_count;
    default: return 0u;
    }
}
