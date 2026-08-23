/* T28 Stage 45: match-bound, exactly-once Codex Battle rewards.
 *
 * T29 recompiles this same owner/runtime with
 * CODEX_WINDOWS_CATALOG_ENABLED=1.  The default remains byte-compatible with
 * the completed Stage 45 artifact; the enabled build adds an IDLE-only
 * Windows catalog context without weakening the match-bound reward window. */

#ifndef CODEX_WINDOWS_CATALOG_ENABLED
#define CODEX_WINDOWS_CATALOG_ENABLED 0
#endif

#ifndef CODEX_WINDOWS_BOX14_VAULT_ENABLED
#define CODEX_WINDOWS_BOX14_VAULT_ENABLED 0
#endif

#if CODEX_WINDOWS_BOX14_VAULT_ENABLED && !CODEX_WINDOWS_CATALOG_ENABLED
#error "Box 14 vault requires the Windows catalog field context"
#endif

#ifndef CODEX_CATALOG_MAP_GROUP
#define CODEX_CATALOG_MAP_GROUP 96u
#endif

#ifndef CODEX_CATALOG_MAP_NUMBER
#define CODEX_CATALOG_MAP_NUMBER 5u
#endif

#include "codex_battle_rewards.h"

#include <stdint.h>

#include "../codex_battle_runtime/codex_battle_runtime.h"

#define CWR_EXPORT(name) \
    __attribute__((section(".text." #name), used, noinline, externally_visible))
#define PTR(type, address) ((type)(uintptr_t)(address))

typedef uint8_t u8;
typedef uint16_t u16;
typedef uint32_t u32;

typedef struct Pokemon100 { u8 bytes[100]; } Pokemon100;

typedef void (*VoidFn)(void);
typedef u8 (*U8Fn)(u8);
typedef u16 (*U16Fn)(void);
typedef u8 (*BagFn)(u16, u16);
typedef void (*CreateMonFn)(void *, u16, u8, u8, u8, u32, u8, u32);
typedef void (*SetMonDataFn)(void *, int, const void *);
typedef u32 (*GetMonDataFn)(const void *, int, u8 *);
typedef u16 (*GetMonAbilityFn)(const void *);
typedef void (*CalculateStatsFn)(void *);
typedef u8 (*CalculatePpFn)(u16, u8, u8);
typedef u8 (*CalculatePartyCountFn)(void);
typedef u8 (*GiveMonFn)(void *);
typedef u32 (*GetBoxMonDataAtFn)(u8, u8, int);
typedef void (*ZeroBoxMonAtFn)(u8, u8);
#if CODEX_WINDOWS_BOX14_VAULT_ENABLED
typedef void *(*GetBoxedMonPtrFn)(u8, u8);
typedef void (*SetBoxMonAtFn)(u8, u8, void *);
typedef u8 (*IsMailFn)(u16);
#endif
typedef u8 (*TryWriteSectorFn)(u16, const void *);
typedef void (*ReadFlashFn)(u16, u32, void *, u32);
typedef u8 (*TrySavingDataFn)(u8);
typedef u16 (*VarGetFn)(u16);
typedef u8 (*VarSetFn)(u16, u16);
typedef void (*SetMainCallbackFn)(VoidFn);
typedef void (*BufferMonMoveFn)(u8);

enum {
    CWR_T27_STATE_MAGIC = 0x32524243u,
    CWR_T27_PHASE_IDLE = 1u,
    CWR_T27_PHASE_RESULT = 10u,
    CWR_T27_STATUS_READY = 1u,
    CWR_T27_STATUS_ACCEPTED = 2u,
    CWR_T27_STATUS_ERROR = 3u,
    CWR_T27_STATUS_RESULT = 6u,
    CWR_REQUEST_CRC_SIZE = 84u,
    CWR_REQUEST_COPY_SIZE = 92u,
    CWR_SAVE_SECTOR = 31u,
    CWR_SAVE_SECTOR_DATA_SIZE = 0x0FF0u,
    CWR_SAVE_SECTOR_SIZE = 0x1000u,
    CWR_PARTY_SIZE = 6u,
    CWR_MON_SIZE = 100u,
    CWR_BOX_MON_SIZE = 80u,
    CWR_BOX_COUNT = 14u,
    CWR_BOX_CAPACITY = 30u,
    CWR_PC_BOX_VAR = 0x4037u,
    CWR_MON_DATA_PERSONALITY = 0u,
    CWR_MON_DATA_OT_ID = 1u,
    CWR_MON_DATA_SANITY_HAS_SPECIES = 5u,
    CWR_MON_DATA_SPECIES = 11u,
    CWR_MON_DATA_SPECIES2 = 65u,
    CWR_MON_DATA_HELD_ITEM = 12u,
    CWR_MON_DATA_MOVE1 = 13u,
    CWR_MON_DATA_PP1 = 17u,
    CWR_MON_DATA_PP_BONUSES = 21u,
    CWR_MON_DATA_EV_HP = 26u,
    CWR_MON_DATA_POKEBALL = 38u,
    CWR_MON_DATA_IV_HP = 39u,
    CWR_MON_DATA_LEVEL = 56u,
    CWR_MON_DATA_HP = 57u,
    CWR_MON_DATA_MAX_HP = 58u,
    CWR_NATURE_MINT_OFFSET = 0x0Fu,
    CWR_TERA_TYPE_OFFSET = 0x11u,
    CWR_MET_BITS_OFFSET = 0x46u,
    CWR_IV_BITS_OFFSET = 0x48u,
    CWR_HP_OFFSET = 0x56u,
    CWR_MAX_HP_OFFSET = 0x58u,
    CWR_HIDDEN_ABILITY_MASK = 0x1000u,
    CWR_ABILITY_NUM_MASK = 0x80000000u,
    CWR_DESTINATION_NONE = 0u,
    CWR_DESTINATION_PARTY = 1u,
    CWR_DESTINATION_BOX = 2u,
    CWR_TOKEN_PARTY = 0x10000000u,
    CWR_TOKEN_BOX = 0x20000000u,
    CWR_TOKEN_KIND_MASK = 0xF0000000u,
    CWR_OWNER_FLAG_MIGRATED = 0x0001u,
    CWR_OWNER_FLAG_RECOVERED = 0x0002u,
    CWR_OWNER_FLAG_BALL_EXPLICIT = 0x0004u,
#if CODEX_WINDOWS_CATALOG_ENABLED
    CWR_OWNER_FLAG_CATALOG = 0x0008u,
#endif
#if CODEX_WINDOWS_BOX14_VAULT_ENABLED
    CWR_OWNER_FLAG_VAULT = 0x0010u,
#endif
    CWR_TEST_MAGIC = 0x54323846u,
    CWR_OWNER_LOAD_CHECKED = 0xA5u,
    CWR_OWNER_LOAD_STABLE_FRAMES = 0xFFu,
    CWR_FAULT_PREPARE = 0x01u,
    CWR_FAULT_STAGED = 0x02u,
    CWR_FAULT_STANDARD = 0x04u,
    CWR_FAULT_COMMIT = 0x08u,
    CWR_FAULT_OPEN = 0x10u,
    CWR_FAULT_CLOSE = 0x20u,
    CWR_FAULT_AFTER_PREPARE = 0x40u,
    CWR_BATTLE_TYPE_TRAINER = 0x00000008u,
    CWR_BATTLE_TYPE_TRAINER_TOWER = 0x00080000u,
    CWR_FIELD_MAIN_CALLBACK = 0x08055E75u,
    CWR_PARTY_LEVEL_OFFSET = 0x54u,
    CWR_SUMMARY_MOVE_NAMES_OFFSET = 0x3110u,
    /* The live Japanese Summary ABI uses the original packed buffers:
     * ability name 0x318C..0x3194 (8 bytes + EOS), then description
     * 0x3195..0x31AB (22 bytes + EOS).  The aligned 0x3190/0x3198 aliases
     * overlap each other and the isEgg/control fields for the longest
     * expanded strings. */
    CWR_SUMMARY_ABILITY_NAME_OFFSET = 0x318Cu,
    CWR_SUMMARY_ABILITY_DESC_OFFSET = 0x3195u,
    CWR_SUMMARY_MODE_OFFSET = 0x31B4u,
    CWR_SUMMARY_MOVE_IDS_OFFSET = 0x3204u,
    CWR_SUMMARY_CURRENT_MON_OFFSET = 0x323Cu,
    CWR_SUMMARY_MOVE_NAME_SIZE = 9u,
    CWR_SUMMARY_ABILITY_NAME_SIZE = 9u,
    CWR_SUMMARY_ABILITY_DESC_SIZE = 23u,
    CWR_GAME_STRING_END = 0xFFu,
};

#define G_PLAYER_PARTY PTR(Pokemon100 *, 0x020241E4u)
#define G_PLAYER_COUNT PTR(volatile u8 *, 0x02023F89u)
#define G_SPECIAL_RESULT PTR(volatile u16 *, 0x02037004u)
#define G_SPECIAL_MON_BOX_ID PTR(volatile u16 *, 0x0203700Au)
#define G_SPECIAL_MON_BOX_POS PTR(volatile u16 *, 0x0203700Cu)
#define G_BATTLE_OUTCOME PTR(volatile u8 *, 0x02023DEAu)
#define G_BATTLE_FLAGS PTR(volatile u32 *, 0x02022AACu)
#define G_MAIN_SAVED_CALLBACK PTR(volatile u32 *, 0x03003138u)
#define G_MAIN_CALLBACK2 PTR(volatile u32 *, 0x03003134u)
#define G_BASE_NONCE PTR(volatile u32 *, 0x0203F828u)
#define G_SAVE_BLOCK2_PTR PTR(volatile u8 * volatile *, 0x0300504Cu)
#define G_SAVE_BLOCK1_PTR PTR(volatile u8 * volatile *, 0x03005048u)
#define G_SAVE_BUFFER PTR(volatile u8 *, CODEX_REWARD_SAVE_BUFFER_ADDRESS)
#define G_SECTOR31_IMAGE PTR(const volatile u8 *, CODEX_REWARD_SECTOR31_IMAGE_ADDRESS)
#define G_TRANSACTION_SCRATCH PTR(Pokemon100 *, CODEX_REWARD_TRANSACTION_SCRATCH_ADDRESS)
#define G_TEST_CONTROL PTR(volatile u32 *, CODEX_REWARD_TEST_CONTROL_ADDRESS)
#define G_TEST_FAULTS PTR(volatile u32 *, CODEX_REWARD_TEST_CONTROL_ADDRESS + 4u)
#define G_TRANSACTION_LOCK PTR(volatile u32 *, CODEX_REWARD_TEST_CONTROL_ADDRESS + 8u)
#define G_SUMMARY_SCREEN_PTR PTR(volatile u8 * volatile *, 0x0203B0B4u)

#define FN_T27_INITIALIZE PTR(VoidFn, CODEX_REWARD_T27_INITIALIZE)
#define FN_T27_READ_KEYS PTR(VoidFn, CODEX_REWARD_T27_READ_KEYS)
#define FN_BASE_READ_KEYS PTR(VoidFn, CODEX_REWARD_BASE_READ_KEYS)
#define FN_T27_SAVE_LOAD PTR(U8Fn, CODEX_REWARD_T27_SAVE_LOAD)
#define FN_T27_AFTER_BATTLE PTR(U16Fn, CODEX_REWARD_T27_AFTER_BATTLE)
#define FN_T27_FIELD_FINISH PTR(U16Fn, CODEX_REWARD_T27_FIELD_FINISH)
#define FN_ADD_BAG_ITEM PTR(BagFn, CODEX_REWARD_ADD_BAG_ITEM)
#define FN_REMOVE_BAG_ITEM PTR(BagFn, CODEX_REWARD_REMOVE_BAG_ITEM)
#define FN_CHECK_BAG_ITEM PTR(BagFn, CODEX_REWARD_CHECK_BAG_ITEM)
#define FN_CREATE_MON PTR(CreateMonFn, CODEX_REWARD_CREATE_MON)
#define FN_SET_MON_DATA PTR(SetMonDataFn, CODEX_REWARD_SET_MON_DATA)
#define FN_GET_MON_DATA PTR(GetMonDataFn, CODEX_REWARD_GET_MON_DATA)
#define FN_GET_MON_ABILITY PTR(GetMonAbilityFn, CODEX_REWARD_GET_MON_ABILITY)
#define FN_CALCULATE_STATS PTR(CalculateStatsFn, CODEX_REWARD_CALCULATE_STATS)
#define FN_CALCULATE_PP PTR(CalculatePpFn, CODEX_REWARD_CALCULATE_PP)
#define FN_PARTY_COUNT PTR(CalculatePartyCountFn, CODEX_REWARD_PARTY_COUNT)
#define FN_GIVE_MON PTR(GiveMonFn, CODEX_REWARD_GIVE_MON)
#define FN_GET_BOX_MON_DATA PTR(GetBoxMonDataAtFn, CODEX_REWARD_GET_BOX_MON_DATA)
#define FN_ZERO_BOX_MON_AT PTR(ZeroBoxMonAtFn, CODEX_REWARD_ZERO_BOX_MON_AT)
#if CODEX_WINDOWS_BOX14_VAULT_ENABLED
#define FN_GET_BOXED_MON PTR(GetBoxedMonPtrFn, CODEX_VAULT_GET_BOXED_MON_PTR)
#define FN_SET_BOX_MON_AT PTR(SetBoxMonAtFn, CODEX_VAULT_SET_BOX_MON_AT)
#define FN_IS_MAIL PTR(IsMailFn, CODEX_VAULT_IS_MAIL)
#endif
#define FN_TRY_WRITE_SECTOR PTR(TryWriteSectorFn, CODEX_REWARD_TRY_WRITE_SECTOR)
#define FN_READ_FLASH PTR(ReadFlashFn, CODEX_REWARD_READ_FLASH)
#define FN_TRY_SAVING_DATA PTR(TrySavingDataFn, CODEX_REWARD_TRY_SAVING_DATA)
#define FN_VAR_GET PTR(VarGetFn, CODEX_REWARD_VAR_GET)
#define FN_VAR_SET PTR(VarSetFn, CODEX_REWARD_VAR_SET)
#define FN_BATTLE_WON PTR(VoidFn, CODEX_REWARD_BATTLE_WON)
#define FN_BATTLE_LOST PTR(VoidFn, CODEX_REWARD_BATTLE_LOST)
#define FN_SET_MAIN_CALLBACK2 \
    PTR(SetMainCallbackFn, CODEX_REWARD_SET_MAIN_CALLBACK2)
#define FN_END_TRAINER_BATTLE PTR(VoidFn, CODEX_REWARD_END_TRAINER_BATTLE)
#define FN_RETURN_TO_FIELD PTR(VoidFn, CODEX_REWARD_RETURN_TO_FIELD)
#define FN_BUFFER_MON_MOVE PTR(BufferMonMoveFn, CODEX_REWARD_BUFFER_MON_MOVE)
#if CODEX_WINDOWS_CATALOG_ENABLED
#define FN_SCRIPT_CONTEXT2_ENABLED PTR(U16Fn, 0x08069219u)
#endif

void CodexBattleRewards_ReturnToFieldAdapter(void);

static void barrier(void) { __asm__ volatile("" ::: "memory"); }

static void clear_bytes(volatile void *destination, u32 size)
{
    volatile u8 *out = (volatile u8 *)destination;
    u32 index;
    for (index = 0u; index < size; ++index)
        out[index] = 0u;
}

static void copy_bytes(volatile void *destination,
                       const volatile void *source, u32 size)
{
    volatile u8 *out = (volatile u8 *)destination;
    const volatile u8 *in = (const volatile u8 *)source;
    u32 index;
    for (index = 0u; index < size; ++index)
        out[index] = in[index];
}

static void copy_game_string(volatile u8 *destination,
                             const volatile u8 *source, u32 capacity)
{
    u32 index = 0u;
    if (capacity == 0u)
        return;
    while (index + 1u < capacity && source[index] != CWR_GAME_STRING_END) {
        destination[index] = source[index];
        ++index;
    }
    destination[index++] = CWR_GAME_STRING_END;
    while (index < capacity)
        destination[index++] = CWR_GAME_STRING_END;
}

static u16 read16(const volatile u8 *bytes)
{
    return (u16)((u16)bytes[0] | ((u16)bytes[1] << 8));
}

static u32 read32(const volatile u8 *bytes)
{
    return (u32)bytes[0] | ((u32)bytes[1] << 8)
        | ((u32)bytes[2] << 16) | ((u32)bytes[3] << 24);
}

static void write16(volatile u8 *bytes, u16 value)
{
    bytes[0] = (u8)value;
    bytes[1] = (u8)(value >> 8);
}

static void write32(volatile u8 *bytes, u32 value)
{
    bytes[0] = (u8)value;
    bytes[1] = (u8)(value >> 8);
    bytes[2] = (u8)(value >> 16);
    bytes[3] = (u8)(value >> 24);
}

static u32 crc_byte(u32 crc, u8 value)
{
    u32 bit;
    crc ^= value;
    for (bit = 0u; bit < 8u; ++bit) {
        u32 mask = 0u - (crc & 1u);
        crc = (crc >> 1) ^ (0xEDB88320u & mask);
    }
    return crc;
}

static u32 crc32_bytes(const volatile u8 *bytes, u32 size)
{
    u32 crc = 0xFFFFFFFFu;
    u32 index;
    for (index = 0u; index < size; ++index)
        crc = crc_byte(crc, bytes[index]);
    return crc ^ 0xFFFFFFFFu;
}

static u32 fnv32(const volatile void *data, u32 size)
{
    const volatile u8 *bytes = (const volatile u8 *)data;
    u32 value = 2166136261u;
    u32 index;
    for (index = 0u; index < size; ++index) {
        value ^= bytes[index];
        value *= 16777619u;
    }
    return value;
}

static u32 mix32(u32 value)
{
    value ^= value << 13;
    value ^= value >> 17;
    value ^= value << 5;
    return value != 0u ? value : CODEX_REWARD_OWNER_MAGIC;
}

/* The Vega PC cursor still calls the low-ROM box-level helper that was
 * compiled for the 28-byte pre-DPE species table.  Convert the 80-byte box
 * record to a local party record and let the already-expanded stat path
 * derive its level instead of indexing that stale table. */
CWR_EXPORT(CodexBattleRewards_GetLevelFromBoxMonExpAdapter)
u8 CodexBattleRewards_GetLevelFromBoxMonExpAdapter(const void *box_mon)
{
    Pokemon100 mon;
    clear_bytes(&mon, sizeof(mon));
    copy_bytes(&mon, box_mon, CWR_BOX_MON_SIZE);
    FN_CALCULATE_STATS(&mon);
    return mon.bytes[CWR_PARTY_LEVEL_OFFSET];
}

CWR_EXPORT(CodexBattleRewards_FillSummaryAbility)
void CodexBattleRewards_FillSummaryAbility(void)
{
    volatile u8 *summary = *G_SUMMARY_SCREEN_PTR;
    const volatile u8 *name;
    const volatile u8 *description;
    u16 ability;
    u32 description_address;
    if (summary == 0)
        return;
    ability = FN_GET_MON_ABILITY(
        (const void *)(summary + CWR_SUMMARY_CURRENT_MON_OFFSET));
    if (ability >= CODEX_REWARD_ABILITY_COUNT)
        ability = 0u;
    name = PTR(const volatile u8 *, CODEX_REWARD_ABILITY_NAMES
        + (u32)ability * 17u);
    description_address = read32(PTR(const volatile u8 *,
        CODEX_REWARD_ABILITY_DESCRIPTIONS + (u32)ability * 4u));
    description = PTR(const volatile u8 *, description_address);
    copy_game_string(summary + CWR_SUMMARY_ABILITY_NAME_OFFSET, name,
                     CWR_SUMMARY_ABILITY_NAME_SIZE);
    copy_game_string(summary + CWR_SUMMARY_ABILITY_DESC_OFFSET, description,
                     CWR_SUMMARY_ABILITY_DESC_SIZE);
}

/* This hook is entered by a jump from inside BufferMonSkills, so it must
 * preserve that function's frame and branch to its post-ability block. */
CWR_EXPORT(CodexBattleRewards_SummaryAbilityAdapter)
__attribute__((naked)) void CodexBattleRewards_SummaryAbilityAdapter(void)
{
    __asm__ volatile(
        "bl CodexBattleRewards_FillSummaryAbility\n"
        "ldr r3, =0x08136F1B\n"
        "bx r3\n"
    );
}

/* BufferMonMoveI was partially repointed to the 16-byte canonical name
 * table, but its non-empty destination still used an 8-byte stride while
 * the Japanese summary structure and printer use 9 bytes.  Run the stock
 * field buffering, then rebuild only the five name buffers at the ABI's
 * actual stride. */
CWR_EXPORT(CodexBattleRewards_BufferSummaryMovesAdapter)
void CodexBattleRewards_BufferSummaryMovesAdapter(void)
{
    volatile u8 *summary = *G_SUMMARY_SCREEN_PTR;
    u8 count = 4u;
    u8 index;
    if (summary == 0)
        return;
    for (index = 0u; index < 4u; ++index)
        FN_BUFFER_MON_MOVE(index);
    if (summary[CWR_SUMMARY_MODE_OFFSET] == 2u) {
        FN_BUFFER_MON_MOVE(4u);
        count = 5u;
    }
    for (index = 0u; index < count; ++index) {
        u16 move = read16(summary + CWR_SUMMARY_MOVE_IDS_OFFSET
                          + (u32)index * 2u);
        const volatile u8 *source = move < CODEX_REWARD_MOVE_NAME_COUNT
            ? PTR(const volatile u8 *, CODEX_REWARD_MOVE_NAMES
                + (u32)move * 16u)
            : PTR(const volatile u8 *, CODEX_REWARD_SUMMARY_HYPHEN);
        if (move == 0u)
            source = PTR(const volatile u8 *, CODEX_REWARD_SUMMARY_HYPHEN);
        copy_game_string(summary + CWR_SUMMARY_MOVE_NAMES_OFFSET
                         + (u32)index * CWR_SUMMARY_MOVE_NAME_SIZE,
                         source, CWR_SUMMARY_MOVE_NAME_SIZE);
    }
}

static u32 next_sequence(u32 value)
{
    ++value;
    return value == 0u ? 1u : value;
}

static u32 owner_crc_at(const volatile CodexBattleRewardOwnerV1 *owner)
{
    const volatile u8 *bytes = (const volatile u8 *)owner;
    u32 crc = 0xFFFFFFFFu;
    u32 index;
    for (index = 0u; index < CODEX_REWARD_OWNER_SIZE; ++index) {
        u8 value = (index >= 12u && index < 16u) ? 0u : bytes[index];
        crc = crc_byte(crc, value);
    }
    return crc ^ 0xFFFFFFFFu;
}

static void owner_finalize(void)
{
    volatile CodexBattleRewardOwnerV1 *owner = gCodexBattleRewardOwner;
    owner->magic = CODEX_REWARD_OWNER_MAGIC;
    owner->magic_inverse = ~CODEX_REWARD_OWNER_MAGIC;
    owner->version = CODEX_REWARD_OWNER_VERSION;
    owner->struct_size = CODEX_REWARD_OWNER_SIZE;
    owner->crc32 = 0u;
    owner->crc32 = owner_crc_at(owner);
}

static u8 owner_valid_at(const volatile CodexBattleRewardOwnerV1 *owner)
{
    return (u8)(owner->magic == CODEX_REWARD_OWNER_MAGIC
        && owner->magic_inverse == ~CODEX_REWARD_OWNER_MAGIC
        && owner->version == CODEX_REWARD_OWNER_VERSION
        && owner->struct_size == CODEX_REWARD_OWNER_SIZE
        && owner->crc32 == owner_crc_at(owner)
        && owner->window <= CODEX_REWARD_WINDOW_OPEN
        && owner->journal_phase <= CODEX_REWARD_JOURNAL_COMMITTED);
}

static u8 owner_valid(void)
{
    return owner_valid_at(gCodexBattleRewardOwner);
}

static u8 owner_has_non_erased_bytes_at(
    const volatile CodexBattleRewardOwnerV1 *owner)
{
    const volatile u8 *bytes = (const volatile u8 *)owner;
    u32 index;
    u8 all_zero = 1u;
    u8 all_ff = 1u;
    for (index = 0u; index < CODEX_REWARD_OWNER_SIZE; ++index) {
        if (bytes[index] != 0u)
            all_zero = 0u;
        if (bytes[index] != 0xFFu)
            all_ff = 0u;
    }
    return (u8)(!all_zero && !all_ff);
}

static void owner_initialize_closed(u16 flags)
{
    volatile CodexBattleRewardOwnerV1 *owner = gCodexBattleRewardOwner;
    clear_bytes(owner, sizeof(*owner));
    owner->generation = 1u;
    owner->window = CODEX_REWARD_WINDOW_CLOSED;
    owner->journal_phase = CODEX_REWARD_JOURNAL_NONE;
    owner->flags = flags;
    owner_finalize();
}

static void normalize_owner(void)
{
    if (!owner_valid()) {
        u16 flags = owner_has_non_erased_bytes_at(gCodexBattleRewardOwner)
            ? CWR_OWNER_FLAG_MIGRATED : 0u;
        owner_initialize_closed(flags);
    }
}

static void recover_open_owner(void);

static void finish_durable_owner_restore(void)
{
    volatile CodexBattleRewardOwnerV1 *owner = gCodexBattleRewardOwner;
    const volatile CodexBattleRewardOwnerV1 *candidate =
        PTR(const volatile CodexBattleRewardOwnerV1 *,
            CODEX_REWARD_SAVE_BUFFER_ADDRESS);
    u32 owner_offset = CODEX_REWARD_OWNER_ADDRESS
        - CODEX_REWARD_SECTOR31_IMAGE_ADDRESS;
    volatile u8 *save1;
    /* PC Storage owns broad legacy EWRAM work areas while it is active and
     * clears this cache during teardown.  Never write over that UI.  Once the
     * normal field callback and save/party roots are stable, an invalid cache
     * is safe to replace with the same pending sentinel used after Continue;
     * the authoritative sector-31 owner is then reloaded below. */
    if (owner_valid() && owner->reserved0 == CWR_OWNER_LOAD_CHECKED)
        return;
    if (*G_MAIN_CALLBACK2 != CWR_FIELD_MAIN_CALLBACK)
        return;
    save1 = *G_SAVE_BLOCK1_PTR;
    if ((u32)(uintptr_t)save1 < 0x02000000u
        || (u32)(uintptr_t)save1 >= 0x02040000u
        || (save1[0] == 0u && save1[1] == 0u
            && save1[2] == 0u && save1[3] == 0u)
        || *G_PLAYER_COUNT == 0u || *G_PLAYER_COUNT > CWR_PARTY_SIZE)
        return;
    if (!owner_valid())
        normalize_owner();
    if (owner->reserved0 == CWR_OWNER_LOAD_CHECKED)
        return;
    if (owner->window != CODEX_REWARD_WINDOW_CLOSED
        || owner->journal_phase != CODEX_REWARD_JOURNAL_NONE
        || owner->committed_count != 0u) {
        owner->reserved0 = CWR_OWNER_LOAD_CHECKED;
        owner->reserved[0] = 0u;
        owner_finalize();
        return;
    }
    if (owner->reserved[0] != CWR_OWNER_LOAD_STABLE_FRAMES) {
        ++owner->reserved[0];
        owner_finalize();
        return;
    }
    FN_READ_FLASH(CWR_SAVE_SECTOR, owner_offset,
                  PTR(void *, CODEX_REWARD_SAVE_BUFFER_ADDRESS),
                  CODEX_REWARD_OWNER_SIZE);
    if (owner_valid_at(candidate))
        copy_bytes(owner, candidate, sizeof(*candidate));
    owner->reserved0 = CWR_OWNER_LOAD_CHECKED;
    owner->reserved[0] = 0u;
    owner_finalize();
    recover_open_owner();
}

static u8 test_fault(u32 bit)
{
    if (*G_TEST_CONTROL != CWR_TEST_MAGIC || (*G_TEST_FAULTS & bit) == 0u)
        return 0u;
    *G_TEST_FAULTS &= ~bit;
    return 1u;
}

static u8 persist_sector(u32 fault_bit)
{
    owner_finalize();
    if (test_fault(fault_bit))
        return 0u;
    clear_bytes(G_SAVE_BUFFER, CWR_SAVE_SECTOR_SIZE);
    copy_bytes(G_SAVE_BUFFER, G_SECTOR31_IMAGE, CWR_SAVE_SECTOR_DATA_SIZE);
    return (u8)(FN_TRY_WRITE_SECTOR(CWR_SAVE_SECTOR,
                                    (const void *)G_SAVE_BUFFER) == 1u);
}

static u8 persist_standard(void)
{
    u8 result;
    if (test_fault(CWR_FAULT_STANDARD))
        return 0u;
    /* This entrypoint is VegaQolProduction_OriginalTrySavingData.  The global
     * 0x080DB34D adapter also writes sector 31 and must not be re-entered by a
     * transaction that owns its own PREPARED/STAGED/COMMITTED journal. */
    *G_TRANSACTION_LOCK = CWR_TEST_MAGIC;
    result = (u8)(FN_TRY_SAVING_DATA(0u) == 1u);
    *G_TRANSACTION_LOCK = 0u;
    return result;
}

static u8 t27_state_valid(void)
{
    return (u8)(gCodexBattleRuntimeState->magic == CWR_T27_STATE_MAGIC
        && gCodexBattleRuntimeState->magic_inverse == ~CWR_T27_STATE_MAGIC);
}

static u32 snapshot_crc(void)
{
    volatile CodexBattleRuntimeMailboxV2 *mailbox =
        gCodexBattleRuntimeMailbox;
    const volatile u8 *header = (const volatile u8 *)mailbox;
    const volatile u8 *snapshot =
        (const volatile u8 *)&mailbox->snapshot;
    u32 crc = 0xFFFFFFFFu;
    u32 index;
    for (index = 0u; index < 56u; ++index)
        crc = crc_byte(crc, header[index]);
    for (index = 4u; index < sizeof(mailbox->snapshot); ++index)
        crc = crc_byte(crc, snapshot[index]);
    return crc ^ 0xFFFFFFFFu;
}

static void publish_response(u16 current_status)
{
    volatile CodexBattleRuntimeMailboxV2 *mailbox =
        gCodexBattleRuntimeMailbox;
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    volatile CodexBattleRuntimeSnapshotV2 *snapshot = &mailbox->snapshot;
    u32 sequence = next_sequence(mailbox->snapshot_sequence);
    mailbox->phase = state->phase;
    mailbox->status = current_status;
    mailbox->match_id = state->match_id;
    mailbox->turn = state->turn;
    snapshot->payload_size = sizeof(*snapshot);
    snapshot->current_status = current_status;
    snapshot->rejected_count = state->rejected_count;
    snapshot->turn = state->turn;
    snapshot->phase_echo = state->phase;
    snapshot->last_accepted_sequence = state->last_request_sequence;
    snapshot->crc32 = snapshot_crc();
    barrier();
    mailbox->snapshot_sequence_inverse = ~sequence;
    barrier();
    mailbox->snapshot_sequence = sequence;
}

static void reward_accept(u32 sequence, u16 command)
{
    volatile CodexBattleRuntimeMailboxV2 *mailbox =
        gCodexBattleRuntimeMailbox;
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    state->last_request_sequence = sequence;
    state->last_rejected_sequence = 0u;
    state->last_rejected_request_crc32 = 0u;
    state->current_request_crc32 = 0u;
    state->status = CWR_T27_STATUS_ACCEPTED;
    mailbox->snapshot.response_sequence = sequence;
    mailbox->snapshot.response_sequence_inverse = ~sequence;
    mailbox->snapshot.response_status = CWR_T27_STATUS_ACCEPTED;
    mailbox->snapshot.response_error = CODEX_REWARD_ERROR_NONE;
    mailbox->snapshot.last_command = command;
    mailbox->snapshot.response_payload_size = 0u;
    mailbox->snapshot.last_accepted_sequence = sequence;
    publish_response(CWR_T27_STATUS_ACCEPTED);
}

static void reward_reject(u32 sequence, u16 command, u16 error,
                          u32 request_crc)
{
    volatile CodexBattleRuntimeMailboxV2 *mailbox =
        gCodexBattleRuntimeMailbox;
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    /* Capacity can be freed and save faults can be transient.  Those exact
     * requests must remain retryable with the same sequence/payload. */
    if (error == CODEX_REWARD_ERROR_SAVE_FAILED
        || error == CODEX_REWARD_ERROR_STORAGE_FULL) {
        state->last_rejected_sequence = 0u;
        state->last_rejected_request_crc32 = 0u;
    } else {
        state->last_rejected_sequence = sequence;
        state->last_rejected_request_crc32 = request_crc;
    }
    state->current_request_crc32 = request_crc;
    ++state->rejected_count;
    mailbox->snapshot.response_sequence = sequence;
    mailbox->snapshot.response_sequence_inverse = ~sequence;
    mailbox->snapshot.response_status = CWR_T27_STATUS_ERROR;
    mailbox->snapshot.response_error = error;
    mailbox->snapshot.last_command = command;
    mailbox->snapshot.response_payload_size = 0u;
    publish_response(CWR_T27_STATUS_ERROR);
}

static u32 trainer_id(void)
{
    const volatile u8 *save2 = *G_SAVE_BLOCK2_PTR;
    return save2 == 0 ? 0u : read32(save2 + 0x0Au);
}

static u8 personality_is_shiny(u32 personality, u32 owner)
{
    return (u8)(((u16)owner ^ (u16)(owner >> 16)
        ^ (u16)personality ^ (u16)(personality >> 16)) < 8u);
}

static u32 transaction_personality(u32 transaction, u16 species, u8 shiny,
                                   u8 nature, u32 owner)
{
    u32 value = mix32(transaction ^ ((u32)species << 16)
                      ^ 0x52574431u);
    for (;;) {
        u32 candidate = value;
        if (shiny) {
            u16 high = (u16)(value >> 16);
            u16 low = (u16)owner ^ (u16)(owner >> 16) ^ high
                ^ (u16)(value & 7u);
            candidate = ((u32)high << 16) | low;
        }
        if ((u8)(candidate % 25u) == nature
            && personality_is_shiny(candidate, owner) == shiny)
            return candidate;
        value = mix32(value + 0x9E3779B9u);
    }
}

static u8 type_valid(u8 type)
{
    return (u8)(type <= 17u || type == 23u || type == 24u);
}

static u8 ball_valid(u16 item)
{
    if (item > CODEX_REWARD_ITEM_MAX)
        return 0u;
    return (u8)((gCodexRewardBallItems[item >> 3]
                 >> (item & 7u)) & 1u);
}

/* The request/catalog boundary uses canonical item IDs.  MON_DATA_POKEBALL
 * stores CFRU's ball-type enum; appended item order is deliberately not the
 * enum order (notably Park=16 and Dream=26), so use the generated manifest
 * mapping rather than arithmetic on the item ID. */
static u8 ball_type(u16 item)
{
    return item <= CODEX_REWARD_ITEM_MAX
        ? gCodexRewardBallTypes[item] : 0xFFu;
}

static u16 bag_quantity(u16 item)
{
    u16 low = 0u;
    u16 high = (u16)(CODEX_REWARD_QUANTITY_MAX + 1u);
    while ((u16)(low + 1u) < high) {
        u16 middle = (u16)(low + (u16)(high - low) / 2u);
        if (FN_CHECK_BAG_ITEM(item, middle))
            low = middle;
        else
            high = middle;
    }
    return low;
}

static u8 storage_available(void)
{
    u8 box;
    u8 position;
    if (FN_PARTY_COUNT() < CWR_PARTY_SIZE)
        return 1u;
    for (box = 0u; box < CWR_BOX_COUNT; ++box) {
        for (position = 0u; position < CWR_BOX_CAPACITY; ++position) {
            if (FN_GET_BOX_MON_DATA(box, position,
                                    CWR_MON_DATA_SPECIES) == 0u)
                return 1u;
        }
    }
    return 0u;
}

static void set_ability_slot(Pokemon100 *mon, u8 slot)
{
    u16 met = read16(mon->bytes + CWR_MET_BITS_OFFSET);
    u32 iv = read32(mon->bytes + CWR_IV_BITS_OFFSET);
    met &= (u16)~CWR_HIDDEN_ABILITY_MASK;
    iv &= ~CWR_ABILITY_NUM_MASK;
    if (slot == 1u)
        iv |= CWR_ABILITY_NUM_MASK;
    else if (slot == 2u)
        met |= CWR_HIDDEN_ABILITY_MASK;
    write16(mon->bytes + CWR_MET_BITS_OFFSET, met);
    write32(mon->bytes + CWR_IV_BITS_OFFSET, iv);
}

static u8 owner_mon_valid(const CodexBattleRewardMonV1 *mon)
{
    u16 ev_total = 0u;
    u8 saw_zero = 0u;
    u8 index;
    if (mon->species_id == 0u
        || mon->species_id > CODEX_REWARD_SPECIES_MAX
        || mon->level == 0u || mon->level > CODEX_REWARD_LEVEL_MAX
        || mon->ability_slot > CODEX_REWARD_ABILITY_SLOT_MAX
        || mon->held_item_id > CODEX_REWARD_ITEM_MAX
        || mon->nature_id > CODEX_REWARD_NATURE_MAX
        || mon->shiny > 1u || !type_valid(mon->tera_type)
        || !ball_valid(mon->ball_item_id)
        || mon->presence != 0xFFu)
        return 0u;
    for (index = 0u; index < 4u; ++index) {
        if (mon->moves[index] == 0u)
            saw_zero = 1u;
        else if (mon->moves[index] > CODEX_REWARD_MOVE_MAX || saw_zero)
            return 0u;
    }
    if (mon->moves[0] == 0u)
        return 0u;
    for (index = 0u; index < 6u; ++index) {
        if (mon->ivs[index] > CODEX_REWARD_IV_MAX
            || mon->evs[index] > CODEX_REWARD_EV_MAX)
            return 0u;
        ev_total = (u16)(ev_total + mon->evs[index]);
    }
    return (u8)(ev_total <= CODEX_REWARD_EV_TOTAL_MAX);
}

static void copy_mon_to_owner(const CodexBattleRewardMonV1 *mon)
{
    volatile CodexBattleRewardOwnerV1 *owner = gCodexBattleRewardOwner;
    u8 index;
    owner->species_id = mon->species_id;
    owner->level = mon->level;
    owner->ability_slot = mon->ability_slot;
    owner->held_item_id = mon->held_item_id;
    for (index = 0u; index < 4u; ++index)
        owner->moves[index] = mon->moves[index];
    owner->nature_id = mon->nature_id;
    for (index = 0u; index < 6u; ++index) {
        owner->ivs[index] = mon->ivs[index];
        owner->evs[index] = mon->evs[index];
    }
    owner->shiny = mon->shiny;
    owner->tera_type = mon->tera_type;
    owner->presence = mon->presence;
    owner->ball_item_id = mon->ball_item_id;
}

static u8 create_owner_mon(void)
{
    volatile CodexBattleRewardOwnerV1 *owner = gCodexBattleRewardOwner;
    Pokemon100 *mon = G_TRANSACTION_SCRATCH;
    u32 value;
    u8 index;
    clear_bytes(mon, sizeof(*mon));
    FN_CREATE_MON(mon, owner->species_id, owner->level, 31u, 1u,
                  owner->personality, 0u, 0u);
    /* The stock PC renderer consumes MON_DATA_SPECIES2, which also requires
     * the normal has-species sanity bit.  CreateMon owns this bit, but set it
     * explicitly so a reward can never commit as raw storage that the PC UI
     * treats as empty. */
    value = 1u;
    FN_SET_MON_DATA(mon, CWR_MON_DATA_SANITY_HAS_SPECIES, &value);
    value = owner->held_item_id;
    FN_SET_MON_DATA(mon, CWR_MON_DATA_HELD_ITEM, &value);
    value = 0u;
    FN_SET_MON_DATA(mon, CWR_MON_DATA_PP_BONUSES, &value);
    for (index = 0u; index < 4u; ++index) {
        value = owner->moves[index];
        FN_SET_MON_DATA(mon, CWR_MON_DATA_MOVE1 + index, &value);
        value = owner->moves[index] == 0u ? 0u
            : FN_CALCULATE_PP(owner->moves[index], 0u, index);
        FN_SET_MON_DATA(mon, CWR_MON_DATA_PP1 + index, &value);
    }
    for (index = 0u; index < 6u; ++index) {
        value = owner->evs[index];
        FN_SET_MON_DATA(mon, CWR_MON_DATA_EV_HP + index, &value);
        value = owner->ivs[index];
        FN_SET_MON_DATA(mon, CWR_MON_DATA_IV_HP + index, &value);
    }
    value = ball_type(owner->ball_item_id);
    FN_SET_MON_DATA(mon, CWR_MON_DATA_POKEBALL, &value);
    mon->bytes[CWR_NATURE_MINT_OFFSET] = (u8)(owner->nature_id + 1u);
    mon->bytes[CWR_TERA_TYPE_OFFSET] = owner->tera_type;
    set_ability_slot(mon, owner->ability_slot);
    FN_CALCULATE_STATS(mon);
    write16(mon->bytes + CWR_HP_OFFSET,
            read16(mon->bytes + CWR_MAX_HP_OFFSET));
    return (u8)(FN_GET_MON_DATA(mon, CWR_MON_DATA_SPECIES, 0)
                    == owner->species_id
        && FN_GET_MON_DATA(mon, CWR_MON_DATA_SPECIES2, 0)
                    == owner->species_id
        && FN_GET_MON_DATA(mon, CWR_MON_DATA_PERSONALITY, 0)
                    == owner->personality
        && FN_GET_MON_DATA(mon, CWR_MON_DATA_OT_ID, 0) == owner->ot_id
        && (u8)(owner->personality % 25u) == owner->nature_id
        && personality_is_shiny(owner->personality, owner->ot_id)
                    == owner->shiny
        && FN_GET_MON_DATA(mon, CWR_MON_DATA_POKEBALL, 0)
                    == ball_type(owner->ball_item_id));
}

static u8 token_mon_values(u32 token, u16 *species, u32 *personality,
                           u32 *ot_id, u16 *ball)
{
    u32 kind = token & CWR_TOKEN_KIND_MASK;
    if (kind == CWR_TOKEN_PARTY) {
        u8 slot = (u8)token;
        Pokemon100 *mon;
        if (slot >= CWR_PARTY_SIZE)
            return 0u;
        mon = &G_PLAYER_PARTY[slot];
        *species = (u16)FN_GET_MON_DATA(mon, CWR_MON_DATA_SPECIES2, 0);
        *personality = FN_GET_MON_DATA(mon, CWR_MON_DATA_PERSONALITY, 0);
        *ot_id = FN_GET_MON_DATA(mon, CWR_MON_DATA_OT_ID, 0);
        *ball = (u16)FN_GET_MON_DATA(mon, CWR_MON_DATA_POKEBALL, 0);
        return 1u;
    }
    if (kind == CWR_TOKEN_BOX) {
        u8 box = (u8)(token >> 8);
        u8 position = (u8)token;
        if (box >= CWR_BOX_COUNT || position >= CWR_BOX_CAPACITY)
            return 0u;
        *species = (u16)FN_GET_BOX_MON_DATA(
            box, position, CWR_MON_DATA_SPECIES2);
        *personality = FN_GET_BOX_MON_DATA(
            box, position, CWR_MON_DATA_PERSONALITY);
        *ot_id = FN_GET_BOX_MON_DATA(box, position, CWR_MON_DATA_OT_ID);
        *ball = (u16)FN_GET_BOX_MON_DATA(
            box, position, CWR_MON_DATA_POKEBALL);
        return 1u;
    }
    return 0u;
}

static u8 token_matches_owner(u32 token)
{
    volatile CodexBattleRewardOwnerV1 *owner = gCodexBattleRewardOwner;
    u16 species;
    u16 ball;
    u32 personality;
    u32 ot_id;
    return (u8)(token_mon_values(token, &species, &personality, &ot_id, &ball)
        && species == owner->species_id
        && personality == owner->personality
        && ot_id == owner->ot_id
        && ball == ball_type(owner->ball_item_id));
}

static u8 token_empty(u32 token)
{
    u16 species;
    u16 ball;
    u32 personality;
    u32 ot_id;
    return (u8)(token_mon_values(token, &species, &personality, &ot_id, &ball)
                && species == 0u);
}

static void rollback_destination(u32 token)
{
    u32 kind = token & CWR_TOKEN_KIND_MASK;
    if (kind == CWR_TOKEN_PARTY) {
        u8 slot = (u8)token;
        if (slot < CWR_PARTY_SIZE) {
            clear_bytes(&G_PLAYER_PARTY[slot], CWR_MON_SIZE);
            *G_PLAYER_COUNT = FN_PARTY_COUNT();
        }
    } else if (kind == CWR_TOKEN_BOX) {
        u8 box = (u8)(token >> 8);
        u8 position = (u8)token;
        if (box < CWR_BOX_COUNT && position < CWR_BOX_CAPACITY)
            FN_ZERO_BOX_MON_AT(box, position);
    }
}

static u8 deliver_owner_mon(void)
{
    volatile CodexBattleRewardOwnerV1 *owner = gCodexBattleRewardOwner;
    u8 party_before = FN_PARTY_COUNT();
    u16 previous_box = 0u;
    u8 outcome;
    if (!storage_available() || !create_owner_mon())
        return 0u;
    if (party_before >= CWR_PARTY_SIZE) {
        previous_box = FN_VAR_GET(CWR_PC_BOX_VAR);
        (void)FN_VAR_SET(CWR_PC_BOX_VAR, 0u);
    }
    outcome = FN_GIVE_MON(G_TRANSACTION_SCRATCH);
    if (party_before >= CWR_PARTY_SIZE)
        (void)FN_VAR_SET(CWR_PC_BOX_VAR, previous_box);
    if (outcome == 0u && party_before < CWR_PARTY_SIZE) {
        owner->destination_token = CWR_TOKEN_PARTY | party_before;
        owner->destination_kind = CWR_DESTINATION_PARTY;
        owner->destination_box = 0u;
        owner->destination_slot = party_before;
    } else if (outcome == 1u
               && *G_SPECIAL_MON_BOX_ID < CWR_BOX_COUNT
               && *G_SPECIAL_MON_BOX_POS < CWR_BOX_CAPACITY) {
        owner->destination_token = CWR_TOKEN_BOX
            | ((u32)*G_SPECIAL_MON_BOX_ID << 8)
            | (u32)*G_SPECIAL_MON_BOX_POS;
        owner->destination_kind = CWR_DESTINATION_BOX;
        owner->destination_box = (u8)*G_SPECIAL_MON_BOX_ID;
        owner->destination_slot = (u8)*G_SPECIAL_MON_BOX_POS;
    } else {
        owner->destination_token = 0u;
        return 0u;
    }
    if (!token_matches_owner(owner->destination_token)) {
        rollback_destination(owner->destination_token);
        owner->destination_token = 0u;
        return 0u;
    }
    owner->delivery_fingerprint = fnv32(G_TRANSACTION_SCRATCH,
                                        sizeof(*G_TRANSACTION_SCRATCH));
    return 1u;
}

static void clear_transaction_payload(void)
{
    volatile CodexBattleRewardOwnerV1 *owner = gCodexBattleRewardOwner;
    owner->destination_token = 0u;
    owner->personality = 0u;
    owner->ot_id = 0u;
    owner->item_id = 0u;
    owner->quantity = 0u;
    owner->bag_quantity_before = 0u;
    owner->species_id = 0u;
    owner->held_item_id = 0u;
    owner->ball_item_id = 0u;
    clear_bytes(owner->moves, sizeof(owner->moves));
    owner->level = 0u;
    owner->ability_slot = 0u;
    owner->nature_id = 0u;
    owner->presence = 0u;
    clear_bytes(owner->ivs, sizeof(owner->ivs));
    clear_bytes(owner->evs, sizeof(owner->evs));
    owner->shiny = 0u;
    owner->tera_type = 0u;
    owner->destination_kind = CWR_DESTINATION_NONE;
    owner->destination_box = 0u;
    owner->destination_slot = 0u;
    owner->delivery_fingerprint = 0u;
}

static void prepare_common(u32 sequence, u16 command, u32 payload_hash)
{
    volatile CodexBattleRewardOwnerV1 *owner = gCodexBattleRewardOwner;
    clear_transaction_payload();
#if CODEX_WINDOWS_CATALOG_ENABLED
    if (command == CODEX_CATALOG_COMMAND_ITEM
        || command == CODEX_CATALOG_COMMAND_MON)
        owner->flags |= CWR_OWNER_FLAG_CATALOG;
    else
        owner->flags &= (u16)~CWR_OWNER_FLAG_CATALOG;
#endif
    owner->pending_sequence = sequence;
    owner->pending_payload_hash = payload_hash;
    owner->transaction_id = mix32(owner->session_nonce ^ owner->match_id
                                  ^ sequence ^ payload_hash
                                  ^ ((u32)command << 24));
    owner->journal_phase = CODEX_REWARD_JOURNAL_PREPARED;
    owner->last_result = CODEX_REWARD_ERROR_NONE;
    ++owner->generation;
}

static void cancel_pending(u16 result)
{
    volatile CodexBattleRewardOwnerV1 *owner = gCodexBattleRewardOwner;
    owner->pending_sequence = 0u;
    owner->pending_payload_hash = 0u;
    owner->journal_phase = CODEX_REWARD_JOURNAL_NONE;
    owner->last_result = result;
    ++owner->error_count;
    ++owner->generation;
    owner_finalize();
}

static void commit_pending(u16 command, u32 sequence, u32 payload_hash)
{
    volatile CodexBattleRewardOwnerV1 *owner = gCodexBattleRewardOwner;
    owner->journal_phase = CODEX_REWARD_JOURNAL_COMMITTED;
    owner->last_command = (u8)command;
    owner->last_request_sequence = sequence;
    owner->last_payload_hash = payload_hash;
    owner->pending_sequence = 0u;
    owner->pending_payload_hash = 0u;
    owner->last_result = CODEX_REWARD_ERROR_NONE;
    ++owner->committed_count;
    ++owner->generation;
    owner_finalize();
}

static u8 persist_commit_or_restore_staged(u16 command, u32 sequence,
                                            u32 payload_hash)
{
    CodexBattleRewardOwnerV1 staged;
    copy_bytes(&staged, gCodexBattleRewardOwner, sizeof(staged));
    commit_pending(command, sequence, payload_hash);
    if (persist_sector(CWR_FAULT_COMMIT))
        return 1u;
    copy_bytes(gCodexBattleRewardOwner, &staged, sizeof(staged));
    owner_finalize();
    return 0u;
}

static u16 resume_item(u16 command, u32 sequence, u32 payload_hash)
{
    volatile CodexBattleRewardOwnerV1 *owner = gCodexBattleRewardOwner;
    u16 current = bag_quantity(owner->item_id);
    u16 target = (u16)(owner->bag_quantity_before + owner->quantity);
    if (target > CODEX_REWARD_QUANTITY_MAX)
        return CODEX_REWARD_ERROR_STORAGE_FULL;
    if (owner->journal_phase == CODEX_REWARD_JOURNAL_PREPARED) {
        if (current != owner->bag_quantity_before)
            return CODEX_REWARD_ERROR_TRANSACTION_CONFLICT;
        if (!FN_ADD_BAG_ITEM(owner->item_id, owner->quantity))
            return CODEX_REWARD_ERROR_STORAGE_FULL;
        current = bag_quantity(owner->item_id);
        if (current != target) {
            (void)FN_REMOVE_BAG_ITEM(owner->item_id, owner->quantity);
            return CODEX_REWARD_ERROR_TRANSACTION_CONFLICT;
        }
        owner->destination_token = target;
        owner->delivery_fingerprint = mix32(
            ((u32)owner->item_id << 16) | target);
        owner->journal_phase = CODEX_REWARD_JOURNAL_STAGED;
        ++owner->generation;
        if (!persist_sector(CWR_FAULT_STAGED)) {
            (void)FN_REMOVE_BAG_ITEM(owner->item_id, owner->quantity);
            cancel_pending(CODEX_REWARD_ERROR_SAVE_FAILED);
            (void)persist_sector(0u);
            return CODEX_REWARD_ERROR_SAVE_FAILED;
        }
    } else if (owner->journal_phase == CODEX_REWARD_JOURNAL_STAGED) {
        if (current == owner->bag_quantity_before) {
            if (!FN_ADD_BAG_ITEM(owner->item_id, owner->quantity)
                || bag_quantity(owner->item_id) != target)
                return CODEX_REWARD_ERROR_STORAGE_FULL;
        } else if (current != target) {
            return CODEX_REWARD_ERROR_TRANSACTION_CONFLICT;
        }
    } else {
        return CODEX_REWARD_ERROR_TRANSACTION_CONFLICT;
    }
    if (!persist_standard())
        return CODEX_REWARD_ERROR_SAVE_FAILED;
    if (!persist_commit_or_restore_staged(command, sequence, payload_hash))
        return CODEX_REWARD_ERROR_SAVE_FAILED;
    return CODEX_REWARD_ERROR_NONE;
}

static u16 resume_mon(u16 command, u32 sequence, u32 payload_hash)
{
    volatile CodexBattleRewardOwnerV1 *owner = gCodexBattleRewardOwner;
    if (owner->journal_phase == CODEX_REWARD_JOURNAL_PREPARED) {
        if (!deliver_owner_mon())
            return storage_available() ? CODEX_REWARD_ERROR_INVALID_MON
                                       : CODEX_REWARD_ERROR_STORAGE_FULL;
        owner->journal_phase = CODEX_REWARD_JOURNAL_STAGED;
        ++owner->generation;
        if (!persist_sector(CWR_FAULT_STAGED)) {
            rollback_destination(owner->destination_token);
            cancel_pending(CODEX_REWARD_ERROR_SAVE_FAILED);
            (void)persist_sector(0u);
            return CODEX_REWARD_ERROR_SAVE_FAILED;
        }
    } else if (owner->journal_phase == CODEX_REWARD_JOURNAL_STAGED) {
        if (!token_matches_owner(owner->destination_token)) {
            if (!token_empty(owner->destination_token))
                return CODEX_REWARD_ERROR_TRANSACTION_CONFLICT;
            if (!deliver_owner_mon())
                return storage_available() ? CODEX_REWARD_ERROR_INVALID_MON
                                           : CODEX_REWARD_ERROR_STORAGE_FULL;
            ++owner->generation;
            if (!persist_sector(CWR_FAULT_STAGED))
                return CODEX_REWARD_ERROR_SAVE_FAILED;
        }
    } else {
        return CODEX_REWARD_ERROR_TRANSACTION_CONFLICT;
    }
    if (!persist_standard())
        return CODEX_REWARD_ERROR_SAVE_FAILED;
    if (!persist_commit_or_restore_staged(command, sequence, payload_hash))
        return CODEX_REWARD_ERROR_SAVE_FAILED;
    return CODEX_REWARD_ERROR_NONE;
}

static u16 resume_simple(u16 command, u32 sequence, u32 payload_hash)
{
    volatile CodexBattleRewardOwnerV1 *owner = gCodexBattleRewardOwner;
    if (owner->journal_phase != CODEX_REWARD_JOURNAL_PREPARED)
        return CODEX_REWARD_ERROR_TRANSACTION_CONFLICT;
    if (command == CODEX_REWARD_COMMAND_CLOSE)
        owner->window = CODEX_REWARD_WINDOW_CLOSED;
    if (!persist_commit_or_restore_staged(command, sequence, payload_hash))
        return CODEX_REWARD_ERROR_SAVE_FAILED;
    return CODEX_REWARD_ERROR_NONE;
}

static u16 start_or_resume_transaction(u16 command, u32 sequence,
                                       u32 payload_hash,
                                       const volatile u8 *payload, u16 size)
{
    volatile CodexBattleRewardOwnerV1 *owner = gCodexBattleRewardOwner;
    if (owner->pending_sequence != 0u) {
        if (owner->pending_sequence != sequence
            || owner->pending_payload_hash != payload_hash)
            return CODEX_REWARD_ERROR_BUSY;
#if CODEX_WINDOWS_CATALOG_ENABLED
        if (command == CODEX_REWARD_COMMAND_ITEM
            || command == CODEX_CATALOG_COMMAND_ITEM)
#else
        if (command == CODEX_REWARD_COMMAND_ITEM)
#endif
            return resume_item(command, sequence, payload_hash);
#if CODEX_WINDOWS_CATALOG_ENABLED
        if (command == CODEX_REWARD_COMMAND_MON
            || command == CODEX_CATALOG_COMMAND_MON)
#else
        if (command == CODEX_REWARD_COMMAND_MON)
#endif
            return resume_mon(command, sequence, payload_hash);
        return resume_simple(command, sequence, payload_hash);
    }
    if (command == CODEX_REWARD_COMMAND_STATUS) {
        if (size != 0u)
            return CODEX_REWARD_ERROR_PAYLOAD_FORMAT;
        prepare_common(sequence, command, payload_hash);
        if (!persist_sector(CWR_FAULT_PREPARE)) {
            cancel_pending(CODEX_REWARD_ERROR_SAVE_FAILED);
            return CODEX_REWARD_ERROR_SAVE_FAILED;
        }
        if (test_fault(CWR_FAULT_AFTER_PREPARE))
            return CODEX_REWARD_ERROR_SAVE_FAILED;
        return resume_simple(command, sequence, payload_hash);
    }
    if (command == CODEX_REWARD_COMMAND_CLOSE) {
        if (size != 0u)
            return CODEX_REWARD_ERROR_PAYLOAD_FORMAT;
        prepare_common(sequence, command, payload_hash);
        if (!persist_sector(CWR_FAULT_CLOSE)) {
            cancel_pending(CODEX_REWARD_ERROR_SAVE_FAILED);
            return CODEX_REWARD_ERROR_SAVE_FAILED;
        }
        if (test_fault(CWR_FAULT_AFTER_PREPARE))
            return CODEX_REWARD_ERROR_SAVE_FAILED;
        return resume_simple(command, sequence, payload_hash);
    }
#if CODEX_WINDOWS_CATALOG_ENABLED
    if (command == CODEX_REWARD_COMMAND_ITEM
        || command == CODEX_CATALOG_COMMAND_ITEM) {
#else
    if (command == CODEX_REWARD_COMMAND_ITEM) {
#endif
        u16 item;
        u16 quantity;
        if (size != 4u)
            return CODEX_REWARD_ERROR_PAYLOAD_FORMAT;
        item = read16(payload);
        quantity = read16(payload + 2u);
        if (item == 0u || item > CODEX_REWARD_ITEM_MAX
            || quantity == 0u || quantity > CODEX_REWARD_QUANTITY_MAX)
            return CODEX_REWARD_ERROR_INVALID_ITEM;
        prepare_common(sequence, command, payload_hash);
        owner->item_id = item;
        owner->quantity = quantity;
        owner->bag_quantity_before = bag_quantity(item);
        if ((u32)owner->bag_quantity_before + quantity
                > CODEX_REWARD_QUANTITY_MAX) {
            cancel_pending(CODEX_REWARD_ERROR_STORAGE_FULL);
            return CODEX_REWARD_ERROR_STORAGE_FULL;
        }
        if (!persist_sector(CWR_FAULT_PREPARE)) {
            cancel_pending(CODEX_REWARD_ERROR_SAVE_FAILED);
            return CODEX_REWARD_ERROR_SAVE_FAILED;
        }
        if (test_fault(CWR_FAULT_AFTER_PREPARE))
            return CODEX_REWARD_ERROR_SAVE_FAILED;
        return resume_item(command, sequence, payload_hash);
    }
#if CODEX_WINDOWS_CATALOG_ENABLED
    if (command == CODEX_REWARD_COMMAND_MON
        || command == CODEX_CATALOG_COMMAND_MON) {
#else
    if (command == CODEX_REWARD_COMMAND_MON) {
#endif
        CodexBattleRewardMonV1 mon;
        if (size != sizeof(mon))
            return CODEX_REWARD_ERROR_PAYLOAD_FORMAT;
        copy_bytes(&mon, payload, sizeof(mon));
        if (!owner_mon_valid(&mon))
            return (mon.ball_item_id != 0u
                    && !ball_valid(mon.ball_item_id))
                ? CODEX_REWARD_ERROR_INVALID_ITEM
                : CODEX_REWARD_ERROR_INVALID_MON;
        if (!storage_available())
            return CODEX_REWARD_ERROR_STORAGE_FULL;
        prepare_common(sequence, command, payload_hash);
        copy_mon_to_owner(&mon);
        owner->ot_id = trainer_id();
        owner->personality = transaction_personality(
            owner->transaction_id, owner->species_id, owner->shiny,
            owner->nature_id, owner->ot_id);
        if (!persist_sector(CWR_FAULT_PREPARE)) {
            cancel_pending(CODEX_REWARD_ERROR_SAVE_FAILED);
            return CODEX_REWARD_ERROR_SAVE_FAILED;
        }
        if (test_fault(CWR_FAULT_AFTER_PREPARE))
            return CODEX_REWARD_ERROR_SAVE_FAILED;
        return resume_mon(command, sequence, payload_hash);
    }
    return CODEX_REWARD_ERROR_UNKNOWN_COMMAND;
}

#if CODEX_WINDOWS_CATALOG_ENABLED
static u8 catalog_command(u16 command)
{
    return (u8)(command == CODEX_CATALOG_COMMAND_ITEM
                || command == CODEX_CATALOG_COMMAND_MON);
}

static u8 private_field_context_valid(
    const volatile CodexBattleRuntimeState *state)
{
    const volatile u8 *save1 = *G_SAVE_BLOCK1_PTR;
    u32 address = (u32)(uintptr_t)save1;
    return (u8)(state->phase == CWR_T27_PHASE_IDLE
        && state->active == 0u
        && *G_MAIN_CALLBACK2 == CWR_FIELD_MAIN_CALLBACK
        && FN_SCRIPT_CONTEXT2_ENABLED() == 0u
        && address >= 0x02000000u && address < 0x02040000u
#if !CODEX_WINDOWS_BOX14_VAULT_ENABLED
        && save1[4] == CODEX_CATALOG_MAP_GROUP
        && save1[5] == CODEX_CATALOG_MAP_NUMBER
#endif
        );
}

#if CODEX_WINDOWS_BOX14_VAULT_ENABLED
static u8 vault_command(u16 command)
{
    return (u8)(command >= CODEX_VAULT_COMMAND_SCAN
                && command <= CODEX_VAULT_COMMAND_IMPORT);
}

static u32 vault_occupancy_mask(void)
{
    u32 mask = 0u;
    u8 slot;
    for (slot = 0u; slot < WINDOWS_BOX14_VAULT_SLOT_COUNT; ++slot) {
        if (FN_GET_BOX_MON_DATA(WINDOWS_BOX14_VAULT_BOX_INDEX, slot,
                                CWR_MON_DATA_SPECIES) != 0u)
            mask |= (u32)1u << slot;
    }
    return mask;
}

static u8 vault_slot_has_mail(u8 slot)
{
    u16 item = (u16)FN_GET_BOX_MON_DATA(
        WINDOWS_BOX14_VAULT_BOX_INDEX, slot, CWR_MON_DATA_HELD_ITEM);
    return item != 0u ? FN_IS_MAIL(item) : 0u;
}

static u8 vault_mask_has_mail(u32 mask)
{
    u8 slot;
    for (slot = 0u; slot < WINDOWS_BOX14_VAULT_SLOT_COUNT; ++slot) {
        if ((mask & ((u32)1u << slot)) != 0u && vault_slot_has_mail(slot))
            return 1u;
    }
    return 0u;
}

static u32 vault_transfer_crc(const WindowsBox14VaultTransferV1 *transfer)
{
    return crc32_bytes((const volatile u8 *)transfer,
                       offsetof(WindowsBox14VaultTransferV1, block_crc32));
}

static u8 vault_read_input(WindowsBox14VaultTransferV1 *out,
                           u32 expected_generation, u8 expected_slot,
                           u32 expected_record_crc, u32 session_nonce)
{
    const volatile WindowsBox14VaultTransferV1 *shared =
        gWindowsBox14VaultTransfer;
    u32 generation = shared->generation;
    u32 inverse = shared->generation_inverse;
    if (generation == 0u || inverse != ~generation)
        return 0u;
    copy_bytes(out, shared, sizeof(*out));
    barrier();
    if (shared->generation != generation
        || shared->generation_inverse != inverse)
        return 0u;
    return (u8)(generation == expected_generation
        && out->magic == WINDOWS_BOX14_VAULT_MAGIC
        && out->magic_inverse == ~WINDOWS_BOX14_VAULT_MAGIC
        && out->version == WINDOWS_BOX14_VAULT_VERSION
        && out->struct_size == WINDOWS_BOX14_VAULT_TRANSFER_SIZE
        && out->generation_inverse == ~out->generation
        && out->command == CODEX_VAULT_COMMAND_IMPORT
        && out->status == WINDOWS_BOX14_VAULT_TRANSFER_INPUT
        && out->box == WINDOWS_BOX14_VAULT_BOX_INDEX
        && out->slot == expected_slot
        && out->record_size == WINDOWS_BOX14_VAULT_RECORD_SIZE
        && out->record_crc32 == expected_record_crc
        && out->abi_crc32 == CODEX_VAULT_ABI_CRC32
        && out->session_nonce == session_nonce
        && out->record_crc32 == crc32_bytes(
            out->record, WINDOWS_BOX14_VAULT_RECORD_SIZE)
        && out->block_crc32 == vault_transfer_crc(out));
}

static void vault_publish(u16 command, u8 slot, const volatile u8 *record,
                          u32 occupancy_mask, u32 session_nonce)
{
    volatile WindowsBox14VaultTransferV1 *shared =
        gWindowsBox14VaultTransfer;
    WindowsBox14VaultTransferV1 image;
    u32 generation = shared->generation;
    if (generation == 0u || shared->generation_inverse != ~generation)
        generation = 0u;
    generation = next_sequence(generation);
    clear_bytes(&image, sizeof(image));
    image.magic = WINDOWS_BOX14_VAULT_MAGIC;
    image.magic_inverse = ~WINDOWS_BOX14_VAULT_MAGIC;
    image.version = WINDOWS_BOX14_VAULT_VERSION;
    image.struct_size = WINDOWS_BOX14_VAULT_TRANSFER_SIZE;
    image.generation = generation;
    image.generation_inverse = ~generation;
    image.command = command;
    image.status = WINDOWS_BOX14_VAULT_TRANSFER_OUTPUT;
    image.box = WINDOWS_BOX14_VAULT_BOX_INDEX;
    image.slot = slot;
    image.occupancy_mask = occupancy_mask;
    image.abi_crc32 = CODEX_VAULT_ABI_CRC32;
    image.session_nonce = session_nonce;
    if (record != (const volatile u8 *)0) {
        image.record_size = WINDOWS_BOX14_VAULT_RECORD_SIZE;
        copy_bytes(image.record, record, WINDOWS_BOX14_VAULT_RECORD_SIZE);
        image.record_crc32 = crc32_bytes(
            image.record, WINDOWS_BOX14_VAULT_RECORD_SIZE);
    }
    image.block_crc32 = vault_transfer_crc(&image);
    shared->generation = 0u;
    barrier();
    copy_bytes(shared, &image,
               offsetof(WindowsBox14VaultTransferV1, generation));
    copy_bytes((volatile u8 *)shared
                   + offsetof(WindowsBox14VaultTransferV1, command),
               (const volatile u8 *)&image
                   + offsetof(WindowsBox14VaultTransferV1, command),
               sizeof(image)
                   - offsetof(WindowsBox14VaultTransferV1, command));
    shared->generation_inverse = ~generation;
    barrier();
    shared->generation = generation;
}

static void vault_commit_volatile(u16 command, u32 sequence,
                                  u32 payload_hash)
{
    volatile CodexBattleRewardOwnerV1 *owner = gCodexBattleRewardOwner;
    owner->flags &= (u16)~CWR_OWNER_FLAG_CATALOG;
    owner->flags |= CWR_OWNER_FLAG_VAULT;
    owner->journal_phase = CODEX_REWARD_JOURNAL_COMMITTED;
    owner->last_command = (u8)command;
    owner->last_request_sequence = sequence;
    owner->last_payload_hash = payload_hash;
    owner->pending_sequence = 0u;
    owner->pending_payload_hash = 0u;
    owner->last_result = CODEX_REWARD_ERROR_NONE;
    ++owner->committed_count;
    ++owner->generation;
    owner_finalize();
}

static u16 vault_execute(u16 command, u32 sequence, u32 payload_hash,
                         const volatile u8 *payload, u16 size,
                         u32 session_nonce)
{
    u32 occupancy = vault_occupancy_mask();
    u8 slot = 0xFFu;
    if (command == CODEX_VAULT_COMMAND_SCAN) {
        if (size != 0u)
            return CODEX_REWARD_ERROR_PAYLOAD_FORMAT;
        if (vault_mask_has_mail(occupancy))
            return CODEX_REWARD_ERROR_VAULT_MAIL;
        vault_publish(command, slot, (const volatile u8 *)0,
                      occupancy, session_nonce);
    } else if (command == CODEX_VAULT_COMMAND_EXPORT) {
        const volatile u8 *record;
        if (size != 1u || payload[0] >= WINDOWS_BOX14_VAULT_SLOT_COUNT)
            return CODEX_REWARD_ERROR_PAYLOAD_FORMAT;
        slot = payload[0];
        if ((occupancy & ((u32)1u << slot)) == 0u)
            return CODEX_REWARD_ERROR_VAULT_EMPTY;
        if (vault_slot_has_mail(slot))
            return CODEX_REWARD_ERROR_VAULT_MAIL;
        record = (const volatile u8 *)FN_GET_BOXED_MON(
            WINDOWS_BOX14_VAULT_BOX_INDEX, slot);
        if (record == (const volatile u8 *)0)
            return CODEX_REWARD_ERROR_VAULT_CHANGED;
        vault_publish(command, slot, record, occupancy, session_nonce);
    } else if (command == CODEX_VAULT_COMMAND_REMOVE) {
        u8 backup[WINDOWS_BOX14_VAULT_RECORD_SIZE];
        const volatile u8 *record;
        u32 expected_crc;
        if (size != 5u || payload[0] >= WINDOWS_BOX14_VAULT_SLOT_COUNT)
            return CODEX_REWARD_ERROR_PAYLOAD_FORMAT;
        slot = payload[0];
        expected_crc = read32(payload + 1u);
        if ((occupancy & ((u32)1u << slot)) == 0u)
            return CODEX_REWARD_ERROR_VAULT_EMPTY;
        if (vault_slot_has_mail(slot))
            return CODEX_REWARD_ERROR_VAULT_MAIL;
        record = (const volatile u8 *)FN_GET_BOXED_MON(
            WINDOWS_BOX14_VAULT_BOX_INDEX, slot);
        if (record == (const volatile u8 *)0
            || crc32_bytes(record, WINDOWS_BOX14_VAULT_RECORD_SIZE)
                != expected_crc)
            return CODEX_REWARD_ERROR_VAULT_CHANGED;
        copy_bytes(backup, record, sizeof(backup));
        FN_ZERO_BOX_MON_AT(WINDOWS_BOX14_VAULT_BOX_INDEX, slot);
        if (!persist_standard()) {
            FN_SET_BOX_MON_AT(WINDOWS_BOX14_VAULT_BOX_INDEX, slot, backup);
            return CODEX_REWARD_ERROR_SAVE_FAILED;
        }
        occupancy = vault_occupancy_mask();
        vault_publish(command, slot, backup, occupancy, session_nonce);
    } else if (command == CODEX_VAULT_COMMAND_IMPORT) {
        WindowsBox14VaultTransferV1 input;
        u32 generation;
        u32 expected_crc;
        u16 species;
        u16 item;
        if (size != 9u || payload[0] >= WINDOWS_BOX14_VAULT_SLOT_COUNT)
            return CODEX_REWARD_ERROR_PAYLOAD_FORMAT;
        slot = payload[0];
        generation = read32(payload + 1u);
        expected_crc = read32(payload + 5u);
        if ((occupancy & ((u32)1u << slot)) != 0u)
            return CODEX_REWARD_ERROR_VAULT_SLOT_OCCUPIED;
        if (!vault_read_input(&input, generation, slot, expected_crc,
                              session_nonce))
            return CODEX_REWARD_ERROR_VAULT_ABI;
        species = (u16)FN_GET_MON_DATA(
            input.record, CWR_MON_DATA_SPECIES, (u8 *)0);
        item = (u16)FN_GET_MON_DATA(
            input.record, CWR_MON_DATA_HELD_ITEM, (u8 *)0);
        if (species == 0u || species > CODEX_REWARD_SPECIES_MAX)
            return CODEX_REWARD_ERROR_INVALID_MON;
        if (item != 0u && FN_IS_MAIL(item))
            return CODEX_REWARD_ERROR_VAULT_MAIL;
        FN_SET_BOX_MON_AT(WINDOWS_BOX14_VAULT_BOX_INDEX, slot,
                          input.record);
        if (crc32_bytes((const volatile u8 *)FN_GET_BOXED_MON(
                            WINDOWS_BOX14_VAULT_BOX_INDEX, slot),
                        WINDOWS_BOX14_VAULT_RECORD_SIZE) != expected_crc
            || FN_GET_BOX_MON_DATA(WINDOWS_BOX14_VAULT_BOX_INDEX, slot,
                                   CWR_MON_DATA_SPECIES) != species) {
            FN_ZERO_BOX_MON_AT(WINDOWS_BOX14_VAULT_BOX_INDEX, slot);
            return CODEX_REWARD_ERROR_VAULT_CHANGED;
        }
        if (!persist_standard()) {
            FN_ZERO_BOX_MON_AT(WINDOWS_BOX14_VAULT_BOX_INDEX, slot);
            return CODEX_REWARD_ERROR_SAVE_FAILED;
        }
        occupancy = vault_occupancy_mask();
        vault_publish(command, slot, input.record, occupancy, session_nonce);
    } else {
        return CODEX_REWARD_ERROR_UNKNOWN_COMMAND;
    }
    vault_commit_volatile(command, sequence, payload_hash);
    return CODEX_REWARD_ERROR_NONE;
}
#endif

static void publish_catalog_capability(void)
{
    volatile CodexBattleRuntimeMailboxV2 *mailbox =
        gCodexBattleRuntimeMailbox;
    u32 sequence = next_sequence(mailbox->snapshot_sequence);
    mailbox->capabilities |= WINDOWS_BATTLE_CATALOG_CAPABILITY;
#if CODEX_WINDOWS_BOX14_VAULT_ENABLED
    mailbox->capabilities |= WINDOWS_BOX14_VAULT_CAPABILITY;
#endif
    mailbox->snapshot.crc32 = snapshot_crc();
    barrier();
    mailbox->snapshot_sequence_inverse = ~sequence;
    barrier();
    mailbox->snapshot_sequence = sequence;
}
#endif

static void reward_poll(void)
{
    volatile CodexBattleRuntimeMailboxV2 *mailbox =
        gCodexBattleRuntimeMailbox;
    volatile CodexBattleRuntimeRequestV2 *request = &mailbox->request;
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    volatile CodexBattleRewardOwnerV1 *owner = gCodexBattleRewardOwner;
    u32 sequence_before = request->request_sequence;
    u32 inverse_before = request->request_sequence_inverse;
    u8 local[CWR_REQUEST_COPY_SIZE];
    u32 sequence_after;
    u32 request_crc;
    u32 payload_hash;
    u32 expected;
    u16 command;
    u16 phase;
    u16 turn;
    u16 size;
    u16 error;
    normalize_owner();
    if (!t27_state_valid() || sequence_before == 0u
        || inverse_before != ~sequence_before)
        return;
    copy_bytes(local, request, sizeof(local));
    barrier();
    sequence_after = request->request_sequence;
    if (sequence_after != sequence_before
        || request->request_sequence_inverse != inverse_before)
        return;
    command = read16(local + 10u);
#if CODEX_WINDOWS_CATALOG_ENABLED
    if ((command < CODEX_REWARD_COMMAND_STATUS
         || command > CODEX_REWARD_COMMAND_CLOSE)
        && !catalog_command(command)
#if CODEX_WINDOWS_BOX14_VAULT_ENABLED
        && !vault_command(command)
#endif
        )
#else
    if (command < CODEX_REWARD_COMMAND_STATUS
        || command > CODEX_REWARD_COMMAND_CLOSE)
#endif
        return;
    request_crc = read32(local + 84u);
    if (sequence_after == state->last_rejected_sequence
        && request_crc == state->last_rejected_request_crc32)
        return;
    phase = read16(local + 8u);
    turn = read16(local + 12u);
    size = read16(local + 14u);
    if (size > CODEX_RUNTIME_REQUEST_PAYLOAD_MAX) {
        reward_reject(sequence_after, command,
                      CODEX_REWARD_ERROR_OVERSIZE, request_crc);
        return;
    }
    payload_hash = crc32_bytes(local + 20u, size);
    if (payload_hash != read32(local + 16u)) {
        reward_reject(sequence_after, command,
                      CODEX_REWARD_ERROR_PAYLOAD_CRC, request_crc);
        return;
    }
    if (crc32_bytes(local, CWR_REQUEST_CRC_SIZE) != request_crc) {
        reward_reject(sequence_after, command,
                      CODEX_REWARD_ERROR_REQUEST_CRC, request_crc);
        return;
    }
#if CODEX_WINDOWS_CATALOG_ENABLED
    if (catalog_command(command)
#if CODEX_WINDOWS_BOX14_VAULT_ENABLED
        || vault_command(command)
#endif
        ) {
        if (owner->window != CODEX_REWARD_WINDOW_CLOSED
            || !private_field_context_valid(state)
            || phase != state->phase) {
            reward_reject(sequence_after, command,
                          CODEX_REWARD_ERROR_PRIVATE_BOUNDARY, request_crc);
            return;
        }
        /* Private field command sequence numbers belong to the current T27
         * session.  A cleanly committed owner from an older boot remains
         * durable evidence
         * for the host retry file, but must not turn sequence 1 of the new
         * session into a false replay.  Never reset an in-flight journal. */
        if (owner->pending_sequence == 0u
            && (owner->session_nonce != state->session_nonce
                || owner->match_id != state->match_id)) {
            owner->last_request_sequence = state->last_request_sequence;
            owner->last_payload_hash = 0u;
            owner->last_command = 0u;
        }
        owner->session_nonce = state->session_nonce;
        owner->match_id = state->match_id;
        owner_finalize();
    }
#endif
    if (read32(local) != state->session_nonce
        || read32(local) != owner->session_nonce) {
        reward_reject(sequence_after, command,
                      CODEX_REWARD_ERROR_WRONG_NONCE, request_crc);
        return;
    }
    if (read32(local + 4u) != owner->match_id
        || read32(local + 4u) != state->match_id) {
        reward_reject(sequence_after, command,
                      CODEX_REWARD_ERROR_WRONG_MATCH, request_crc);
        return;
    }
    /* A committed response is replay-safe even when close has already moved
     * the volatile T27 phase to IDLE. */
    if (sequence_after == owner->last_request_sequence) {
        if (owner->last_command == command
            && owner->last_payload_hash == payload_hash) {
            state->last_request_sequence = sequence_after;
            reward_accept(sequence_after, command);
        } else {
            reward_reject(sequence_after, command,
                          CODEX_REWARD_ERROR_WRONG_HASH, request_crc);
        }
        return;
    }
#if CODEX_WINDOWS_CATALOG_ENABLED
    if (catalog_command(command)
#if CODEX_WINDOWS_BOX14_VAULT_ENABLED
        || vault_command(command)
#endif
        ) {
#if CODEX_WINDOWS_BOX14_VAULT_ENABLED
        if (owner->pending_sequence != 0u
            && (vault_command(command)
                || (owner->flags & CWR_OWNER_FLAG_CATALOG) == 0u)) {
#else
        if (owner->pending_sequence != 0u
            && (owner->flags & CWR_OWNER_FLAG_CATALOG) == 0u) {
#endif
            reward_reject(sequence_after, command,
                          CODEX_REWARD_ERROR_BUSY, request_crc);
            return;
        }
    } else {
#endif
    if (owner->window != CODEX_REWARD_WINDOW_OPEN) {
        reward_reject(sequence_after, command,
                      CODEX_REWARD_ERROR_WINDOW_CLOSED, request_crc);
        return;
    }
    if (phase != state->phase || state->phase != CWR_T27_PHASE_RESULT) {
        reward_reject(sequence_after, command,
                      CODEX_REWARD_ERROR_WRONG_PHASE, request_crc);
        return;
    }
#if CODEX_WINDOWS_CATALOG_ENABLED
    if (owner->pending_sequence != 0u
        && (owner->flags & CWR_OWNER_FLAG_CATALOG) != 0u) {
        reward_reject(sequence_after, command,
                      CODEX_REWARD_ERROR_BUSY, request_crc);
        return;
    }
    }
#endif
    if (turn != state->turn) {
        reward_reject(sequence_after, command,
                      CODEX_REWARD_ERROR_WRONG_TURN, request_crc);
        return;
    }
    expected = owner->pending_sequence != 0u
        ? owner->pending_sequence : next_sequence(state->last_request_sequence);
    if (sequence_after != expected) {
        reward_reject(sequence_after, command,
            sequence_after < expected ? CODEX_REWARD_ERROR_STALE_SEQUENCE
                                      : CODEX_REWARD_ERROR_FUTURE_SEQUENCE,
            request_crc);
        return;
    }
#if CODEX_WINDOWS_BOX14_VAULT_ENABLED
    if (vault_command(command))
        error = vault_execute(command, sequence_after, payload_hash,
                              local + 20u, size, state->session_nonce);
    else
#endif
        error = start_or_resume_transaction(
            command, sequence_after, payload_hash, local + 20u, size);
    if (error != CODEX_REWARD_ERROR_NONE) {
        reward_reject(sequence_after, command, error, request_crc);
        return;
    }
    if (command == CODEX_REWARD_COMMAND_CLOSE)
        (void)FN_T27_FIELD_FINISH();
    reward_accept(sequence_after, command);
}

static void recover_open_owner(void)
{
    volatile CodexBattleRewardOwnerV1 *owner = gCodexBattleRewardOwner;
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    u32 nonce;
    normalize_owner();
    if (owner->window != CODEX_REWARD_WINDOW_OPEN)
        return;
    FN_T27_INITIALIZE();
    if (!t27_state_valid())
        return;
    nonce = state->session_nonce;
    if (nonce == 0u)
        nonce = *G_BASE_NONCE;
    if (nonce == 0u)
        nonce = 0x43425232u;
    owner->session_nonce = nonce;
    owner->flags |= CWR_OWNER_FLAG_RECOVERED;
    ++owner->reset_recovery_count;
    owner_finalize();
    state->session_nonce = nonce;
    state->match_id = owner->match_id;
    state->phase = CWR_T27_PHASE_RESULT;
    state->status = CWR_T27_STATUS_RESULT;
    state->active = 0u;
    state->field_completion_pending = 1u;
    state->last_request_sequence = owner->last_request_sequence;
    FN_T27_INITIALIZE();
    /* T27 initialization rebuilds the mailbox but its generic snapshot does
     * not copy the recovered sequence into last_accepted_sequence.  Publish
     * the reward-aware result snapshot so the host's next explicit command
     * starts after the durable owner rather than incorrectly restarting at 1. */
    publish_response(CWR_T27_STATUS_RESULT);
}

CWR_EXPORT(CodexBattleRewards_ReadKeysAdapter)
void CodexBattleRewards_ReadKeysAdapter(void)
{
    u16 command = gCodexBattleRuntimeMailbox->request.command;
    finish_durable_owner_restore();
#if CODEX_WINDOWS_CATALOG_ENABLED
    if ((command >= CODEX_REWARD_COMMAND_STATUS
         && command <= CODEX_REWARD_COMMAND_CLOSE)
        || catalog_command(command)
#if CODEX_WINDOWS_BOX14_VAULT_ENABLED
        || vault_command(command)
#endif
        ) {
#else
    if (command >= CODEX_REWARD_COMMAND_STATUS
        && command <= CODEX_REWARD_COMMAND_CLOSE) {
#endif
        FN_BASE_READ_KEYS();
        reward_poll();
    } else {
        FN_T27_READ_KEYS();
    }
#if CODEX_WINDOWS_CATALOG_ENABLED
    /* Both inherited delegates rebuild/publish the mailbox.  Advertise the
     * Stage46/47 capabilities after that write so the live host sees the
     * newest private field protocol rather than the Stage45 mask. */
    publish_catalog_capability();
#endif
}

CWR_EXPORT(CodexBattleRewards_SaveLoadAdapter)
u8 CodexBattleRewards_SaveLoadAdapter(u8 save_type)
{
    u8 result = FN_T27_SAVE_LOAD(save_type);
    if (*G_TRANSACTION_LOCK != CWR_TEST_MAGIC) {
        /* The inherited chain restores only the legacy 2 KiB ledger.  Reset
         * this independent owner to a valid pending sentinel here, but do not
         * read flash while the stock load callback still owns its workspace.
         * Stable field input completes the physical sector-31 tail restore. */
        if (result == 1u)
            owner_initialize_closed(0u);
        else
            normalize_owner();
    }
    return result;
}

static void arm_nonpunitive_codex_result(void)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    if (t27_state_valid() && state->active != 0u
        && state->player_selection_valid != 0u
        && state->controller_installed != 0u
        && (*G_BATTLE_FLAGS & CWR_BATTLE_TYPE_TRAINER) != 0u) {
        /* Set this only after the outcome dispatcher has run.  The stock
         * Tower result scripts return to trainerbattle without prize money
         * or whiteout warp; T27 AfterBattle then restores the exact party,
         * money, stats and original battle flags before opening rewards. */
        *G_BATTLE_FLAGS |= CWR_BATTLE_TYPE_TRAINER_TOWER;
        /* ReturnFromBattleToOverworld dispatches this callback after the
         * battle script ends.  The stock trainer callback whiteouts solely
         * from B_OUTCOME_LOST even for a late Tower flag, so route this one
         * Codex result back to the suspended reception script. */
        *G_MAIN_SAVED_CALLBACK =
            ((u32)(uintptr_t)CodexBattleRewards_ReturnToFieldAdapter) | 1u;
    }
}

CWR_EXPORT(CodexBattleRewards_ReturnToFieldAdapter)
void CodexBattleRewards_ReturnToFieldAdapter(void)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    if (t27_state_valid() && state->active != 0u
        && state->player_selection_valid != 0u
        && state->controller_installed != 0u) {
        FN_SET_MAIN_CALLBACK2(FN_RETURN_TO_FIELD);
        return;
    }
    FN_END_TRAINER_BATTLE();
}

CWR_EXPORT(CodexBattleRewards_BattleWonAdapter)
void CodexBattleRewards_BattleWonAdapter(void)
{
    arm_nonpunitive_codex_result();
    FN_BATTLE_WON();
}

CWR_EXPORT(CodexBattleRewards_BattleLostAdapter)
void CodexBattleRewards_BattleLostAdapter(void)
{
    arm_nonpunitive_codex_result();
    FN_BATTLE_LOST();
}

CWR_EXPORT(CodexBattleRewards_AfterBattleAdapter)
u16 CodexBattleRewards_AfterBattleAdapter(void)
{
    volatile CodexBattleRewardOwnerV1 *owner = gCodexBattleRewardOwner;
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    u16 result = FN_T27_AFTER_BATTLE();
    u32 previous_generation;
    u8 outcome;
    if (result != 1u || !t27_state_valid()
        || state->phase != CWR_T27_PHASE_RESULT)
        return result;
    normalize_owner();
    previous_generation = owner->generation;
    clear_bytes(owner, sizeof(*owner));
    owner->generation = previous_generation + 1u;
    owner->window = CODEX_REWARD_WINDOW_OPEN;
    owner->journal_phase = CODEX_REWARD_JOURNAL_NONE;
    owner->session_nonce = state->session_nonce;
    owner->match_id = state->match_id;
    owner->last_request_sequence = state->last_request_sequence;
    outcome = (u8)(*G_BATTLE_OUTCOME & 0x7Fu);
    owner->result_kind = outcome == 5u ? 4u
        : (u8)state->cleanup_reason;
    owner_finalize();
    if (!persist_sector(CWR_FAULT_OPEN)) {
        owner_initialize_closed(0u);
        *G_SPECIAL_RESULT = CODEX_REWARD_ERROR_SAVE_FAILED;
        return CODEX_REWARD_ERROR_SAVE_FAILED;
    }
    *G_SPECIAL_RESULT = 1u;
    return 1u;
}

CWR_EXPORT(CodexBattleRewards_FieldFinishAdapter)
u16 CodexBattleRewards_FieldFinishAdapter(void)
{
    normalize_owner();
    if (gCodexBattleRewardOwner->window == CODEX_REWARD_WINDOW_OPEN) {
        *G_SPECIAL_RESULT = 1u;
        return 1u;
    }
    return FN_T27_FIELD_FINISH();
}

CWR_EXPORT(CodexBattleRewards_Poll)
void CodexBattleRewards_Poll(void)
{
    finish_durable_owner_restore();
    reward_poll();
}

CWR_EXPORT(CodexBattleRewards_Probe)
u32 CodexBattleRewards_Probe(u32 selector)
{
    switch (selector) {
    case 0u: return CODEX_REWARD_OWNER_MAGIC;
    case 1u: return CODEX_REWARD_OWNER_ADDRESS;
    case 2u: return CODEX_REWARD_OWNER_SIZE;
    case 3u: return gCodexBattleRewardOwner->window;
    case 4u: return gCodexBattleRewardOwner->journal_phase;
    case 5u: return gCodexBattleRewardOwner->last_request_sequence;
    case 6u: return gCodexBattleRewardOwner->pending_sequence;
    case 7u: return owner_valid();
    case 8u: return gCodexBattleRewardOwner->committed_count;
    case 9u: return gCodexBattleRewardOwner->destination_token;
    default: return 0u;
    }
}

CWR_EXPORT(CodexBattleRewards_TestOpen)
u32 CodexBattleRewards_TestOpen(u32 nonce, u32 match_id,
                                u32 sequence, u32 result_kind)
{
    volatile CodexBattleRuntimeState *state = gCodexBattleRuntimeState;
    *G_BASE_NONCE = nonce == 0u ? 0x45000001u : nonce;
    FN_T27_INITIALIZE();
    if (!t27_state_valid())
        return 0u;
    state->session_nonce = *G_BASE_NONCE;
    state->match_id = match_id == 0u ? 0x45000002u : match_id;
    state->phase = CWR_T27_PHASE_RESULT;
    state->status = CWR_T27_STATUS_RESULT;
    state->active = 0u;
    state->field_completion_pending = 1u;
    state->last_request_sequence = sequence;
    FN_T27_INITIALIZE();
    owner_initialize_closed(0u);
    gCodexBattleRewardOwner->window = CODEX_REWARD_WINDOW_OPEN;
    gCodexBattleRewardOwner->journal_phase = CODEX_REWARD_JOURNAL_NONE;
    gCodexBattleRewardOwner->session_nonce = state->session_nonce;
    gCodexBattleRewardOwner->match_id = state->match_id;
    gCodexBattleRewardOwner->last_request_sequence = sequence;
    gCodexBattleRewardOwner->result_kind = (u8)result_kind;
    owner_finalize();
    return persist_sector(CWR_FAULT_OPEN) ? state->session_nonce : 0u;
}

CWR_EXPORT(CodexBattleRewards_TestSetFault)
u32 CodexBattleRewards_TestSetFault(u32 mask)
{
    *G_TEST_CONTROL = CWR_TEST_MAGIC;
    *G_TEST_FAULTS = mask;
    return mask;
}

CWR_EXPORT(CodexBattleRewards_TestRecover)
u32 CodexBattleRewards_TestRecover(void)
{
    recover_open_owner();
    return owner_valid();
}

CWR_EXPORT(CodexBattleRewards_TestClearFault)
u32 CodexBattleRewards_TestClearFault(void)
{
    *G_TEST_FAULTS = 0u;
    *G_TEST_CONTROL = 0u;
    *G_TRANSACTION_LOCK = 0u;
    return 1u;
}
