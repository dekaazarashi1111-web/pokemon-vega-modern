/* T28 Stage 45 exact-ROM reward/save/replay validation for libmGBA. */
#define CBR_RUNTIME_EMBEDDED
#include "mgba_codex_battle_runtime_smoke.c"

static uint32_t cwr_call(struct mCore *core, uint32_t function,
                         uint32_t r0, uint32_t r1,
                         uint32_t r2, uint32_t r3);
#define cbr_call cwr_call

enum {
    CWR_OWNER = 0x0203D800U,
    CWR_OWNER_SIZE = 128U,
    CWR_OWNER_MAGIC = 0x31525743U,
    CWR_OWNER_CRC = 12U,
    CWR_OWNER_WINDOW = 20U,
    CWR_OWNER_PHASE = 21U,
    CWR_OWNER_RESULT_KIND = 22U,
    CWR_OWNER_LAST_COMMAND = 23U,
    CWR_OWNER_SESSION = 24U,
    CWR_OWNER_MATCH = 28U,
    CWR_OWNER_LAST_SEQUENCE = 32U,
    CWR_OWNER_LAST_HASH = 36U,
    CWR_OWNER_PENDING_SEQUENCE = 40U,
    CWR_OWNER_PENDING_HASH = 44U,
    CWR_OWNER_TRANSACTION = 48U,
    CWR_OWNER_DESTINATION = 52U,
    CWR_OWNER_PERSONALITY = 56U,
    CWR_OWNER_OT = 60U,
    CWR_OWNER_ITEM = 64U,
    CWR_OWNER_QUANTITY = 66U,
    CWR_OWNER_BAG_BEFORE = 68U,
    CWR_OWNER_SPECIES = 70U,
    CWR_OWNER_HELD = 72U,
    CWR_OWNER_BALL = 74U,
    CWR_OWNER_MOVES = 76U,
    CWR_OWNER_LEVEL = 84U,
    CWR_OWNER_ABILITY = 85U,
    CWR_OWNER_NATURE = 86U,
    CWR_OWNER_PRESENCE = 87U,
    CWR_OWNER_IVS = 88U,
    CWR_OWNER_EVS = 94U,
    CWR_OWNER_SHINY = 100U,
    CWR_OWNER_TERA = 101U,
    CWR_OWNER_LAST_RESULT = 102U,
    CWR_OWNER_COMMITTED_COUNT = 104U,
    CWR_OWNER_ERROR_COUNT = 106U,
    CWR_OWNER_RECOVERY_COUNT = 108U,
    CWR_OWNER_FLAGS = 110U,
    CWR_OWNER_DESTINATION_KIND = 112U,
    CWR_OWNER_DESTINATION_BOX = 113U,
    CWR_OWNER_DESTINATION_SLOT = 114U,
    CWR_OWNER_FINGERPRINT = 116U,
    CWR_WINDOW_CLOSED = 0U,
    CWR_WINDOW_OPEN = 1U,
    CWR_PHASE_NONE = 0U,
    CWR_PHASE_PREPARED = 1U,
    CWR_PHASE_STAGED = 2U,
    CWR_PHASE_COMMITTED = 3U,
    CWR_COMMAND_STATUS = 11U,
    CWR_COMMAND_ITEM = 12U,
    CWR_COMMAND_MON = 13U,
    CWR_COMMAND_CLOSE = 14U,
    CWR_ERROR_FUTURE = 1U,
    CWR_ERROR_STALE = 2U,
    CWR_ERROR_NONCE = 3U,
    CWR_ERROR_PAYLOAD_CRC = 5U,
    CWR_ERROR_REQUEST_CRC = 6U,
    CWR_ERROR_PHASE = 7U,
    CWR_ERROR_MATCH = 11U,
    CWR_ERROR_TURN = 12U,
    CWR_ERROR_WINDOW_CLOSED = 18U,
    CWR_ERROR_SAVE_FAILED = 19U,
    CWR_ERROR_STORAGE_FULL = 20U,
    CWR_ERROR_INVALID_ITEM = 21U,
    CWR_ERROR_INVALID_MON = 22U,
    CWR_ERROR_WRONG_HASH = 23U,
    CWR_FAULT_PREPARE = 0x01U,
    CWR_FAULT_STAGED = 0x02U,
    CWR_FAULT_STANDARD = 0x04U,
    CWR_FAULT_COMMIT = 0x08U,
    CWR_FAULT_AFTER_PREPARE = 0x40U,
    CWR_READ_KEYS_POINTER = 0x080005ECU,
    CWR_BOX_LEVEL_SITE = 0x0803DF9CU,
    CWR_SUMMARY_ABILITY_SITE = 0x08136F04U,
    CWR_SUMMARY_MOVES_SITE = 0x08136F98U,
    CWR_SUMMARY_ABILITY_NAME_RENDER = 0x081382D0U,
    CWR_SUMMARY_ABILITY_DESC_RENDER = 0x08138434U,
    CWR_SAVE_LOAD_SITE = 0x080DB4E4U,
    CWR_AFTER_POINTER_SITE = 0x093CD57BU,
    CWR_FINISH_LAUNCH_SITE = 0x093CD588U,
    CWR_FINISH_ERROR_SITE = 0x093CD5AAU,
    CWR_BATTLE_WON_SITE = 0x0820CAECU,
    CWR_BATTLE_LOST_SITE = 0x0820CAF0U,
    CWR_BATTLE_DREW_SITE = 0x0820CAF4U,
    CWR_SPECIAL_RESULT = 0x02037004U,
    CWR_MAIN_CALLBACK2 = 0x03003134U,
    CWR_MAIN_SAVED_CALLBACK = 0x03003138U,
    CWR_END_TRAINER_BATTLE = 0x0807FBCDU,
    CWR_RETURN_TO_FIELD = 0x080561A1U,
    CWR_STATE_PLAYER_SELECTION_VALID = 27U,
    CWR_BATTLE_TYPE_TRAINER = 0x00000008U,
    CWR_BATTLE_TYPE_TRAINER_TOWER = 0x00080000U,
    CWR_ADD_BAG_ITEM = 0x08099A8DU,
    CWR_REMOVE_BAG_ITEM = 0x08099BE1U,
    CWR_CHECK_BAG_ITEM = 0x08099949U,
    CWR_CREATE_MON = 0x0803D1C1U,
    CWR_GET_MON_DATA = 0x0803F355U,
    CWR_GET_MON_ABILITY = 0x090DA23DU,
    CWR_SET_BOX_MON = 0x0808B651U,
    CWR_GET_BOX_MON_DATA = 0x0808B4B5U,
    CWR_ZERO_BOX_MON = 0x0808B751U,
    CWR_LOAD_GAME_DATA = 0x080DB4E5U,
    CWR_PLAYER_PARTY = 0x020241E4U,
    CWR_PLAYER_COUNT = 0x02023F89U,
    CWR_SPECIAL_BOX = 0x0203700AU,
    CWR_SPECIAL_POS = 0x0203700CU,
    CWR_BASE_NONCE = 0x0203F828U,
    CWR_SCRATCH = 0x0203E300U,
    CWR_STORAGE_POINTER = 0x03005050U,
    CWR_SUMMARY_POINTER = 0x0203B0B4U,
    CWR_FAKE_SUMMARY = 0x0203B0C4U,
    CWR_SUMMARY_MOVE_NAMES = 0x3110U,
    CWR_SUMMARY_ABILITY_NAME = 0x318CU,
    CWR_SUMMARY_ABILITY_DESC = 0x3195U,
    CWR_SUMMARY_IS_EGG = 0x31ACU,
    CWR_SUMMARY_IS_BAD_EGG = 0x31B0U,
    CWR_SUMMARY_MODE = 0x31B4U,
    CWR_SUMMARY_INPUT_STATE = 0x321CU,
    CWR_SUMMARY_CURRENT_MON = 0x323CU,
    CWR_ABILITY_DESCRIPTIONS = 0x0904CC28U,
    CWR_MON_SIZE = 100U,
    CWR_MON_DATA_SPECIES2 = 65U,
    CWR_BOX_COUNT = 14U,
    CWR_BOX_CAPACITY = 30U,
    CWR_TOKEN_PARTY = 0x10000000U,
    CWR_TOKEN_BOX = 0x20000000U,
};

#define CWR_SYMBOL_LIST(X) \
    X(buffer_summary_moves, "CodexBattleRewards_BufferSummaryMovesAdapter") \
    X(fill_summary_ability, "CodexBattleRewards_FillSummaryAbility") \
    X(box_level, "CodexBattleRewards_GetLevelFromBoxMonExpAdapter") \
    X(probe, "CodexBattleRewards_Probe") \
    X(poll, "CodexBattleRewards_Poll") \
    X(read_keys, "CodexBattleRewards_ReadKeysAdapter") \
    X(save_load, "CodexBattleRewards_SaveLoadAdapter") \
    X(summary_ability, "CodexBattleRewards_SummaryAbilityAdapter") \
    X(battle_won, "CodexBattleRewards_BattleWonAdapter") \
    X(battle_lost, "CodexBattleRewards_BattleLostAdapter") \
    X(return_to_field, "CodexBattleRewards_ReturnToFieldAdapter") \
    X(after_battle, "CodexBattleRewards_AfterBattleAdapter") \
    X(field_finish, "CodexBattleRewards_FieldFinishAdapter") \
    X(test_open, "CodexBattleRewards_TestOpen") \
    X(test_set_fault, "CodexBattleRewards_TestSetFault") \
    X(test_recover, "CodexBattleRewards_TestRecover") \
    X(test_clear_fault, "CodexBattleRewards_TestClearFault")

struct CwrSymbols {
#define CWR_SYMBOL_MEMBER(member, name) uint32_t member;
    CWR_SYMBOL_LIST(CWR_SYMBOL_MEMBER)
#undef CWR_SYMBOL_MEMBER
};

struct CwrCases {
    bool exact_tests;
    uint32_t payload;
    uint32_t owner;
    uint32_t owner_size;
};

static void cwr_die(const char *message)
{
    cbr_die(message);
}

static uint32_t cwr_call(struct mCore *core, uint32_t function,
                         uint32_t r0, uint32_t r1,
                         uint32_t r2, uint32_t r3)
{
    struct CpuState original = capture_cpu_state(core);
    uint64_t steps = 0U;
    write_register(core, "cpsr", (uint32_t)original.registers[16] | 0xA0U);
    write_register(core, "lr", 0x08000001U);
    write_register(core, "r0", r0);
    write_register(core, "r1", r1);
    write_register(core, "r2", r2);
    write_register(core, "r3", r3);
    write_register(core, "pc", function);
    while ((((uint32_t)read_register(core, "pc")) & ~1U) != 0x08000002U) {
        if (++steps > UINT64_C(60000000)) {
            fprintf(stderr, "cwr call limit function=%08" PRIx32
                    " pc=%08" PRIx32 "\n", function,
                    (uint32_t)read_register(core, "pc"));
            cwr_die("direct call exceeded instruction limit");
        }
        core->step(core);
    }
    r0 = (uint32_t)read_register(core, "r0");
    restore_cpu_state(core, &original);
    return r0;
}

static void cwr_write16(struct mCore *core, uint32_t address, uint16_t value)
{
    write8(core, address, (uint8_t)value);
    write8(core, address + 1U, (uint8_t)(value >> 8U));
}

static uint32_t cwr_read32_unaligned(struct mCore *core, uint32_t address)
{
    return (uint32_t)read8(core, address)
        | ((uint32_t)read8(core, address + 1U) << 8U)
        | ((uint32_t)read8(core, address + 2U) << 16U)
        | ((uint32_t)read8(core, address + 3U) << 24U);
}

static struct CwrSymbols cwr_load_symbols(const char *path)
{
    char *text = cbr_read_text(path);
    struct CwrSymbols result = {0};
#define CWR_LOAD_SYMBOL(member, name) result.member = cbr_json_symbol(text, name);
    CWR_SYMBOL_LIST(CWR_LOAD_SYMBOL)
#undef CWR_LOAD_SYMBOL
    free(text);
    return result;
}

static struct CwrCases cwr_load_cases(const char *path)
{
    static const char *const tests[] = {
        "exact_stage45_fixture",
        "rooted_stage44_identity_and_hooks",
        "owner_version_crc_and_migration",
        "normal_result_window_and_optional_close",
        "item_boundaries_bag_and_atomic_capacity",
        "mon_optional_fields_ball_party_and_box",
        "invalid_full_storage_and_generation_atomic",
        "duplicate_stale_future_wrong_identity_and_hash",
        "prepared_staged_committed_fault_reset_recovery",
        "multiple_rewards_close_and_replay",
        "stage42_to_44_runtime_noninterference",
        "codex_result_nonpunitive_dispatch",
        "warnings_zero",
    };
    char *text = cbr_read_text(path);
    bool exact = true;
    for (unsigned index = 0U; index < ARRAY_LEN(tests); ++index) {
        char quoted[128];
        snprintf(quoted, sizeof(quoted), "\"%s\"", tests[index]);
        exact = exact && cbr_occurrences(text, quoted) == 1U;
    }
    const char *runtime = cbr_find_key(text, "runtime");
    const char *payload = runtime ? cbr_find_key(runtime, "payload") : NULL;
    const char *owner = cbr_find_key(text, "owner");
    struct CwrCases result = {
        .exact_tests = exact,
        .payload = payload ? cbr_json_number(payload, "address") : 0U,
        .owner = owner ? cbr_json_number(owner, "address") : 0U,
        .owner_size = owner ? cbr_json_number(owner, "size") : 0U,
    };
    free(text);
    return result;
}

static uint32_t cwr_owner_crc(struct mCore *core)
{
    uint32_t crc = UINT32_C(0xFFFFFFFF);
    for (unsigned index = 0U; index < CWR_OWNER_SIZE; ++index) {
        uint8_t value = (index >= 12U && index < 16U)
            ? 0U : read8(core, CWR_OWNER + index);
        crc = cbr_crc_byte(crc, value);
    }
    return crc ^ UINT32_C(0xFFFFFFFF);
}

static bool cwr_owner_valid(struct mCore *core)
{
    return read32(core, CWR_OWNER) == CWR_OWNER_MAGIC
        && read32(core, CWR_OWNER + 4U) == ~(uint32_t)CWR_OWNER_MAGIC
        && read16(core, CWR_OWNER + 8U) == 1U
        && read16(core, CWR_OWNER + 10U) == CWR_OWNER_SIZE
        && read32(core, CWR_OWNER + CWR_OWNER_CRC) == cwr_owner_crc(core)
        && read8(core, CWR_OWNER + CWR_OWNER_WINDOW) <= CWR_WINDOW_OPEN
        && read8(core, CWR_OWNER + CWR_OWNER_PHASE) <= CWR_PHASE_COMMITTED;
}

static bool cwr_open(struct mCore *core, const struct CwrSymbols *symbols,
                     uint32_t nonce, uint32_t match, uint32_t sequence,
                     uint32_t result)
{
    uint32_t actual = cbr_call(core, symbols->test_open,
                               nonce, match, sequence, result);
    return actual == nonce && cwr_owner_valid(core)
        && read8(core, CWR_OWNER + CWR_OWNER_WINDOW) == CWR_WINDOW_OPEN
        && read8(core, CWR_OWNER + CWR_OWNER_PHASE) == CWR_PHASE_NONE
        && read32(core, CWR_OWNER + CWR_OWNER_SESSION) == nonce
        && read32(core, CWR_OWNER + CWR_OWNER_MATCH) == match
        && read32(core, CWR_OWNER + CWR_OWNER_LAST_SEQUENCE) == sequence
        && read8(core, CWR_OWNER + CWR_OWNER_RESULT_KIND) == result
        && read16(core, CBR_STATE + 16U) == CBR_PHASE_RESULT;
}

static void cwr_build_request(struct mCore *core, uint8_t request[96],
                              uint16_t command, const uint8_t *payload,
                              uint16_t size, uint32_t sequence)
{
    cbr_build_request(core, request, command, payload, size, sequence);
}

static bool cwr_process(struct mCore *core, const struct CwrSymbols *symbols,
                        const uint8_t request[96], bool accepted,
                        uint16_t expected_error)
{
    uint32_t sequence = (uint32_t)request[92]
        | ((uint32_t)request[93] << 8U)
        | ((uint32_t)request[94] << 16U)
        | ((uint32_t)request[95] << 24U);
    uint16_t command = (uint16_t)request[10]
        | ((uint16_t)request[11] << 8U);
    uint32_t previous = read32(core, CBR_STATE + CBR_STATE_LAST_SEQUENCE);
    cbr_write_request(core, request, false);
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    if (!cbr_snapshot_valid(core)
        || read32(core, CBR_MAILBOX + 72U) != sequence
        || read16(core, CBR_MAILBOX + 84U) != command)
        return false;
    if (accepted) {
        return read16(core, CBR_MAILBOX + 80U) == CBR_STATUS_ACCEPTED
            && read16(core, CBR_MAILBOX + 82U) == 0U
            && read32(core, CBR_STATE + CBR_STATE_LAST_SEQUENCE) == sequence;
    }
    return read16(core, CBR_MAILBOX + 80U) == CBR_STATUS_ERROR
        && read16(core, CBR_MAILBOX + 82U) == expected_error
        && read32(core, CBR_STATE + CBR_STATE_LAST_SEQUENCE) == previous;
}

static bool cwr_send(struct mCore *core, const struct CwrSymbols *symbols,
                     uint16_t command, const uint8_t *payload, uint16_t size,
                     uint32_t sequence, uint8_t request[96])
{
    cwr_build_request(core, request, command, payload, size, sequence);
    return cwr_process(core, symbols, request, true, 0U);
}

static bool cwr_send_error(struct mCore *core,
                           const struct CwrSymbols *symbols,
                           uint16_t command, const uint8_t *payload,
                           uint16_t size, uint32_t sequence,
                           uint16_t expected_error, uint8_t request[96])
{
    cwr_build_request(core, request, command, payload, size, sequence);
    return cwr_process(core, symbols, request, false, expected_error);
}

static unsigned cwr_bag_quantity(struct mCore *core, uint16_t item)
{
    unsigned low = 0U;
    unsigned high = 1000U;
    while (low + 1U < high) {
        unsigned middle = low + (high - low) / 2U;
        if (cbr_call(core, CWR_CHECK_BAG_ITEM, item, middle, 0U, 0U))
            low = middle;
        else
            high = middle;
    }
    return low;
}

static uint32_t cwr_call8(struct mCore *core, uint32_t function,
                          uint32_t r0, uint32_t r1, uint32_t r2, uint32_t r3,
                          uint32_t a4, uint32_t a5, uint32_t a6, uint32_t a7)
{
    struct CpuState original = capture_cpu_state(core);
    uint32_t original_sp = (uint32_t)original.registers[13];
    uint32_t call_sp = (original_sp - 16U) & ~7U;
    uint8_t saved[16];
    uint64_t steps = 0U;
    for (unsigned index = 0U; index < sizeof(saved); ++index)
        saved[index] = read8(core, call_sp + index);
    write32_bytes(core, call_sp, a4);
    write32_bytes(core, call_sp + 4U, a5);
    write32_bytes(core, call_sp + 8U, a6);
    write32_bytes(core, call_sp + 12U, a7);
    write_register(core, "sp", call_sp);
    write_register(core, "cpsr", (uint32_t)original.registers[16] | 0xA0U);
    write_register(core, "lr", 0x08000001U);
    write_register(core, "r0", r0);
    write_register(core, "r1", r1);
    write_register(core, "r2", r2);
    write_register(core, "r3", r3);
    write_register(core, "pc", function);
    while ((((uint32_t)read_register(core, "pc")) & ~1U) != 0x08000002U) {
        if (++steps > 5000000U)
            cwr_die("eight-argument call exceeded instruction limit");
        core->step(core);
    }
    r0 = (uint32_t)read_register(core, "r0");
    for (unsigned index = 0U; index < sizeof(saved); ++index)
        write8(core, call_sp + index, saved[index]);
    restore_cpu_state(core, &original);
    return r0;
}

static void cwr_clear(struct mCore *core, uint32_t address, uint32_t size)
{
    for (uint32_t index = 0U; index < size; ++index)
        write8(core, address + index, 0U);
}

static bool cwr_bytes_equal(struct mCore *core, uint32_t address,
                            const uint8_t *expected, size_t size)
{
    for (size_t index = 0U; index < size; ++index) {
        if (read8(core, address + (uint32_t)index) != expected[index])
            return false;
    }
    return true;
}

static bool cwr_ranges_equal(struct mCore *core, uint32_t left,
                             uint32_t right, size_t size)
{
    for (size_t index = 0U; index < size; ++index) {
        if (read8(core, left + (uint32_t)index)
            != read8(core, right + (uint32_t)index))
            return false;
    }
    return true;
}

static void cwr_create_mon(struct mCore *core, uint32_t address,
                           uint16_t species, uint8_t level,
                           uint32_t personality)
{
    cwr_clear(core, address, CWR_MON_SIZE);
    (void)cwr_call8(core, CWR_CREATE_MON, address, species, level, 31U,
                    1U, personality, 0U, 0U);
    if (cbr_call(core, CWR_GET_MON_DATA, address, 11U, 0U, 0U) != species)
        cwr_die("CreateMon setup failed");
}

static void cwr_clear_boxes(struct mCore *core)
{
    for (unsigned box = 0U; box < CWR_BOX_COUNT; ++box) {
        for (unsigned slot = 0U; slot < CWR_BOX_CAPACITY; ++slot)
            (void)cbr_call(core, CWR_ZERO_BOX_MON, box, slot, 0U, 0U);
    }
}

static void cwr_fill_boxes(struct mCore *core)
{
    cwr_create_mon(core, CWR_SCRATCH, 25U, 5U, 0x12345678U);
    for (unsigned box = 0U; box < CWR_BOX_COUNT; ++box) {
        for (unsigned slot = 0U; slot < CWR_BOX_CAPACITY; ++slot) {
            uint32_t species = cbr_call(core, CWR_GET_BOX_MON_DATA,
                                        box, slot, 11U, 0U);
            if (species == 0U)
                (void)cbr_call(core, CWR_SET_BOX_MON,
                               box, slot, CWR_SCRATCH, 0U);
        }
    }
}

static void cwr_install_party(struct mCore *core, unsigned count)
{
    uint8_t mon[CWR_MON_SIZE];
    cwr_create_mon(core, CWR_SCRATCH, 25U, 5U, 0x87654321U);
    for (unsigned index = 0U; index < sizeof(mon); ++index)
        mon[index] = read8(core, CWR_SCRATCH + index);
    cwr_clear(core, CWR_PLAYER_PARTY, 6U * CWR_MON_SIZE);
    for (unsigned slot = 0U; slot < count; ++slot) {
        for (unsigned index = 0U; index < sizeof(mon); ++index)
            write8(core, CWR_PLAYER_PARTY + slot * CWR_MON_SIZE + index,
                   mon[index]);
    }
    write8(core, CWR_PLAYER_COUNT, (uint8_t)count);
}

static void cwr_mon_payload(uint8_t raw[32], uint16_t species,
                            uint8_t level, uint16_t ball)
{
    memset(raw, 0, 32U);
    cbr_put16(raw, 0U, species);
    raw[2] = level;
    raw[3] = 1U;
    cbr_put16(raw, 4U, 0U);
    cbr_put16(raw, 6U, 33U);
    cbr_put16(raw, 8U, 45U);
    raw[14] = 13U;
    memset(raw + 15U, 31, 6U);
    raw[21] = 252U;
    raw[22] = 252U;
    raw[27] = 1U;
    raw[28] = 23U;
    raw[29] = 0xFFU;
    cbr_put16(raw, 30U, ball);
}

static void cwr_dragonite_payload(uint8_t raw[32])
{
    cwr_mon_payload(raw, 494U, 50U, 510U);
    raw[3] = 2U;
    cbr_put16(raw, 6U, 200U);
    cbr_put16(raw, 8U, 53U);
    cbr_put16(raw, 10U, 85U);
    cbr_put16(raw, 12U, 157U);
    raw[14] = 3U;
    memset(raw + 21U, 0, 6U);
    raw[23] = 252U;
    raw[25] = 252U;
    raw[26] = 4U;
    raw[28] = 16U;
}

static bool cwr_roots_test(struct mCore *core,
                           const struct CwrSymbols *symbols,
                           const struct CwrCases *cases)
{
    bool exact = cases->exact_tests && cases->owner == CWR_OWNER
        && cases->owner_size == CWR_OWNER_SIZE
        && cases->payload >= 0x08000000U
        && cbr_call(core, symbols->probe, 0U, 0U, 0U, 0U) == CWR_OWNER_MAGIC
        && cbr_call(core, symbols->probe, 1U, 0U, 0U, 0U) == CWR_OWNER
        && cbr_call(core, symbols->probe, 2U, 0U, 0U, 0U) == CWR_OWNER_SIZE
        && read32(core, CWR_READ_KEYS_POINTER) == symbols->read_keys
        && read16(core, CWR_SAVE_LOAD_SITE) == 0x4B00U
        && read16(core, CWR_SAVE_LOAD_SITE + 2U) == 0x4718U
        && read32(core, CWR_SAVE_LOAD_SITE + 4U) == symbols->save_load
        && read16(core, CWR_BOX_LEVEL_SITE) == 0x4B00U
        && read16(core, CWR_BOX_LEVEL_SITE + 2U) == 0x4718U
        && read32(core, CWR_BOX_LEVEL_SITE + 4U) == symbols->box_level
        && read16(core, CWR_SUMMARY_ABILITY_SITE) == 0x4B00U
        && read16(core, CWR_SUMMARY_ABILITY_SITE + 2U) == 0x4718U
        && (CWR_SUMMARY_ABILITY_SITE & 3U) == 0U
        && read32(core, (CWR_SUMMARY_ABILITY_SITE + 4U) & ~3U)
            == symbols->summary_ability
        && cwr_read32_unaligned(core, CWR_SUMMARY_ABILITY_SITE + 4U)
            == symbols->summary_ability
        && read32(core, CWR_SUMMARY_ABILITY_NAME_RENDER)
            == CWR_SUMMARY_ABILITY_NAME
        && read32(core, CWR_SUMMARY_ABILITY_DESC_RENDER)
            == CWR_SUMMARY_ABILITY_DESC
        && read16(core, CWR_SUMMARY_MOVES_SITE) == 0x4B00U
        && read16(core, CWR_SUMMARY_MOVES_SITE + 2U) == 0x4718U
        && read32(core, CWR_SUMMARY_MOVES_SITE + 4U)
            == symbols->buffer_summary_moves
        && read32(core, CWR_BATTLE_WON_SITE) == symbols->battle_won
        && read32(core, CWR_BATTLE_LOST_SITE) == symbols->battle_lost
        && read32(core, CWR_BATTLE_DREW_SITE) == symbols->battle_lost
        && cwr_read32_unaligned(core, CWR_AFTER_POINTER_SITE)
            == symbols->after_battle
        && cwr_read32_unaligned(core, CWR_FINISH_LAUNCH_SITE)
            == symbols->field_finish
        && cwr_read32_unaligned(core, CWR_FINISH_ERROR_SITE)
            == symbols->field_finish;
    if (!exact) {
        fprintf(stderr, "reward roots probe=%08" PRIx32 "/%08" PRIx32
                "/%08" PRIx32 " owner=%08" PRIx32 ":%" PRIu32
                " payload=%08" PRIx32 " level=%08" PRIx32
                " ability=%08" PRIx32 " moves=%08" PRIx32 "\n",
                cbr_call(core, symbols->probe, 0U, 0U, 0U, 0U),
                cbr_call(core, symbols->probe, 1U, 0U, 0U, 0U),
                cbr_call(core, symbols->probe, 2U, 0U, 0U, 0U),
                cases->owner, cases->owner_size, cases->payload,
                read32(core, CWR_BOX_LEVEL_SITE + 4U),
                cwr_read32_unaligned(core, CWR_SUMMARY_ABILITY_SITE + 4U),
                read32(core, CWR_SUMMARY_MOVES_SITE + 4U));
    }
    return exact;
}

static bool cwr_nonpunitive_result_test(
    struct mCore *core, const struct CwrSymbols *symbols,
    const struct CbrSymbols *t27)
{
    bool exact = true;
    cbr_test_initialize(core, t27, 0x45009101U);
    write8(core, CBR_STATE + CBR_STATE_ACTIVE, 1U);
    write8(core, CBR_STATE + CWR_STATE_PLAYER_SELECTION_VALID, 1U);
    write8(core, CBR_STATE + CBR_STATE_CONTROLLER_INSTALLED, 1U);
    write32_bytes(core, CBR_BATTLE_FLAGS, CWR_BATTLE_TYPE_TRAINER);
    cwr_write16(core, CWR_SPECIAL_RESULT, 0xFFFFU);
    (void)cbr_call(core, symbols->battle_won, 0U, 0U, 0U, 0U);
    exact = exact
        && (read32(core, CBR_BATTLE_FLAGS)
            & CWR_BATTLE_TYPE_TRAINER_TOWER) != 0U
        && read32(core, CWR_MAIN_SAVED_CALLBACK) == symbols->return_to_field
        && read16(core, CWR_SPECIAL_RESULT) == 0U;

    cbr_test_initialize(core, t27, 0x45009102U);
    write8(core, CBR_STATE + CBR_STATE_ACTIVE, 1U);
    write8(core, CBR_STATE + CWR_STATE_PLAYER_SELECTION_VALID, 1U);
    write8(core, CBR_STATE + CBR_STATE_CONTROLLER_INSTALLED, 1U);
    write32_bytes(core, CBR_BATTLE_FLAGS, CWR_BATTLE_TYPE_TRAINER);
    cwr_write16(core, CWR_SPECIAL_RESULT, 0xFFFFU);
    (void)cbr_call(core, symbols->battle_lost, 0U, 0U, 0U, 0U);
    exact = exact
        && (read32(core, CBR_BATTLE_FLAGS)
            & CWR_BATTLE_TYPE_TRAINER_TOWER) != 0U
        && read32(core, CWR_MAIN_SAVED_CALLBACK) == symbols->return_to_field
        && read16(core, CWR_SPECIAL_RESULT) == 1U;
    (void)cbr_call(core, symbols->return_to_field, 0U, 0U, 0U, 0U);
    exact = exact && read32(core, CWR_MAIN_CALLBACK2) == CWR_RETURN_TO_FIELD;

    cbr_test_initialize(core, t27, 0x45009103U);
    write8(core, CBR_STATE + CBR_STATE_ACTIVE, 0U);
    write8(core, CBR_STATE + CWR_STATE_PLAYER_SELECTION_VALID, 1U);
    write8(core, CBR_STATE + CBR_STATE_CONTROLLER_INSTALLED, 1U);
    write32_bytes(core, CBR_BATTLE_FLAGS, CWR_BATTLE_TYPE_TRAINER);
    write32_bytes(core, CWR_MAIN_SAVED_CALLBACK, CWR_END_TRAINER_BATTLE);
    cwr_write16(core, CWR_SPECIAL_RESULT, 0xFFFFU);
    (void)cbr_call(core, symbols->battle_lost, 0U, 0U, 0U, 0U);
    return exact
        && read32(core, CBR_BATTLE_FLAGS) == CWR_BATTLE_TYPE_TRAINER
        && read32(core, CWR_MAIN_SAVED_CALLBACK) == CWR_END_TRAINER_BATTLE
        && read16(core, CWR_SPECIAL_RESULT) == 1U;
}

static bool cwr_migration_test(struct mCore *core,
                               const struct CwrSymbols *symbols)
{
    bool exact = true;
    cwr_clear(core, CWR_OWNER, CWR_OWNER_SIZE);
    exact = exact && cbr_call(core, symbols->test_recover, 0U, 0U, 0U, 0U) == 1U
        && cwr_owner_valid(core)
        && read8(core, CWR_OWNER + CWR_OWNER_WINDOW) == CWR_WINDOW_CLOSED;
    for (unsigned index = 0U; index < CWR_OWNER_SIZE; ++index)
        write8(core, CWR_OWNER + index, 0xFFU);
    exact = exact && cbr_call(core, symbols->test_recover, 0U, 0U, 0U, 0U) == 1U
        && cwr_owner_valid(core)
        && read16(core, CWR_OWNER + CWR_OWNER_FLAGS) == 0U;
    cwr_clear(core, CWR_OWNER, CWR_OWNER_SIZE);
    write32_bytes(core, CWR_OWNER, CWR_OWNER_MAGIC);
    write32_bytes(core, CWR_OWNER + 4U, ~CWR_OWNER_MAGIC);
    cwr_write16(core, CWR_OWNER + 8U, 2U);
    cwr_write16(core, CWR_OWNER + 10U, CWR_OWNER_SIZE);
    exact = exact && cbr_call(core, symbols->test_recover, 0U, 0U, 0U, 0U) == 1U
        && cwr_owner_valid(core)
        && (read16(core, CWR_OWNER + CWR_OWNER_FLAGS) & 1U) != 0U;
    return exact;
}

static bool cwr_item_and_close_test(struct mCore *core,
                                    const struct CwrSymbols *symbols,
                                    bool *window, bool *item,
                                    bool *multiple)
{
    const uint16_t item_id = 100U;
    uint8_t payload[4];
    uint8_t first[96];
    uint8_t second[96];
    uint8_t close[96];
    uint8_t after_close[96];
    unsigned before;
    unsigned after;
    bool exact;
    cbr_put16(payload, 0U, item_id);
    cbr_put16(payload, 2U, 1U);
    if (!cwr_open(core, symbols, 0x45001001U, 0x45002001U, 20U, 1U))
        return false;
    before = cwr_bag_quantity(core, item_id);
    exact = cwr_send(core, symbols, CWR_COMMAND_ITEM,
                     payload, sizeof(payload), 21U, first);
    after = cwr_bag_quantity(core, item_id);
    *item = exact && after == before + 1U && cwr_owner_valid(core)
        && read8(core, CWR_OWNER + CWR_OWNER_PHASE) == CWR_PHASE_COMMITTED
        && read16(core, CWR_OWNER + CWR_OWNER_ITEM) == item_id
        && read16(core, CWR_OWNER + CWR_OWNER_QUANTITY) == 1U
        && read16(core, CWR_OWNER + CWR_OWNER_BAG_BEFORE) == before;
    exact = exact && cwr_process(core, symbols, first, true, 0U)
        && cwr_bag_quantity(core, item_id) == after;
    cbr_put16(payload, 2U, 2U);
    exact = exact && cwr_send(core, symbols, CWR_COMMAND_ITEM,
                              payload, sizeof(payload), 22U, second)
        && cwr_bag_quantity(core, item_id) == after + 2U
        && read16(core, CWR_OWNER + CWR_OWNER_COMMITTED_COUNT) == 2U;
    exact = exact && cwr_send(core, symbols, CWR_COMMAND_CLOSE,
                              NULL, 0U, 23U, close)
        && read8(core, CWR_OWNER + CWR_OWNER_WINDOW) == CWR_WINDOW_CLOSED
        && read16(core, CBR_STATE + 16U) == CBR_PHASE_IDLE;
    cbr_put16(payload, 2U, 1U);
    exact = exact && cwr_send_error(core, symbols, CWR_COMMAND_ITEM,
                                    payload, sizeof(payload), 24U,
                                    CWR_ERROR_WINDOW_CLOSED, after_close)
        && cwr_process(core, symbols, close, true, 0U)
        && cwr_bag_quantity(core, item_id) == after + 2U;
    *window = exact && read8(core, CWR_OWNER + CWR_OWNER_WINDOW)
        == CWR_WINDOW_CLOSED;
    *multiple = exact
        && read32(core, CWR_OWNER + CWR_OWNER_LAST_SEQUENCE) == 23U
        && read8(core, CWR_OWNER + CWR_OWNER_LAST_COMMAND) == CWR_COMMAND_CLOSE
        && read16(core, CWR_OWNER + CWR_OWNER_COMMITTED_COUNT) == 3U;
    (void)cbr_call(core, CWR_REMOVE_BAG_ITEM, item_id,
                   cwr_bag_quantity(core, item_id) - before, 0U, 0U);
    return exact;
}

static bool cwr_mon_test(struct mCore *core,
                         const struct CwrSymbols *symbols,
                         bool *capacity, bool *cache_rehydrate,
                         bool *restart_close)
{
    static const uint8_t multiscale[] = {
        0x6FU, 0x79U, 0x61U, 0x5DU, 0x59U, 0x52U, 0x79U, 0xFFU,
    };
    static const uint8_t move_names[][9] = {
        {0x3AU, 0x07U, 0x28U, 0x2EU, 0xFFU},
        {0x06U, 0x04U, 0x2EU, 0x1EU, 0x03U, 0x0CU, 0x34U, 0xFFU},
        {0xA2U, 0xA1U, 0x1FU, 0x2EU, 0x9AU, 0x79U, 0x64U, 0xFFU},
        {0x02U, 0x2CU, 0x15U, 0x41U, 0x2AU, 0xFFU},
    };
    uint8_t payload[32];
    uint8_t request[96];
    uint8_t invalid[96];
    uint8_t full[96];
    uint8_t close[96];
    bool exact;
    cwr_clear_boxes(core);
    cwr_install_party(core, 0U);
    if (!cwr_open(core, symbols, 0x45003001U, 0x45004001U, 30U, 2U))
        return false;
    cwr_dragonite_payload(payload);
    exact = cwr_send(core, symbols, CWR_COMMAND_MON,
                     payload, sizeof(payload), 31U, request)
        && read8(core, CWR_PLAYER_COUNT) == 1U
        && cbr_call(core, CWR_GET_MON_DATA,
                    CWR_PLAYER_PARTY, 11U, 0U, 0U) == 494U
        && cbr_call(core, CWR_GET_MON_DATA,
                    CWR_PLAYER_PARTY, CWR_MON_DATA_SPECIES2, 0U, 0U) == 494U
        && cbr_call(core, CWR_GET_MON_DATA,
                    CWR_PLAYER_PARTY, 38U, 0U, 0U) == 16U
        && cbr_call(core, CWR_GET_MON_DATA,
                    CWR_PLAYER_PARTY, 13U, 0U, 0U) == 200U
        && cbr_call(core, CWR_GET_MON_DATA,
                    CWR_PLAYER_PARTY, 14U, 0U, 0U) == 53U
        && cbr_call(core, CWR_GET_MON_DATA,
                    CWR_PLAYER_PARTY, 15U, 0U, 0U) == 85U
        && cbr_call(core, CWR_GET_MON_DATA,
                    CWR_PLAYER_PARTY, 16U, 0U, 0U) == 157U
        && cbr_call(core, CWR_GET_MON_ABILITY,
                    CWR_PLAYER_PARTY, 0U, 0U, 0U) == 137U
        && cbr_call(core, symbols->box_level,
                    CWR_PLAYER_PARTY, 0U, 0U, 0U) == 50U
        && read8(core, CWR_PLAYER_PARTY + 0x0FU) == 4U
        && read8(core, CWR_PLAYER_PARTY + 0x11U) == 16U
        && (read8(core, CWR_PLAYER_PARTY + 0x47U) & 0x10U) != 0U
        && cbr_call(core, CWR_GET_MON_DATA,
                    CWR_PLAYER_PARTY, 0U, 0U, 0U) % 25U == 3U
        && read8(core, CWR_OWNER + CWR_OWNER_DESTINATION_KIND) == 1U
        && (read32(core, CWR_OWNER + CWR_OWNER_DESTINATION)
            & 0xF0000000U) == CWR_TOKEN_PARTY
        && read16(core, CWR_OWNER + CWR_OWNER_BALL) == 510U;
    if (!exact) {
        fprintf(stderr, "reward dragonite count=%u species=%" PRIu32
                "/%" PRIu32 " ball=%" PRIu32 " ability=%" PRIu32
                " level=%" PRIu32 " pid=%" PRIu32 " mint=%u tera=%u"
                " hidden=%u destination=%u owner_ball=%u\n",
                read8(core, CWR_PLAYER_COUNT),
                cbr_call(core, CWR_GET_MON_DATA, CWR_PLAYER_PARTY,
                         11U, 0U, 0U),
                cbr_call(core, CWR_GET_MON_DATA, CWR_PLAYER_PARTY,
                         CWR_MON_DATA_SPECIES2, 0U, 0U),
                cbr_call(core, CWR_GET_MON_DATA, CWR_PLAYER_PARTY,
                         38U, 0U, 0U),
                cbr_call(core, CWR_GET_MON_ABILITY, CWR_PLAYER_PARTY,
                         0U, 0U, 0U),
                cbr_call(core, symbols->box_level, CWR_PLAYER_PARTY,
                         0U, 0U, 0U),
                cbr_call(core, CWR_GET_MON_DATA, CWR_PLAYER_PARTY,
                         0U, 0U, 0U),
                read8(core, CWR_PLAYER_PARTY + 0x0FU),
                read8(core, CWR_PLAYER_PARTY + 0x11U),
                (read8(core, CWR_PLAYER_PARTY + 0x47U) & 0x10U) != 0U,
                read8(core, CWR_OWNER + CWR_OWNER_DESTINATION_KIND),
                read16(core, CWR_OWNER + CWR_OWNER_BALL));
    }

    uint32_t previous_summary = read32(core, CWR_SUMMARY_POINTER);
    cwr_clear(core, CWR_FAKE_SUMMARY + CWR_SUMMARY_MOVE_NAMES,
              CWR_SUMMARY_CURRENT_MON - CWR_SUMMARY_MOVE_NAMES);
    for (unsigned index = 0U; index < CWR_MON_SIZE; ++index)
        write8(core, CWR_FAKE_SUMMARY + CWR_SUMMARY_CURRENT_MON + index,
               read8(core, CWR_PLAYER_PARTY + index));
    write8(core, CWR_FAKE_SUMMARY + CWR_SUMMARY_IS_EGG, 0x5AU);
    write8(core, CWR_FAKE_SUMMARY + CWR_SUMMARY_IS_BAD_EGG, 0xA5U);
    write8(core, CWR_FAKE_SUMMARY + CWR_SUMMARY_MODE, 0U);
    write8(core, CWR_FAKE_SUMMARY + CWR_SUMMARY_INPUT_STATE, 0x3CU);
    write32_bytes(core, CWR_SUMMARY_POINTER, CWR_FAKE_SUMMARY);
    (void)cbr_call(core, symbols->fill_summary_ability, 0U, 0U, 0U, 0U);
    bool summary_control_ok =
        read8(core, CWR_FAKE_SUMMARY + CWR_SUMMARY_IS_EGG) == 0x5AU
        && read8(core, CWR_FAKE_SUMMARY + CWR_SUMMARY_IS_BAD_EGG) == 0xA5U
        && read8(core, CWR_FAKE_SUMMARY + CWR_SUMMARY_MODE) == 0U
        && read8(core, CWR_FAKE_SUMMARY + CWR_SUMMARY_INPUT_STATE) == 0x3CU;
    (void)cbr_call(core, symbols->buffer_summary_moves, 0U, 0U, 0U, 0U);
    uint32_t multiscale_desc = read32(
        core, CWR_ABILITY_DESCRIPTIONS + 137U * 4U);
    bool summary_ok = summary_control_ok && cwr_bytes_equal(
            core, CWR_FAKE_SUMMARY + CWR_SUMMARY_ABILITY_NAME,
            multiscale, sizeof(multiscale))
        && cwr_ranges_equal(
            core, CWR_FAKE_SUMMARY + CWR_SUMMARY_ABILITY_DESC,
            multiscale_desc, 16U);
    for (unsigned index = 0U; index < 4U; ++index) {
        summary_ok = summary_ok && cwr_bytes_equal(
            core, CWR_FAKE_SUMMARY + CWR_SUMMARY_MOVE_NAMES + index * 9U,
            move_names[index],
            index == 0U ? 5U : index < 3U ? 8U : 6U);
    }
    write32_bytes(core, CWR_SUMMARY_POINTER, previous_summary);
    if (!summary_ok) {
        fprintf(stderr, "reward summary ability=");
        for (unsigned index = 0U; index < 8U; ++index)
            fprintf(stderr, "%02x", read8(core, CWR_FAKE_SUMMARY
                                           + CWR_SUMMARY_ABILITY_NAME + index));
        fprintf(stderr, " moves=");
        for (unsigned index = 0U; index < 36U; ++index)
            fprintf(stderr, "%02x", read8(core, CWR_FAKE_SUMMARY
                                           + CWR_SUMMARY_MOVE_NAMES + index));
        fprintf(stderr, "\n");
    }
    exact = exact && summary_ok;
    cwr_mon_payload(payload, 1U, 5U, 13U);
    bool invalid_ok = cwr_send_error(core, symbols, CWR_COMMAND_MON,
                                     payload, sizeof(payload), 32U,
                                     CWR_ERROR_INVALID_ITEM, invalid);
    exact = exact && invalid_ok && read8(core, CWR_PLAYER_COUNT) == 1U;
    cwr_install_party(core, 6U);
    cwr_clear_boxes(core);
    cwr_mon_payload(payload, 1620U, 100U, 510U);
    bool box_ok = cwr_send(core, symbols, CWR_COMMAND_MON,
                           payload, sizeof(payload), 32U, request);
    uint8_t destination_box = (uint8_t)read16(core, CWR_SPECIAL_BOX);
    uint8_t destination_pos = (uint8_t)read16(core, CWR_SPECIAL_POS);
    exact = exact && box_ok
        && read8(core, CWR_OWNER + CWR_OWNER_DESTINATION_KIND) == 2U
        && (read32(core, CWR_OWNER + CWR_OWNER_DESTINATION)
            & 0xF0000000U) == CWR_TOKEN_BOX
        && cbr_call(core, CWR_GET_BOX_MON_DATA,
                    destination_box, destination_pos, 11U, 0U) == 1620U
        && cbr_call(core, CWR_GET_BOX_MON_DATA,
                    destination_box, destination_pos,
                    CWR_MON_DATA_SPECIES2, 0U) == 1620U
        && cbr_call(core, CWR_GET_BOX_MON_DATA,
                    destination_box, destination_pos, 38U, 0U) == 16U;
    /* Prove that the same UI-visible storage row survives the normal save
     * boundary.  Clearing only RAM before Save_LoadGameData prevents an
     * immediate-memory check from satisfying this assertion. */
    (void)cbr_call(core, CWR_ZERO_BOX_MON,
                   destination_box, destination_pos, 0U, 0U);
    /* A real core reset runs ReadKeys before Continue.  That creates a valid
     * CLOSED owner in empty EWRAM; Save_LoadGameData must still replace it
     * from the Stage 45 tail stored in physical sector 31. */
    cwr_clear(core, CWR_OWNER, CWR_OWNER_SIZE);
    (void)cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    bool owner_closed_before_load = cwr_owner_valid(core)
        && read8(core, CWR_OWNER + CWR_OWNER_WINDOW) == CWR_WINDOW_CLOSED;
    uint32_t cleared_species = cbr_call(core, CWR_GET_BOX_MON_DATA,
                                        destination_box, destination_pos,
                                        CWR_MON_DATA_SPECIES2, 0U);
    uint32_t load_result = cbr_call(core, CWR_LOAD_GAME_DATA,
                                    0U, 0U, 0U, 0U);
    uint32_t save2 = read32(core, 0x0300504CU);
    if (save2 >= 0x02000000U && save2 + 17U < 0x02040000U)
        write8(core, save2 + 16U, 2U);
    write32_bytes(core, CWR_MAIN_CALLBACK2, 0x08055E75U);
    for (unsigned frame = 0U; frame < 257U; ++frame)
        (void)cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    uint32_t loaded_species = cbr_call(core, CWR_GET_BOX_MON_DATA,
                                       destination_box, destination_pos,
                                       CWR_MON_DATA_SPECIES2, 0U);
    uint32_t loaded_ball = cbr_call(core, CWR_GET_BOX_MON_DATA,
                                    destination_box, destination_pos,
                                    38U, 0U);
    uint32_t storage = read32(core, CWR_STORAGE_POINTER);
    uint32_t loaded_box_mon = storage + 4U
        + ((uint32_t)destination_box * CWR_BOX_CAPACITY
           + destination_pos) * 80U;
    uint32_t loaded_level = cbr_call(
        core, symbols->box_level, loaded_box_mon, 0U, 0U, 0U);
    bool owner_reloaded = owner_closed_before_load && cwr_owner_valid(core)
        && read8(core, CWR_OWNER + CWR_OWNER_WINDOW) == CWR_WINDOW_OPEN
        && read8(core, CWR_OWNER + CWR_OWNER_PHASE) == CWR_PHASE_COMMITTED
        && read16(core, CWR_OWNER + CWR_OWNER_COMMITTED_COUNT) == 2U
        && read16(core, CWR_OWNER + CWR_OWNER_RECOVERY_COUNT) >= 1U;
    bool box_reload = cleared_species == 0U && load_result == 1U
        && loaded_species == 1620U && loaded_ball == 16U
        && loaded_level == 100U && owner_reloaded;
    if (!box_reload)
        fprintf(stderr, "reward box reload clear=%" PRIu32
                " load=%" PRIu32 " species=%" PRIu32 " ball=%" PRIu32
                " level=%" PRIu32 " owner=%u/%u/%u recovery=%u"
                " box=%u pos=%u\n", cleared_species, load_result,
                loaded_species, loaded_ball, loaded_level,
                read8(core, CWR_OWNER + CWR_OWNER_WINDOW),
                read8(core, CWR_OWNER + CWR_OWNER_PHASE),
                read16(core, CWR_OWNER + CWR_OWNER_COMMITTED_COUNT),
                read16(core, CWR_OWNER + CWR_OWNER_RECOVERY_COUNT),
                destination_box, destination_pos);
    exact = exact && box_reload;
    /* The stock PC Storage teardown can clear this legacy EWRAM work range.
     * Fault-inject that exact cache loss after a durable COMMITTED reward and
     * require normal stable-field polling to rehydrate it from sector 31. */
    cwr_clear(core, CWR_OWNER, CWR_OWNER_SIZE);
    for (unsigned frame = 0U; frame < 257U; ++frame)
        (void)cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    *cache_rehydrate = cwr_owner_valid(core)
        && read8(core, CWR_OWNER + CWR_OWNER_WINDOW) == CWR_WINDOW_OPEN
        && read8(core, CWR_OWNER + CWR_OWNER_PHASE) == CWR_PHASE_COMMITTED
        && read16(core, CWR_OWNER + CWR_OWNER_COMMITTED_COUNT) == 2U
        && read16(core, CWR_OWNER + CWR_OWNER_RECOVERY_COUNT) >= 1U
        && read32(core, CBR_MAILBOX + 88U) == 32U;
    if (!*cache_rehydrate)
        fprintf(stderr, "reward field cache rehydrate owner=%u/%u/%u "
                "recovery=%u valid=%u\n",
                read8(core, CWR_OWNER + CWR_OWNER_WINDOW),
                read8(core, CWR_OWNER + CWR_OWNER_PHASE),
                read16(core, CWR_OWNER + CWR_OWNER_COMMITTED_COUNT),
                read16(core, CWR_OWNER + CWR_OWNER_RECOVERY_COUNT),
                cwr_owner_valid(core));
    cwr_fill_boxes(core);
    cwr_mon_payload(payload, 25U, 50U, 4U);
    *capacity = cwr_send_error(core, symbols, CWR_COMMAND_MON,
                               payload, sizeof(payload), 33U,
                               CWR_ERROR_STORAGE_FULL, full)
        && read32(core, CWR_OWNER + CWR_OWNER_LAST_SEQUENCE) == 32U
        && read16(core, CWR_OWNER + CWR_OWNER_COMMITTED_COUNT) == 2U;
    if (!*capacity)
        fprintf(stderr, "reward capacity phase=%u sequence=%" PRIu32
                " committed=%u box0=%" PRIu32 " box24=%" PRIu32 "\n",
                read8(core, CWR_OWNER + CWR_OWNER_PHASE),
                read32(core, CWR_OWNER + CWR_OWNER_LAST_SEQUENCE),
                read16(core, CWR_OWNER + CWR_OWNER_COMMITTED_COUNT),
                cbr_call(core, CWR_GET_BOX_MON_DATA, 0U, 0U, 11U, 0U),
                cbr_call(core, CWR_GET_BOX_MON_DATA, 24U, 29U, 11U, 0U));
    *restart_close = *cache_rehydrate
        && cwr_send(core, symbols, CWR_COMMAND_CLOSE,
                    NULL, 0U, 33U, close)
        && read8(core, CWR_OWNER + CWR_OWNER_WINDOW) == CWR_WINDOW_CLOSED
        && read32(core, CWR_OWNER + CWR_OWNER_LAST_SEQUENCE) == 33U
        && read32(core, CBR_MAILBOX + 88U) == 33U;
    if (!*restart_close)
        fprintf(stderr, "reward restart close window=%u owner_sequence=%" PRIu32
                " snapshot_sequence=%" PRIu32 "\n",
                read8(core, CWR_OWNER + CWR_OWNER_WINDOW),
                read32(core, CWR_OWNER + CWR_OWNER_LAST_SEQUENCE),
                read32(core, CBR_MAILBOX + 88U));
    return exact && *capacity;
}

static bool cwr_identity_test(struct mCore *core,
                              const struct CwrSymbols *symbols,
                              unsigned iterations)
{
    uint8_t payload[4];
    uint8_t request[96];
    uint8_t accepted[96];
    bool exact;
    cbr_put16(payload, 0U, 101U);
    cbr_put16(payload, 2U, 1U);
    if (!cwr_open(core, symbols, 0x45005001U, 0x45006001U, 40U, 4U))
        return false;
    exact = cwr_send_error(core, symbols, CWR_COMMAND_ITEM,
                           payload, sizeof(payload), 42U,
                           CWR_ERROR_FUTURE, request)
        && cwr_send_error(core, symbols, CWR_COMMAND_ITEM,
                          payload, sizeof(payload), 39U,
                          CWR_ERROR_STALE, request);
    cwr_build_request(core, request, CWR_COMMAND_ITEM,
                      payload, sizeof(payload), 41U);
    request[0] ^= 1U;
    cbr_put32(request, 84U, cbr_crc_bytes(request, 84U));
    exact = exact && cwr_process(core, symbols, request, false, CWR_ERROR_NONCE);
    cwr_build_request(core, request, CWR_COMMAND_ITEM,
                      payload, sizeof(payload), 41U);
    request[4] ^= 1U;
    cbr_put32(request, 84U, cbr_crc_bytes(request, 84U));
    exact = exact && cwr_process(core, symbols, request, false, CWR_ERROR_MATCH);
    cwr_build_request(core, request, CWR_COMMAND_ITEM,
                      payload, sizeof(payload), 41U);
    request[8] = CBR_PHASE_IDLE;
    cbr_put32(request, 84U, cbr_crc_bytes(request, 84U));
    exact = exact && cwr_process(core, symbols, request, false, CWR_ERROR_PHASE);
    cwr_build_request(core, request, CWR_COMMAND_ITEM,
                      payload, sizeof(payload), 41U);
    request[12] ^= 1U;
    cbr_put32(request, 84U, cbr_crc_bytes(request, 84U));
    exact = exact && cwr_process(core, symbols, request, false, CWR_ERROR_TURN);
    cwr_build_request(core, request, CWR_COMMAND_ITEM,
                      payload, sizeof(payload), 41U);
    request[20] ^= 1U;
    exact = exact && cwr_process(core, symbols, request, false,
                                 CWR_ERROR_PAYLOAD_CRC);
    cwr_build_request(core, request, CWR_COMMAND_ITEM,
                      payload, sizeof(payload), 41U);
    request[84] ^= 1U;
    exact = exact && cwr_process(core, symbols, request, false,
                                 CWR_ERROR_REQUEST_CRC);
    exact = exact && cwr_send(core, symbols, CWR_COMMAND_ITEM,
                              payload, sizeof(payload), 41U, accepted);
    cbr_put16(payload, 2U, 2U);
    exact = exact && cwr_send_error(core, symbols, CWR_COMMAND_ITEM,
                                    payload, sizeof(payload), 41U,
                                    CWR_ERROR_WRONG_HASH, request);
    for (unsigned index = 0U; index < iterations; ++index) {
        uint8_t mon[32];
        uint16_t species = (uint16_t)((index & 1U) ? 0U : 1621U);
        cwr_mon_payload(mon, species, 50U, 4U);
        exact = exact && cwr_send_error(
            core, symbols, CWR_COMMAND_MON, mon, sizeof(mon), 42U,
            CWR_ERROR_INVALID_MON, request);
        /* Change payload so the deterministic rejected-request cache cannot
         * turn the next boundary case into a vacuous no-op. */
        cbr_put16(payload, 2U, (uint16_t)(2U + (index & 1U)));
    }
    return exact;
}

static void cwr_simulate_reset(struct mCore *core,
                               const struct CwrSymbols *symbols,
                               uint32_t nonce)
{
    cwr_clear(core, CBR_STATE, 1536U);
    cwr_clear(core, CBR_MAILBOX, 256U);
    write32_bytes(core, CWR_BASE_NONCE, nonce);
    if (cbr_call(core, symbols->test_recover, 0U, 0U, 0U, 0U) != 1U
        || !cwr_owner_valid(core)
        || read32(core, CWR_OWNER + CWR_OWNER_SESSION) != nonce
        || read16(core, CBR_STATE + 16U) != CBR_PHASE_RESULT)
        cwr_die("reward reset recovery setup failed");
}

static bool cwr_fault_test(struct mCore *core,
                           const struct CwrSymbols *symbols)
{
    const uint16_t item_id = 102U;
    const uint32_t faults[] = {
        CWR_FAULT_PREPARE, CWR_FAULT_STAGED,
        CWR_FAULT_STANDARD, CWR_FAULT_COMMIT,
    };
    uint8_t payload[4];
    uint8_t request[96];
    bool exact = true;
    cbr_put16(payload, 0U, item_id);
    cbr_put16(payload, 2U, 1U);
    for (unsigned index = 0U; index < ARRAY_LEN(faults); ++index) {
        uint32_t nonce = 0x45007010U + index;
        unsigned before;
        if (!cwr_open(core, symbols, nonce, 0x45008010U + index, 50U, 1U))
            return false;
        before = cwr_bag_quantity(core, item_id);
        (void)cbr_call(core, symbols->test_set_fault,
                       faults[index], 0U, 0U, 0U);
        exact = exact && cwr_send_error(
            core, symbols, CWR_COMMAND_ITEM, payload, sizeof(payload), 51U,
            CWR_ERROR_SAVE_FAILED, request);
        if (faults[index] == CWR_FAULT_PREPARE
            || faults[index] == CWR_FAULT_STAGED) {
            exact = exact && cwr_bag_quantity(core, item_id) == before;
        } else {
            exact = exact && cwr_bag_quantity(core, item_id) == before + 1U
                && read8(core, CWR_OWNER + CWR_OWNER_PHASE) == CWR_PHASE_STAGED;
        }
        (void)cbr_call(core, symbols->test_clear_fault, 0U, 0U, 0U, 0U);
        exact = exact && cwr_process(core, symbols, request, true, 0U)
            && cwr_bag_quantity(core, item_id) == before + 1U
            && read8(core, CWR_OWNER + CWR_OWNER_PHASE) == CWR_PHASE_COMMITTED;
        (void)cbr_call(core, CWR_REMOVE_BAG_ITEM, item_id, 1U, 0U, 0U);
    }
    if (!cwr_open(core, symbols, 0x45007100U, 0x45008100U, 60U, 2U))
        return false;
    unsigned before = cwr_bag_quantity(core, item_id);
    (void)cbr_call(core, symbols->test_set_fault,
                   CWR_FAULT_AFTER_PREPARE, 0U, 0U, 0U);
    exact = exact && cwr_send_error(
        core, symbols, CWR_COMMAND_ITEM, payload, sizeof(payload), 61U,
        CWR_ERROR_SAVE_FAILED, request)
        && read8(core, CWR_OWNER + CWR_OWNER_PHASE) == CWR_PHASE_PREPARED
        && read32(core, CWR_OWNER + CWR_OWNER_PENDING_SEQUENCE) == 61U
        && cwr_bag_quantity(core, item_id) == before;
    (void)cbr_call(core, symbols->test_clear_fault, 0U, 0U, 0U, 0U);
    cwr_simulate_reset(core, symbols, 0x45007101U);
    cwr_build_request(core, request, CWR_COMMAND_ITEM,
                      payload, sizeof(payload), 61U);
    exact = exact && cwr_process(core, symbols, request, true, 0U)
        && cwr_bag_quantity(core, item_id) == before + 1U
        && read16(core, CWR_OWNER + CWR_OWNER_RECOVERY_COUNT) >= 1U;
    (void)cbr_call(core, CWR_REMOVE_BAG_ITEM, item_id, 1U, 0U, 0U);

    if (!cwr_open(core, symbols, 0x45007200U, 0x45008200U, 70U, 3U))
        return false;
    before = cwr_bag_quantity(core, item_id);
    (void)cbr_call(core, symbols->test_set_fault,
                   CWR_FAULT_STANDARD, 0U, 0U, 0U);
    exact = exact && cwr_send_error(
        core, symbols, CWR_COMMAND_ITEM, payload, sizeof(payload), 71U,
        CWR_ERROR_SAVE_FAILED, request)
        && read8(core, CWR_OWNER + CWR_OWNER_PHASE) == CWR_PHASE_STAGED
        && cwr_bag_quantity(core, item_id) == before + 1U;
    (void)cbr_call(core, symbols->test_clear_fault, 0U, 0U, 0U, 0U);
    cwr_simulate_reset(core, symbols, 0x45007201U);
    cwr_build_request(core, request, CWR_COMMAND_ITEM,
                      payload, sizeof(payload), 71U);
    exact = exact && cwr_process(core, symbols, request, true, 0U)
        && cwr_bag_quantity(core, item_id) == before + 1U;
    exact = exact && cwr_process(core, symbols, request, true, 0U)
        && cwr_bag_quantity(core, item_id) == before + 1U;
    (void)cbr_call(core, CWR_REMOVE_BAG_ITEM, item_id, 1U, 0U, 0U);
    return exact;
}

static bool cwr_noninterference_test(struct mCore *core,
                                     const struct CwrSymbols *symbols,
                                     const struct CbrSymbols *t27)
{
    cbr_test_initialize(core, t27, 0x45009001U);
    bool exact = cbr_header_test(core, t27)
        && cbr_configure(core, t27, 0U)
        && read32(core, CBR_OPPONENT_CHOOSE_ACTION_POINTER) == t27->controller
        && read32(core, CBR_OPPONENT_CHOOSE_MOVE_POINTER) == t27->controller
        && read32(core, CBR_OPPONENT_CHOOSE_POKEMON_POINTER) == t27->controller;
    uint32_t state_hash = cbr_call(core, t27->state_hash, 0U, 0U, 0U, 0U);
    cbr_call(core, symbols->poll, 0U, 0U, 0U, 0U);
    return exact
        && cbr_call(core, t27->state_hash, 0U, 0U, 0U, 0U) == state_hash;
}

#ifndef CWR_RUNTIME_EMBEDDED
int main(int argc, char **argv)
{
    if (argc != 5)
        return 2;
    bool full = !strcmp(argv[4], "full");
    if (!full && strcmp(argv[4], "quick"))
        return 2;
    struct CwrSymbols symbols = cwr_load_symbols(argv[2]);
    struct CwrCases cases = cwr_load_cases(argv[3]);
    struct CbrSymbols t27 = cbr_load_symbols(argv[2]);
    struct mLogger logger = {.log = quiet_log, .filter = NULL};
    mLogSetDefaultLogger(&logger);
    struct mRTCSource rtc = {
        .sample = NULL, .unixTime = fixed_unix_time,
        .serialize = NULL, .deserialize = NULL,
    };
    struct mCore *core = mCoreFind(argv[1]);
    if (!core || !core->init(core))
        cwr_die("mGBA core initialization failed");
    if (!mCoreLoadFile(core, argv[1]))
        cwr_die("ROM load failed");
    mCoreInitConfig(core, NULL);
    mCoreConfigSetDefaultValue(&core->config, "idleOptimization", "ignore");
    mCoreSetRTC(core, &rtc);
    core->reset(core);
    run_trace_prefix(core);
    run_fixed_frames(core);
    struct Snapshot base = take_snapshot(core);

    bool tests[15] = {false};
    bool window = false;
    bool item = false;
    bool multiple = false;
    bool capacity = false;
    bool cache_rehydrate = false;
    bool restart_close = false;
    tests[0] = cases.exact_tests;
    tests[1] = cwr_roots_test(core, &symbols, &cases);
    restore_snapshot(core, &base);
    tests[2] = cwr_migration_test(core, &symbols);
    restore_snapshot(core, &base);
    (void)cwr_item_and_close_test(
        core, &symbols, &window, &item, &multiple);
    tests[3] = window;
    tests[4] = item;
    tests[9] = multiple;
    restore_snapshot(core, &base);
    tests[5] = cwr_mon_test(
        core, &symbols, &capacity, &cache_rehydrate, &restart_close);
    tests[6] = capacity;
    restore_snapshot(core, &base);
    tests[7] = cwr_identity_test(core, &symbols, full ? 64U : 8U);
    restore_snapshot(core, &base);
    tests[8] = cwr_fault_test(core, &symbols);
    restore_snapshot(core, &base);
    tests[10] = cwr_noninterference_test(core, &symbols, &t27);
    restore_snapshot(core, &base);
    tests[11] = cwr_nonpunitive_result_test(core, &symbols, &t27);
    tests[12] = cache_rehydrate;
    tests[13] = restart_close;
    tests[14] = log_problem_count == 0U;
    bool passed = true;
    for (unsigned index = 0U; index < ARRAY_LEN(tests); ++index)
        passed = passed && tests[index];

    static const char *const names[] = {
        "exact_stage45_fixture",
        "rooted_stage44_identity_and_hooks",
        "owner_version_crc_and_migration",
        "normal_result_window_and_optional_close",
        "item_boundaries_bag_and_atomic_capacity",
        "mon_optional_fields_ball_party_and_box",
        "invalid_full_storage_and_generation_atomic",
        "duplicate_stale_future_wrong_identity_and_hash",
        "prepared_staged_committed_fault_reset_recovery",
        "multiple_rewards_close_and_replay",
        "stage42_to_44_runtime_noninterference",
        "codex_result_nonpunitive_dispatch",
        "field_owner_cache_invalidation_rehydrate",
        "restart_reward_close_sequence_sync",
        "warnings_zero",
    };
    char rom_sha[65], runner_source_sha[65], runner_binary_sha[65];
    char symbols_sha[65], cases_sha[65];
    sha256_file(argv[1], rom_sha);
    sha256_file(__FILE__, runner_source_sha);
    sha256_file(argv[0], runner_binary_sha);
    sha256_file(argv[2], symbols_sha);
    sha256_file(argv[3], cases_sha);
    fprintf(stderr, "mgba-codex-battle-rewards %s: ", full ? "full" : "quick");
    for (unsigned index = 0U; index < ARRAY_LEN(tests); ++index)
        fprintf(stderr, "%s=%u%s", names[index], tests[index],
                index + 1U == ARRAY_LEN(tests) ? "\n" : " ");
    printf("{\"schema_version\":1,\"task\":\"T28\",\"stage\":45,"
           "\"mode\":\"%s\",\"status\":\"%s\","
           "\"rom_sha256\":\"%s\","
           "\"runner_source_sha256\":\"%s\","
           "\"runner_binary_sha256\":\"%s\","
           "\"symbols_sha256\":\"%s\",\"cases_sha256\":\"%s\","
           "\"tests\":{",
           full ? "full" : "quick", passed ? "PASS" : "FAIL",
           rom_sha, runner_source_sha, runner_binary_sha, symbols_sha, cases_sha);
    for (unsigned index = 0U; index < ARRAY_LEN(tests); ++index)
        printf("\"%s\":%s%s", names[index], tests[index] ? "true" : "false",
               index + 1U == ARRAY_LEN(tests) ? "" : ",");
    printf("},\"total\":%zu,\"warnings\":%u,"
           "\"transaction_iterations\":%u,"
           "\"result_identity\":\"CB45:reward:v1:128:exactly-once\"}\n",
           ARRAY_LEN(tests), log_problem_count, full ? 64U : 8U);

    free(base.bytes);
    mCoreConfigDeinit(&core->config);
    core->deinit(core);
    return passed ? 0 : 1;
}
#endif
